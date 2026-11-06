"""Build a workspace from seed/ the way docs/adoption.md says, then run every check on it.

Fixtures are synthetic. The scions are simulated by copying the kit's exported directories and its own
grafted meta-KB, so no network is needed. knowledge-base-integrity comes from KBI_SRC (skipped if unset).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
EXPORTED = ("docs", "templates", "skills", "tools", "nix", "seed")
PLACEHOLDER = re.compile(r"<<([A-Z_]+)>>")
VALUES = {
    "WORKSPACE_NAME": "Example Workspace",
    "ONE_LINE_DESCRIPTION": "A synthetic workspace for tests.",
    "OWNER": "the owner",
    "WHAT_WORK_BELONGS_HERE": "tests",
    "WHAT_STAYS_ELSEWHERE": "everything else",
    "SUITABLE_DATA": "synthetic data",
    "EXCLUDED_DATA": "real data",
    "APPROVED_SERVICES": "none",
    "EXCLUDED_SERVICES": "all",
}


def build_workspace(root: Path) -> None:
    for profile_or_common in ("profiles/generic", "common"):
        shutil.copytree(KIT / "seed" / profile_or_common, root, dirs_exist_ok=True,
                        copy_function=lambda s, d: None if Path(d).exists() else shutil.copy2(s, d))
    scion = root / ".scions" / "notebook-conventions"
    scion.mkdir(parents=True)
    for name in EXPORTED:
        shutil.copytree(KIT / name, scion / name)
    for name in ("README.md", "CHANGELOG.md"):
        if (KIT / name).exists():
            shutil.copy2(KIT / name, scion / name)
    shutil.copytree(KIT / ".scions" / "meta-knowledge-base", root / ".scions" / "meta-knowledge-base")
    shutil.copy2(KIT / ".scions" / "README.md", root / ".scions" / "README.md")
    for template in (scion / "templates").glob("*.md"):
        shutil.copy2(template, root / "notebook/templates" / template.name)
    for path in root.rglob("*"):
        if path.is_file() and ".scions" not in path.parts and ".obsidian" not in path.parts:
            text = path.read_text()
            if PLACEHOLDER.search(text):
                path.write_text(PLACEHOLDER.sub(lambda m: VALUES[m.group(1)], text))


class SeedTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        build_workspace(self.root)

    def run_tool(self, *args, env=None):
        return subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=self.root,
                              env={**os.environ, **(env or {}), "PYTHONDONTWRITEBYTECODE": "1"})

    def test_placeholders_are_all_documented(self):
        used = set()
        for path in (KIT / "seed").rglob("*"):
            if path.is_file():
                used |= set(PLACEHOLDER.findall(path.read_text()))
        self.assertEqual(set(), used - set(VALUES), "seed placeholders missing from the test's value map")

    def test_no_placeholders_remain_after_filling(self):
        for path in self.root.rglob("*"):
            if path.is_file() and ".scions" not in path.parts and ".obsidian" not in path.parts:
                self.assertIsNone(PLACEHOLDER.search(path.read_text()), path)

    def test_flake_imports_the_scion_wiring_conditionally(self):
        flake = (self.root / "flake.nix").read_text()
        self.assertIn("builtins.pathExists wiring", flake)
        self.assertTrue((self.root / ".scions/notebook-conventions/nix/workspace.nix").is_file())

    def test_task_check_passes_on_empty_workspace(self):
        proc = self.run_tool(str(KIT / "tools/check-tasks.py"), "--root", str(self.root))
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    def test_templates_match_canonical(self):
        proc = self.run_tool(str(KIT / "tools/check-templates.py"), "--root", str(self.root), "--strict")
        self.assertEqual(0, proc.returncode, proc.stdout)

    def test_integrity_checks_pass(self):
        kbi = os.environ.get("KBI_SRC")
        if not kbi:
            self.skipTest("KBI_SRC not set")
        proc = self.run_tool(str(KIT / "tools/check-kb.py"), "--root", str(self.root), env={"KBI_SRC": kbi})
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    def test_hook_wrapper_is_executable_and_runs_the_kit_hook(self):
        wrapper = self.root / ".githooks/pre-commit"
        self.assertTrue(os.access(wrapper, os.X_OK), "graft drops the exec bit in .scions/, so the wrapper must have it")
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.root, check=True)
        proc = subprocess.run([str(wrapper)], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)  # no staged Markdown: exits 0

    def test_skill_files_are_loadable(self):
        for skill in (self.root / ".scions/notebook-conventions/skills").glob("*/SKILL.md"):
            head = skill.read_text().split("---")[1]
            self.assertRegex(head, r"(?m)^name: " + skill.parent.name + r"$")
            self.assertRegex(head, r"(?m)^description: .{40,}")
        settings = json.loads((self.root / ".pi/settings.json").read_text())
        target = (self.root / ".pi" / settings["skills"][0]).resolve()
        self.assertTrue(target.is_dir())


if __name__ == "__main__":
    unittest.main()
