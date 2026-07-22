#!/usr/bin/env python3
"""Opt-in live Agy smoke test. This consumes image-generation quota."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "skill-source/nano-banana-2-assets/scripts/nano_banana_assets.py"
SPEC = importlib.util.spec_from_file_location("nano_banana_assets", RUNNER)
module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(module)

PROMPTS = {
    "web": "Editorial construction management landing-page hero, site supervisor and crew reviewing plans at sunrise, subjects on the right, calm dark negative space on the left for HTML copy, realistic PPE, commercial photography, 35 mm lens, amber and navy palette, no text, logos, watermarks, signs, UI, or unsafe behavior.",
    "mobile": "Premium mobile finance onboarding illustration, a confident small-business owner reviewing a clear abstract growth scene, centered upper focal point with calm space in the lower third for native onboarding copy and controls, tactile paper-cut geometry, navy mint and warm cream palette, no text, letters, numbers, logos, watermarks, or UI.",
}


def args_for(kind: str, output: Path) -> argparse.Namespace:
    size = (1600, 900) if kind == "web" else (900, 1200)
    return argparse.Namespace(prompt=PROMPTS[kind], prompt_file=None, output=str(output), reference=[], ratio="1:1",
                              target_width=size[0], target_height=size[1], overwrite=False, agy="agy",
                              print_timeout="5m", process_timeout=330, artifact_root=[], project_root=str(ROOT))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-quota-use", action="store_true", help="Required safety switch")
    parser.add_argument("--output-dir", default="live-test-output")
    args = parser.parse_args(argv)
    if not args.confirm_quota_use:
        parser.error("Live generation is opt-in; pass --confirm-quota-use")
    output_dir = Path(args.output_dir)
    results = []
    for kind in ("web", "mobile"):
        results.append(module.generate(args_for(kind, output_dir / f"{kind}-asset.jpg")))
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except module.AssetError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
