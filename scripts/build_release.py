#!/usr/bin/env python3
"""Sync the canonical skill into both plugins and build deterministic ZIP files."""

from __future__ import annotations

import argparse
import filecmp
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "nano-banana-2-assets"
SOURCE = ROOT / "skill-source" / SKILL_NAME
COMMAND_SOURCE = ROOT / "command-source"
PACKAGES = {
    "openai": ROOT / "packages" / "openai" / SKILL_NAME,
    "claude": ROOT / "packages" / "claude" / SKILL_NAME,
}
REPO_CODEX_PLUGIN = ROOT / "plugins" / SKILL_NAME


def files(root: Path) -> list[Path]:
    return sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc")


def same_tree(left: Path, right: Path) -> bool:
    left_files, right_files = files(left), files(right)
    return left_files == right_files and all(filecmp.cmp(left / rel, right / rel, shallow=False) for rel in left_files)


def sync_skill(plugin_root: Path, check: bool) -> None:
    destination = plugin_root / "skills" / SKILL_NAME
    if check:
        if not destination.is_dir() or not same_tree(SOURCE, destination):
            raise RuntimeError(f"Package is out of sync: {destination}")
        return
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if not same_tree(SOURCE, destination):
        raise RuntimeError(f"Package copy differs from canonical skill: {destination}")


def sync_commands(plugin_root: Path, check: bool) -> None:
    destination = plugin_root / "commands"
    if check:
        if not destination.is_dir() or not same_tree(COMMAND_SOURCE, destination):
            raise RuntimeError(f"Package commands are out of sync: {destination}")
        return
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(COMMAND_SOURCE, destination)
    if not same_tree(COMMAND_SOURCE, destination):
        raise RuntimeError(f"Package command copy differs from canonical source: {destination}")


def sync_repo_codex_plugin(check: bool) -> None:
    source = PACKAGES["openai"]
    if check:
        if not REPO_CODEX_PLUGIN.is_dir() or not same_tree(source, REPO_CODEX_PLUGIN):
            raise RuntimeError(f"Repo marketplace plugin is out of sync: {REPO_CODEX_PLUGIN}")
        return
    if REPO_CODEX_PLUGIN.exists():
        shutil.rmtree(REPO_CODEX_PLUGIN)
    REPO_CODEX_PLUGIN.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, REPO_CODEX_PLUGIN, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if not same_tree(source, REPO_CODEX_PLUGIN):
        raise RuntimeError("Repo marketplace plugin differs from the OpenAI release package")


def update_version(plugin_root: Path, version: str) -> None:
    manifest_name = ".codex-plugin/plugin.json" if (plugin_root / ".codex-plugin").exists() else ".claude-plugin/plugin.json"
    manifest = plugin_root / manifest_name
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["version"] = version
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_marketplace_version(version: str) -> None:
    manifest = ROOT / ".claude-plugin" / "marketplace.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    matches = [plugin for plugin in data.get("plugins", []) if plugin.get("name") == SKILL_NAME]
    if len(matches) != 1:
        raise RuntimeError("Claude marketplace must contain exactly one nano-banana-2-assets entry")
    matches[0]["version"] = version
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_zip(platform: str, plugin_root: Path, version: str, output_dir: Path) -> Path:
    output = output_dir / f"{SKILL_NAME}-{platform}-{version}.zip"
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in files(plugin_root):
            info = zipfile.ZipInfo(rel.as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (plugin_root / rel).read_bytes())
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="0.1.2")
    parser.add_argument("--check", action="store_true", help="Only verify package copies match the canonical skill")
    args = parser.parse_args(argv)
    for root in PACKAGES.values():
        sync_skill(root, args.check)
        sync_commands(root, args.check)
    if args.check:
        sync_repo_codex_plugin(check=True)
        print("Canonical skill and package copies match.")
        return 0
    outputs = []
    update_marketplace_version(args.version)
    for platform, root in PACKAGES.items():
        update_version(root, args.version)
        outputs.append(build_zip(platform, root, args.version, ROOT / "dist"))
    sync_repo_codex_plugin(check=False)
    for output in outputs:
        print(output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"release build failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
