from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "skill-source/nano-banana-2-assets/scripts/nano_banana_assets.py"
SPEC = importlib.util.spec_from_file_location("nano_banana_assets", RUNNER_PATH)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(runner)


def minimal_png(width: int, height: int) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + width.to_bytes(4, "big") + height.to_bytes(4, "big") + b"\x08\x02\x00\x00\x00"


class PlanningTests(unittest.TestCase):
    def test_ratio_mapping(self):
        self.assertEqual(runner.closest_native_ratio(1600, 900), "16:9")
        self.assertEqual(runner.closest_native_ratio(1080, 1920), "9:16")
        self.assertEqual(runner.closest_native_ratio(1000, 1000), "1:1")

    def test_responsive_threshold_is_strictly_greater_than_twenty_percent(self):
        self.assertFalse(runner.needs_art_directed_variant((100, 100), (120, 100)))
        self.assertTrue(runner.needs_art_directed_variant((1600, 900), (390, 520)))

    def test_sanitize_posix_and_windows_paths(self):
        self.assertEqual(runner.sanitize_filename("../../Hero Final.JPG"), "hero-final.jpg")
        self.assertEqual(runner.sanitize_filename(r"C:\\temp\\Hero Final.JPG"), "hero-final.jpg")

    def test_stdout_path_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "nb2-run-hero.png"
            image.write_bytes(minimal_png(20, 10))
            found = runner.extract_artifact_path(f"Artifact: file://{image}\n", "nb2-run")
            self.assertEqual(found, image)

    def test_windows_path_is_parsed_without_requiring_local_existence(self):
        found = runner.extract_artifact_path(r"C:\\Users\\me\\nb2-win\\asset.jpg", "nb2-win", require_exists=False)
        self.assertIsNotNone(found)
        self.assertIn("nb2-win", str(found))

    def test_fallback_search_uses_run_id_and_recency(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "conversation" / "nb2-abc-image.png"
            image.parent.mkdir()
            image.write_bytes(minimal_png(20, 10))
            found = runner.find_recent_artifact("nb2-abc", time.time() - 1, [root])
            self.assertEqual(found, image)


class FakeAgyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def fake_agy(self, mode: str) -> Path:
        path = self.root / f"agy-{mode}"
        code = f'''#!/usr/bin/env python3
import pathlib, re, sys, time
if "--version" in sys.argv or (len(sys.argv) > 1 and sys.argv[1] == "version"):
    print("agy 1.1.5")
    raise SystemExit(0)
if "--print" not in sys.argv:
    print("missing --print", file=sys.stderr); raise SystemExit(9)
prompt_index = sys.argv.index("--print") + 1
instruction = sys.argv[prompt_index]
if instruction == "--print-timeout":
    print("prompt must immediately follow --print", file=sys.stderr); raise SystemExit(9)
if "--print-timeout" not in sys.argv[prompt_index + 1:]:
    print("missing trailing --print-timeout", file=sys.stderr); raise SystemExit(9)
run_id = re.search(r"nb2-[a-f0-9]+", instruction).group(0)
mode = {mode!r}
if mode == "timeout":
    time.sleep(3)
if mode == "auth":
    print("OAuth login required", file=sys.stderr); raise SystemExit(1)
if mode == "quota":
    print("quota resource exhausted", file=sys.stderr); raise SystemExit(1)
if mode == "quota-zero":
    print("Waiting for rate limit reset...")
    print("429 RESOURCE_EXHAUSTED: gemini-3.1-flash-image quota exhausted, resets in ~3 hours")
    print("Had it succeeded: /tmp/" + run_id + ".png")
    raise SystemExit(0)
if mode == "quota-recovered":
    print("Waiting for rate limit reset...")
    print("Previous 429 RESOURCE_EXHAUSTED; retry succeeded")
if mode == "missing":
    print("completed without an artifact"); raise SystemExit(0)
if mode == "permission":
    print('a tool required the "command" permission and was auto-denied'); raise SystemExit(0)
output = pathlib.Path({str(self.root)!r}) / (run_id + ".png")
output.write_bytes(b"\\x89PNG\\r\\n\\x1a\\n" + b"\\x00\\x00\\x00\\rIHDR" + (800).to_bytes(4,"big") + (600).to_bytes(4,"big") + b"\\x08\\x02\\x00\\x00\\x00")
print(output)
'''
        path.write_text(code, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path

    def args(self, agy: Path, output: Path, **overrides):
        values = dict(prompt="a detailed image", prompt_file=None, reference=[], output=str(output), ratio="4:3",
                      target_width=None, target_height=None, overwrite=False, agy=str(agy), print_timeout="5m",
                      process_timeout=2, artifact_root=[], project_root=str(self.root))
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_success_and_measured_dimensions(self):
        result = runner.generate(self.args(self.fake_agy("success"), self.root / "final.png"))
        self.assertEqual((result["width"], result["height"]), (800, 600))
        self.assertTrue((self.root / "final.png").is_file())

    def test_output_extension_tracks_real_artifact_format(self):
        result = runner.generate(self.args(self.fake_agy("success"), self.root / "final.jpg"))
        self.assertTrue((self.root / "final.png").is_file())
        self.assertFalse((self.root / "final.jpg").exists())
        self.assertTrue(result["warnings"])

    def test_missing_artifact_does_not_create_output(self):
        output = self.root / "missing.png"
        with self.assertRaisesRegex(runner.AssetError, "no image artifact"):
            runner.generate(self.args(self.fake_agy("missing"), output))
        self.assertFalse(output.exists())

    def test_timeout(self):
        with self.assertRaisesRegex(runner.AssetError, "timed out"):
            runner.generate(self.args(self.fake_agy("timeout"), self.root / "timeout.png", process_timeout=1))

    def test_auth_and_quota_errors_are_actionable(self):
        with self.assertRaisesRegex(runner.AssetError, "authentication"):
            runner.generate(self.args(self.fake_agy("auth"), self.root / "auth.png"))
        with self.assertRaisesRegex(runner.AssetError, "quota"):
            runner.generate(self.args(self.fake_agy("quota"), self.root / "quota.png"))

    def test_zero_exit_rate_limit_is_structured_and_does_not_create_output(self):
        output = self.root / "quota-zero.png"
        with self.assertRaises(runner.RateLimitError) as caught:
            runner.generate(self.args(self.fake_agy("quota-zero"), output))
        error = caught.exception
        self.assertEqual(error.retry_after_seconds, 10800)
        self.assertEqual(error.reset_hint, "~3 hours")
        self.assertEqual(error.model, "gemini-3.1-flash-image")
        self.assertEqual(error.payload()["error_type"], "rate_limit")
        self.assertFalse(output.exists())

    def test_cli_rate_limit_json_and_temporary_failure_exit_code(self):
        output = self.root / "quota-cli.png"
        process = subprocess.run(
            [sys.executable, str(RUNNER_PATH), "generate", "--prompt", "test image",
             "--output", str(output), "--project-root", str(self.root),
             "--agy", str(self.fake_agy("quota-zero"))],
            capture_output=True,
            text=True,
            check=False,
        )
        payload = json.loads(process.stderr)
        self.assertEqual(process.returncode, 75)
        self.assertEqual(payload["error_type"], "rate_limit")
        self.assertEqual(payload["retry_after_seconds"], 10800)
        self.assertTrue(payload["retryable"])
        self.assertFalse(output.exists())

    def test_recovered_rate_limit_with_real_artifact_succeeds(self):
        result = runner.generate(self.args(self.fake_agy("quota-recovered"), self.root / "recovered.png"))
        self.assertEqual(result["width"], 800)
        self.assertTrue((self.root / "recovered.png").exists())

    def test_retry_hint_parser_supports_compound_and_short_units(self):
        self.assertEqual(runner.parse_retry_after_seconds("retry after 2h 15m")[0], 8100)
        self.assertEqual(runner.parse_retry_after_seconds("resets in 45 seconds")[0], 45)

    def test_headless_permission_error_is_actionable_and_safe(self):
        with self.assertRaisesRegex(runner.AssetError, "narrow command allow-rule"):
            runner.generate(self.args(self.fake_agy("permission"), self.root / "permission.png"))

    def test_existing_output_collision_stops_before_generation(self):
        output = self.root / "existing.png"
        output.write_bytes(b"existing")
        with self.assertRaisesRegex(runner.AssetError, "already exists"):
            runner.generate(self.args(self.fake_agy("success"), output))
        self.assertEqual(output.read_bytes(), b"existing")

    def test_output_cannot_escape_project_root(self):
        with tempfile.TemporaryDirectory() as outside:
            with self.assertRaisesRegex(runner.AssetError, "inside project root"):
                runner.generate(self.args(self.fake_agy("success"), Path(outside) / "escape.png"))

    def test_concurrent_runs_use_distinct_ids_and_outputs(self):
        import concurrent.futures
        agy = self.fake_agy("success")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(runner.generate, self.args(agy, self.root / f"final-{index}.png")) for index in range(2)]
        results = [future.result() for future in futures]
        self.assertEqual(len({result["run_id"] for result in results}), 2)


if __name__ == "__main__":
    unittest.main()
