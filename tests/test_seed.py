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

    def test_seed_pins_the_release_it_ships_in(self):
        newest = re.search(r"^## (v[0-9.]+)", (KIT / "CHANGELOG.md").read_text(), re.M).group(1)
        self.assertIn(f"notebook-conventions/{newest}\"", (KIT / "seed/common/flake.nix").read_text())

    def test_seed_pins_the_graft_the_kit_uses(self):
        pin = re.search(r"danielnaab/graft/v[0-9.]+", (KIT / "flake.nix").read_text()).group(0)
        self.assertIn(pin, (KIT / "seed/common/flake.nix").read_text())

    def test_flake_reads_the_wiring_from_the_pinned_kit(self):
        # From the input, not .scions/, so the dev shell and checks exist before the first graft.
        flake = (self.root / "flake.nix").read_text()
        self.assertIn('import "${inputs.notebook-conventions}/nix/workspace.nix"', flake)
        self.assertEqual("use flake\n", (self.root / ".envrc").read_text())

    def test_task_check_passes_on_empty_workspace(self):
        proc = self.run_tool(str(KIT / "tools/check-tasks.py"), "--root", str(self.root))
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    def test_templates_match_canonical(self):
        proc = self.run_tool(str(KIT / "tools/check-templates.py"), "--root", str(self.root), "--strict")
        self.assertEqual(0, proc.returncode, proc.stdout)

    def test_obsidian_settings_match_the_seed(self):
        proc = self.run_tool(str(KIT / "tools/check-obsidian.py"), "--root", str(self.root), "--strict")
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    def test_integrity_checks_pass(self):
        kbi = os.environ.get("KBI_SRC")
        if not kbi:
            self.skipTest("KBI_SRC not set")
        proc = self.run_tool(str(KIT / "tools/check-kb.py"), "--root", str(self.root), env={"KBI_SRC": kbi})
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    def test_indexes_are_current(self):
        kbi = os.environ.get("KBI_SRC")
        if not kbi:
            self.skipTest("KBI_SRC not set")
        proc = self.run_tool(str(KIT / "tools/index.py"), "--root", str(self.root), "--check", env={"KBI_SRC": kbi})
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    def test_vault_settings_live_in_the_vault(self):
        self.assertFalse((self.root / ".obsidian").exists())
        daily = json.loads((self.root / "notebook/.obsidian/daily-notes.json").read_text())
        self.assertEqual("records/daily", daily["folder"])
        self.assertTrue((self.root / "notebook" / (daily["template"] + ".md")).is_file())

    def test_hook_wrapper_is_executable_and_runs_the_kit_hook(self):
        wrapper = self.root / ".githooks/pre-commit"
        self.assertTrue(os.access(wrapper, os.X_OK), "graft drops the exec bit in .scions/, so the wrapper must have it")
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.root, check=True)
        proc = subprocess.run([str(wrapper)], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)  # no staged Markdown: exits 0

    def test_hook_skips_staged_scion_markdown(self):
        # Explicit paths bypass markdownlint's ignores, so the hook must not pass .scions/ files at all:
        # the scion's seed links resolve only inside a workspace, and every graft upgrade stages .scions/.
        stubs = self.root / ".stubs"
        stubs.mkdir()
        record = self.root / ".lint-args"
        (stubs / "markdownlint-cli2").write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > "{record}"\n')
        (stubs / "nix").write_text("#!/bin/sh\nexit 0\n")
        for stub in stubs.iterdir():
            stub.chmod(0o755)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "README.md", ".scions/notebook-conventions/README.md"], cwd=self.root, check=True)
        proc = subprocess.run([str(self.root / ".githooks/pre-commit")], cwd=self.root, capture_output=True,
                              text=True, env={**os.environ, "PATH": f"{stubs}{os.pathsep}{os.environ['PATH']}"})
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertEqual(["--no-globs", "README.md"], record.read_text().split())

    def test_hook_never_runs_nix_without_a_root_flake(self):
        # A workspace whose flake is in a subdirectory: with no tools on PATH the hook says so, and never runs nix.
        stubs = self.root / ".stubs"
        stubs.mkdir()
        called = self.root / ".nix-called"
        (stubs / "nix").write_text(f'#!/bin/sh\ntouch "{called}"\n')
        (stubs / "nix").chmod(0o755)
        (self.root / "flake.nix").unlink()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "README.md"], cwd=self.root, check=True)
        for tool in ("git", "sh"):  # PATH holds only these and the stub, whatever else the machine has
            (stubs / tool).symlink_to(shutil.which(tool))
        proc = subprocess.run([str(stubs / "sh"), str(self.root / ".githooks/pre-commit")], cwd=self.root,
                              capture_output=True, text=True, env={**os.environ, "PATH": str(stubs)})
        self.assertEqual(1, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("no flake.nix at the top", proc.stderr)
        self.assertFalse(called.exists())

    def test_skill_files_are_loadable(self):
        for skill in (self.root / ".scions/notebook-conventions/skills").glob("*/SKILL.md"):
            head = skill.read_text().split("---")[1]
            self.assertRegex(head, r"(?m)^name: " + skill.parent.name + r"$")
            self.assertRegex(head, r"(?m)^description: .{40,}")
        settings = json.loads((self.root / ".pi/settings.json").read_text())
        target = (self.root / ".pi" / settings["skills"][0]).resolve()
        self.assertTrue(target.is_dir())


JUST = shutil.which("just")
KIT_RECIPES = {
    "check": ["check", "graft-check", "check-kb", "check-tasks", "check-templates", "check-obsidian"],
    "notes": ["index", "move"],
    "deps": ["outdated", "changelog", "upgrade", "migrate", "sync"],
    "migrations": ["convert", "upgrade-obsidian"],
}


@unittest.skipUnless(JUST, "just not on PATH")
class JustMenuTest(unittest.TestCase):
    """The seeded justfile imports the kit's menu from the scion; recipes pass arguments through intact."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        build_workspace(self.root)
        # Stub tools record one line per call: their name and arguments, separated by \x1f, so quoting is exact.
        self.stubs = self.root / ".stubs"
        self.stubs.mkdir()
        self.log = self.root / ".calls"
        for name in ("check-kb", "check-tasks", "check-templates", "check-obsidian", "index", "move", "convert",
                     "upgrade-obsidian", "graft"):
            stub = self.stubs / name
            stub.write_text(f'#!/bin/sh\n{{ printf {name}; for a; do printf "\\037%s" "$a"; done; echo; }} >> "{self.log}"\n')
            stub.chmod(0o755)
        self.env = {**os.environ, "KIT_RUN": f"{self.stubs}/{{}}", "GRAFT_RUN": str(self.stubs / "graft")}

    def just(self, *args, cwd=None, env=None):
        return subprocess.run([JUST, *args], capture_output=True, text=True, cwd=cwd or self.root,
                              env=env or self.env)

    def calls(self):
        if not self.log.exists():
            return []
        return [line.split("\x1f") for line in self.log.read_text().splitlines()]

    def test_no_arguments_lists_the_grouped_menu(self):
        proc = self.just()
        self.assertEqual(0, proc.returncode, proc.stderr)
        for group, recipes in KIT_RECIPES.items():
            self.assertIn(f"[{group}]", proc.stdout)
            for recipe in recipes:
                line = re.search(rf"(?m)^\s+{re.escape(recipe)}\b.*# (.+)$", proc.stdout)
                self.assertIsNotNone(line, f"{recipe} is listed with a description")
        self.assertNotRegex(proc.stdout, r"(?m)^\s+(check-local|default)\b", "private recipes stay unlisted")
        # just finds the workspace justfile from inside the vault
        self.assertEqual(proc.stdout, self.just(cwd=self.root / "notebook").stdout)

    def test_every_recipe_resolves(self):
        for recipes in KIT_RECIPES.values():
            for recipe in recipes:
                proc = self.just("--show", recipe)
                self.assertEqual(0, proc.returncode, proc.stderr)

    def test_default_runs_tools_and_graft_through_the_root_flake(self):
        env = {k: v for k, v in os.environ.items() if k not in ("KIT_RUN", "GRAFT_RUN")}
        proc = self.just("--dry-run", "check-kb", "--root", ".", env=env)
        self.assertIn('nix run .#check-kb -- "$@"', proc.stderr)
        proc = self.just("--dry-run", "upgrade", "x@v1", env=env)
        self.assertIn('nix run .#graft -- upgrade "$@"', proc.stderr)

    def test_check_runs_every_kit_check(self):
        proc = self.just("check")
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual([["graft", "check"], ["check-kb"], ["check-tasks"], ["index", "--check"], ["check-obsidian"]],
                         self.calls())

    def test_arguments_pass_through_intact(self):
        proc = self.just("move", "notebook/a b.md", "notebook/c.md", "--dry-run", cwd=self.root / "notebook")
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.just("index", "--check")
        self.just("changelog", "notebook-conventions")
        self.assertEqual([["move", "notebook/a b.md", "notebook/c.md", "--dry-run"], ["index", "--check"],
                          ["graft", "changelog", "notebook-conventions"]], self.calls())

    def test_sync_runs_graft_bare_and_upgrade_applies_obsidian_and_lists_next_steps(self):
        self.just("sync")
        proc = self.just("upgrade", "notebook-conventions@v9.9.9")
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual([["graft"], ["graft", "upgrade", "notebook-conventions@v9.9.9"], ["upgrade-obsidian"]],
                         self.calls())
        for step in ("just changelog", "just migrate", "just check", "Commit"):
            self.assertIn(step, proc.stdout)

    def test_workspace_overrides_how_tools_run_and_extends_check(self):
        env = {k: v for k, v in os.environ.items() if k not in ("KIT_RUN", "GRAFT_RUN")}
        with (self.root / "justfile").open("a") as justfile:
            justfile.write(f'\nkit_run := "{self.stubs}/{{}}"\ngraft_run := "{self.stubs}/graft"\n'
                           f'\ncheck-local:\n    @echo local >> "{self.log}"\n')
        proc = self.just("check", env=env)
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual([["graft", "check"], ["check-kb"], ["check-tasks"], ["index", "--check"], ["check-obsidian"],
                          ["local"]], self.calls())
        self.just("outdated", env=env)
        self.assertEqual(["graft", "outdated"], self.calls()[-1])

    def test_check_passes_with_the_real_tools(self):
        kbi = os.environ.get("KBI_SRC")
        if not kbi:
            self.skipTest("KBI_SRC not set")
        tools = self.root / ".scions/notebook-conventions/tools"
        # graft check needs the workspace's flake; its own tests cover it
        env = {**os.environ, "KIT_RUN": f"{sys.executable} {tools}/{{}}.py", "GRAFT_RUN": "true",
               "PYTHONDONTWRITEBYTECODE": "1"}
        proc = self.just("check", env=env)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("all checks passed", proc.stdout)


if __name__ == "__main__":
    unittest.main()
