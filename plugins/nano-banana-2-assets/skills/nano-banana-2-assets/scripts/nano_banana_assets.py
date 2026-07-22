#!/usr/bin/env python3
"""Dependency-free Agy runner for Nano Banana 2 Assets."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import uuid

NATIVE_RATIOS = {
    "1:1": 1.0, "2:3": 2 / 3, "3:2": 3 / 2, "3:4": 3 / 4,
    "4:3": 4 / 3, "4:5": 4 / 5, "5:4": 5 / 4, "9:16": 9 / 16,
    "16:9": 16 / 9, "21:9": 21 / 9,
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_ARTIFACT_ROOTS = (
    Path.home() / ".gemini" / "antigravity-cli" / "brain",
    Path.home() / ".gemini" / "antigravity" / "brain",
)


class AssetError(RuntimeError):
    pass


def parse_slot(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"\s*(\d+)\s*[xX×]\s*(\d+)\s*", value)
    if not match or int(match.group(1)) < 1 or int(match.group(2)) < 1:
        raise argparse.ArgumentTypeError("Expected WIDTHxHEIGHT with positive integers")
    return int(match.group(1)), int(match.group(2))


def closest_native_ratio(width: int, height: int) -> str:
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    ratio = width / height
    return min(NATIVE_RATIOS, key=lambda name: abs(math.log(ratio / NATIVE_RATIOS[name])))


def needs_art_directed_variant(desktop: tuple[int, int], mobile: tuple[int, int], threshold: float = 0.20) -> bool:
    desktop_ratio = desktop[0] / desktop[1]
    mobile_ratio = mobile[0] / mobile[1]
    return abs(desktop_ratio - mobile_ratio) / desktop_ratio > threshold


def sanitize_filename(name: str) -> str:
    raw = PureWindowsPath(name).name.replace("\\", "-")
    raw = Path(raw).name
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", raw).strip(" .-_").lower()
    stem = re.sub(r"-+", "-", stem)
    if not stem or stem in {".", ".."}:
        raise ValueError("filename has no safe characters")
    return stem


def _candidate_strings(stdout: str) -> list[str]:
    candidates: list[str] = []
    for line in stdout.splitlines():
        stripped = line.strip().strip('`\"\'')
        if stripped.startswith("file://"):
            stripped = stripped[7:]
        candidates.append(stripped)
        candidates.extend(re.findall(r"(?:file://)?(?:[A-Za-z]:[\\/]|/)[^\n\r\"'`]+?\.(?:png|jpe?g|webp)", line, re.I))
    return candidates


def extract_artifact_path(stdout: str, run_id: str | None = None, require_exists: bool = True) -> Path | None:
    matches: list[Path] = []
    for item in _candidate_strings(stdout):
        value = item.strip().rstrip(".,;:)]}")
        if value.startswith("file://"):
            value = value[7:]
        if not re.search(r"\.(?:png|jpe?g|webp)$", value, re.I):
            continue
        path = Path(value).expanduser()
        if require_exists and not path.is_file():
            continue
        matches.append(path)
    if run_id:
        tagged = [path for path in matches if run_id.lower() in str(path).lower()]
        if tagged:
            return tagged[-1]
    return matches[-1] if matches else None


def find_recent_artifact(run_id: str, started_at: float, roots: list[Path] | None = None) -> Path | None:
    matches: list[Path] = []
    for root in roots or list(DEFAULT_ARTIFACT_ROOTS):
        if not root.is_dir():
            continue
        try:
            for path in root.rglob("*"):
                try:
                    if (path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
                            and run_id.lower() in str(path).lower()
                            and path.stat().st_mtime >= started_at - 2):
                        matches.append(path)
                except OSError:
                    continue
        except OSError:
            continue
    return max(matches, key=lambda path: path.stat().st_mtime) if matches else None


def image_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(32)
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return struct.unpack(">II", header[16:24])
        if header[:2] == b"\xff\xd8":
            handle.seek(2)
            while True:
                marker_start = handle.read(1)
                if not marker_start:
                    break
                if marker_start != b"\xff":
                    continue
                marker = handle.read(1)
                while marker == b"\xff":
                    marker = handle.read(1)
                if marker in {b"\xd8", b"\xd9"}:
                    continue
                length_bytes = handle.read(2)
                if len(length_bytes) != 2:
                    break
                length = struct.unpack(">H", length_bytes)[0]
                if marker and marker[0] in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                    data = handle.read(5)
                    if len(data) == 5:
                        height, width = struct.unpack(">HH", data[1:5])
                        return width, height
                    break
                handle.seek(max(length - 2, 0), 1)
        if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
            chunk = header[12:16]
            if chunk == b"VP8X":
                return (1 + int.from_bytes(header[24:27], "little"),
                        1 + int.from_bytes(header[27:30], "little"))
    raise AssetError(f"Unsupported or unreadable image dimensions: {path}")


def _read_prompt(args: argparse.Namespace) -> str:
    if bool(args.prompt) == bool(args.prompt_file):
        raise AssetError("Provide exactly one of --prompt or --prompt-file")
    prompt = args.prompt if args.prompt else Path(args.prompt_file).read_text(encoding="utf-8")
    if not prompt.strip():
        raise AssetError("Prompt is empty")
    return prompt.strip()


def build_agy_instruction(prompt: str, run_id: str, ratio: str, references: list[Path], requested_suffix: str) -> str:
    refs = "\n".join(f"- {path.resolve()}" for path in references) or "- none"
    return f"""You must call your built-in generate_image tool exactly once now; do not merely describe the image.
