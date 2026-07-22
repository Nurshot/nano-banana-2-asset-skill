from pathlib import Path
import json
import subprocess
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    def test_eval_catalog_has_expected_routing_cases(self):
        data = json.loads((ROOT / "evals/trigger-cases.json").read_text(encoding="utf-8"))
        cases = data["cases"]
        self.assertGreaterEqual(sum(case["expected_agy"] for case in cases), 4)
        self.assertGreaterEqual(sum(not case["expected_agy"] for case in cases), 2)
        self.assertTrue(all(case["expected_skill"] for case in cases))

    def test_synced_packages_and_zip_shape(self):
        subprocess.run([sys.executable, "scripts/build_release.py", "--version", "0.1.1"], cwd=ROOT, check=True, capture_output=True)
        subprocess.run([sys.executable, "scripts/build_release.py", "--check"], cwd=ROOT, check=True, capture_output=True)
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(marketplace["plugins"][0]["version"], "0.1.1")
        codex_marketplace = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(codex_marketplace["name"], "nano-banana-assets")
        self.assertEqual(codex_marketplace["plugins"][0]["source"]["path"], "./plugins/nano-banana-2-assets")
        for platform, manifest in (("openai", ".codex-plugin/plugin.json"), ("claude", ".claude-plugin/plugin.json")):
            archive = ROOT / f"dist/nano-banana-2-assets-{platform}-0.1.1.zip"
            self.assertLess(archive.stat().st_size, 100 * 1024 * 1024)
            with zipfile.ZipFile(archive) as zipped:
                self.assertIn(manifest, zipped.namelist())
                self.assertIn("skills/nano-banana-2-assets/SKILL.md", zipped.namelist())
                self.assertIn("commands/nano-banana.md", zipped.namelist())
                data = json.loads(zipped.read(manifest))
                self.assertEqual(data["name"], "nano-banana-2-assets")


if __name__ == "__main__":
    unittest.main()
