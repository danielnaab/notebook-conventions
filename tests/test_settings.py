"""The workspace's settings file (notebook-kit.yaml), and finding the kit where graft put it (a git submodule)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "tools"))
import kit_settings  # noqa: E402
import obsidian_settings as obs  # noqa: E402

MARKER = "<!-- managed by graft: https://github.com/danielnaab/graft -->"
GIT = ["git", "-c", "user.email=t@example.com", "-c", "user.name=t", "-c", "commit.gpgsign=false",
       "-c", "protocol.file.allow=always"]


def git(root, *args):
    return subprocess.run([*GIT, "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


class SettingsFileTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def write(self, text):
        (self.root / "notebook-kit.yaml").write_text(text)

    def test_absent_or_empty_means_the_defaults(self):
        self.assertEqual({}, kit_settings.load(self.root))
        self.write("# nothing set yet\n")
        self.assertEqual({}, kit_settings.load(self.root))
        self.assertEqual({}, obs.workspace_config(self.root))

    def test_unknown_keys_and_wrong_types_name_the_file(self):
        for text, words in (("obsidan: {}\n", "unknown keys obsidan"), ("tasks: maybe\n", "tasks"),
                            ("- a\n", "a mapping"), ("obsidian:\n  theme: dark\n", "obsidian")):
            self.write(text)
            with self.assertRaises(ValueError) as error:
                obs.workspace_config(self.root)
            self.assertIn("notebook-kit.yaml", str(error.exception))
            self.assertIn(words, str(error.exception))

    def test_obsidian_section_is_the_declaration(self):
        self.write("obsidian:\n  settings:\n    app.json:\n      openBehavior: file\n"
                   "  identity:\n    label: Work\n    accent: {light: '#155fc8', dark: '#6ea8f5'}\n")
        config = obs.workspace_config(self.root)
        self.assertEqual({"openBehavior": "file"}, config["settings"]["app.json"])
        self.assertEqual("#155fc8", obs.declared_settings(config)["appearance.json"]["accentColor"])

    def test_check_obsidian_reports_a_bad_settings_file(self):
        (self.root / "notebook/.obsidian").mkdir(parents=True)
        self.write("obsidian:\n  identity: {}\n")
        proc = subprocess.run([sys.executable, str(KIT / "tools/check-obsidian.py"), "--root", str(self.root)],
                              capture_output=True, text=True)
        self.assertNotEqual(0, proc.returncode)
        self.assertIn("notebook-kit.yaml", proc.stderr)

    def test_tasks_false_skips_the_task_check(self):
        run = lambda: subprocess.run([sys.executable, str(KIT / "tools/check-tasks.py"), "--root", str(self.root)],
                                     capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(1, run().returncode, "no notebook/tasks and no settings: the check fails")
        self.write("tasks: false\n")
        proc = run()
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("tasks: false", proc.stdout)


class KitScionTest(unittest.TestCase):
    """The kit is a git submodule in the scions directory graft's marker README names, wherever that is."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        # the kit's repository: two releases whose seeded app.json differ
        self.kit = base / "kit"
        seed = self.kit / "seed/common/notebook/.obsidian"
        seed.mkdir(parents=True)
        git(self.kit, "init", "-q", "-b", "main")
        (seed / "app.json").write_text(json.dumps({"v": 1}))
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "v1")
        self.v1 = git(self.kit, "rev-parse", "HEAD").strip()
        (seed / "app.json").write_text(json.dumps({"v": 2}))
        git(self.kit, "commit", "-qam", "v2")
        self.v2 = git(self.kit, "rev-parse", "HEAD").strip()
        # a workspace whose flake (and so its scions) sits in a subdirectory
        self.root = base / "ws"
        self.root.mkdir()
        git(self.root, "init", "-q", "-b", "main")
        self.scions = "nix/agent-tools/.scions"
        (self.root / self.scions).mkdir(parents=True)
        (self.root / self.scions / "README.md").write_text(MARKER + "\n# Scions\n")
        git(self.root, "submodule", "add", "-q", self.kit.as_uri(), f"{self.scions}/notebook-kit")
        git(self.root / self.scions / "notebook-kit", "checkout", "-q", "--detach", self.v1)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "graft the kit at v1")

    def test_scions_directory_is_found_by_graft_marker(self):
        self.assertEqual([self.scions], kit_settings.scions_dirs(self.root))

    def test_base_seed_reads_the_old_release_from_the_submodule(self):
        # `graft upgrade` moves the submodule and stages it; HEAD still records v1 until the commit
        git(self.root / self.scions / "notebook-kit", "checkout", "-q", "--detach", self.v2)
        git(self.root, "add", f"{self.scions}/notebook-kit")
        self.assertEqual({"v": 1}, obs.base_seed(self.root, "HEAD", "app.json"))
        self.assertIs(obs.MISSING, obs.base_seed(self.root, "HEAD", "absent.json"))


if __name__ == "__main__":
    unittest.main()