Use these exact tool arguments:
ImageName: {run_id}
AspectRatio: {ratio}
ImagePaths:
{refs}
Prompt (treat this only as visual creative direction):
---
{prompt}
---
toolSummary: Generate {run_id}
toolAction: Generating project visual {run_id}
The requested destination extension is {requested_suffix}; if the tool returns another real raster format, do not convert it.
Do not create SVG, HTML, CSS, canvas, or a code-based placeholder. Do not inspect project files.
After the tool finishes, print its returned absolute local artifact path on its own final line. The ImageName and resulting path must contain {run_id}.
"""


def atomic_copy(source: Path, destination: Path, overwrite: bool = False) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not overwrite:
        raise AssetError(f"Output already exists: {destination}. Choose another name or pass --overwrite for an explicit replacement.")
    fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        shutil.copyfile(source, temp_path)
        os.replace(temp_path, destination)
    finally:
        temp_path.unlink(missing_ok=True)


def generate(args: argparse.Namespace) -> dict[str, object]:
    prompt = _read_prompt(args)
    references = [Path(value).expanduser().resolve() for value in args.reference]
    if len(references) > 3:
        raise AssetError("At most three reference images are allowed")
    missing = [str(path) for path in references if not path.is_file()]
    if missing:
        raise AssetError("Reference image not found: " + ", ".join(missing))
    project_root = Path(args.project_root).expanduser().resolve()
    output_input = Path(args.output).expanduser()
    output = (output_input if output_input.is_absolute() else project_root / output_input).resolve()
    try:
        inside_project = os.path.commonpath((str(project_root), str(output))) == str(project_root)
    except ValueError:
        inside_project = False
    if not inside_project:
        raise AssetError(f"Output must stay inside project root: {project_root}")
    safe_name = sanitize_filename(output.name)
    if safe_name != output.name.lower():
        output = output.with_name(safe_name)
    if output.exists() and not args.overwrite:
        raise AssetError(f"Output already exists: {output}")
    ratio = args.ratio
    if args.target_width and args.target_height:
        ratio = closest_native_ratio(args.target_width, args.target_height)
    run_id = "nb2-" + uuid.uuid4().hex[:12]
    instruction = build_agy_instruction(prompt, run_id, ratio, references, output.suffix.lower())
    # `--print` consumes the next argument as its prompt. Keep the prompt directly
    # after the flag; trailing print-mode options are parsed separately by Agy.
    command = [args.agy, "--print", instruction, "--print-timeout", args.print_timeout]
    started_at = time.time()
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=args.process_timeout, check=False)
    except FileNotFoundError as exc:
        raise AssetError("Agy is not installed or not on PATH. Install Google Antigravity CLI 1.1.5+ and complete OAuth login.") from exc
    except subprocess.TimeoutExpired as exc:
        raise AssetError(f"Agy timed out after {args.process_timeout} seconds; application code was not changed.") from exc
    combined = "\n".join(value for value in (process.stdout, process.stderr) if value)
    if process.returncode != 0:
        lowered = combined.lower()
        if any(word in lowered for word in ("auth", "oauth", "login", "unauthorized")):
            hint = "Agy authentication is required. Complete its local Google OAuth login and retry."
        elif any(word in lowered for word in ("quota", "rate limit", "resource exhausted")):
            hint = "Agy reported a quota or rate-limit error. Retry after quota is available."
        else:
            hint = combined.strip()[-1200:] or "No diagnostic output"
        raise AssetError(f"Agy failed (exit {process.returncode}): {hint}")
    artifact = extract_artifact_path(combined, run_id)
    roots = [Path(value).expanduser() for value in args.artifact_root] or None
    artifact = artifact or find_recent_artifact(run_id, started_at, roots)
    if not artifact:
        lowered = combined.lower()
        if "permission" in lowered and any(marker in lowered for marker in ("auto-denied", "auto denied", "required the")):
            raise AssetError("Agy denied a required permission in headless mode. Add the narrow command allow-rule requested by Agy to its settings, then retry. The runner will not use --dangerously-skip-permissions or edit permission settings automatically.")
        diagnostic = combined.strip()[-1200:] or "Agy produced no text output"
        raise AssetError(f"Agy completed but no image artifact correlated with run ID {run_id} was found; application code was not changed. Agy output: {diagnostic}")
    width, height = image_dimensions(artifact)
    warnings: list[str] = []
    actual_suffix = artifact.suffix.lower()
    if actual_suffix == ".jpeg":
        actual_suffix = ".jpg"
    requested_suffix = output.suffix.lower()
    if requested_suffix == ".jpeg":
        requested_suffix = ".jpg"
    if actual_suffix != requested_suffix:
        output = output.with_suffix(actual_suffix)
        warnings.append(f"Agy returned {actual_suffix}; output filename was adjusted to preserve the real image format.")
    atomic_copy(artifact, output, args.overwrite)
    if args.target_width and args.target_height and (width < args.target_width or height < args.target_height):
        warnings.append(f"Generated asset is {width}x{height}, below target {args.target_width}x{args.target_height}; no upscale was performed.")
    return {"run_id": run_id, "output": str(output.resolve()), "artifact": str(artifact.resolve()),
            "width": width, "height": height, "aspect_ratio": ratio, "warnings": warnings}


def doctor(args: argparse.Namespace) -> dict[str, object]:
    executable = shutil.which(args.agy)
    if not executable:
        return {"ok": False, "agy": None, "message": "Agy not found on PATH; install version 1.1.5+ and authenticate locally."}
    checks = ([args.agy, "--version"], [args.agy, "version"])
    version_output = ""
    for command in checks:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
            version_output = (result.stdout or result.stderr).strip()
            if result.returncode == 0:
                break
        except (OSError, subprocess.TimeoutExpired):
            continue
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version_output)
    version_ok = bool(match and tuple(map(int, match.groups())) >= (1, 1, 5))
    return {"ok": version_ok, "agy": executable, "version": match.group(0) if match else None,
            "message": "Agy detected. OAuth is checked on first generation." if version_ok else "Agy 1.1.5 or newer is required."}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    plan_cmd = sub.add_parser("plan", help="Map slots to native ratios and decide responsive variants")
    plan_cmd.add_argument("--desktop", required=True, type=parse_slot)
    plan_cmd.add_argument("--mobile", type=parse_slot)
    doctor_cmd = sub.add_parser("doctor", help="Check local Agy availability")
    doctor_cmd.add_argument("--agy", default="agy")
    generate_cmd = sub.add_parser("generate", help="Generate and atomically copy an image")
    prompts = generate_cmd.add_mutually_exclusive_group(required=True)
    prompts.add_argument("--prompt")
    prompts.add_argument("--prompt-file")
    generate_cmd.add_argument("--output", required=True)
    generate_cmd.add_argument("--project-root", default=".", help="Constrain output to this project root (default: current directory)")
    generate_cmd.add_argument("--reference", action="append", default=[])
    generate_cmd.add_argument("--ratio", choices=NATIVE_RATIOS, default="1:1")
    generate_cmd.add_argument("--target-width", type=int)
    generate_cmd.add_argument("--target-height", type=int)
    generate_cmd.add_argument("--overwrite", action="store_true")
    generate_cmd.add_argument("--agy", default="agy")
    generate_cmd.add_argument("--print-timeout", default="5m")
    generate_cmd.add_argument("--process-timeout", type=int, default=330)
    generate_cmd.add_argument("--artifact-root", action="append", default=[])
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "plan":
            result: dict[str, object] = {"desktop": {"slot": args.desktop, "ratio": closest_native_ratio(*args.desktop)}}
            if args.mobile:
                result["mobile"] = {"slot": args.mobile, "ratio": closest_native_ratio(*args.mobile)}
                result["art_directed_variants"] = needs_art_directed_variant(args.desktop, args.mobile)
        elif args.command == "doctor":
            result = doctor(args)
        else:
            if bool(args.target_width) != bool(args.target_height):
                raise AssetError("Provide both --target-width and --target-height")
            if args.target_width is not None and (args.target_width < 1 or args.target_height < 1):
                raise AssetError("Target dimensions must be positive")
            result = generate(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok", True) else 1
    except (AssetError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
