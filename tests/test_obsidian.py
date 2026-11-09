"""Tests for the shared Obsidian settings: the seed, the plugin pins, and the drift check. Fixtures are synthetic."""

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
SEEDED = KIT / "seed/common/notebook/.obsidian"
PINS = json.loads((KIT / "docs/obsidian-plugins.json").read_text())["plugins"]
PINNED = {pin["id"]: pin for pin in PINS}
sys.path.insert(0, str(KIT / "tools"))

import obsidian_settings as obs  # noqa: E402

spec = importlib.util.spec_from_file_location("check_obsidian", KIT / "tools/check-obsidian.py")
check_obsidian = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_obsidian)


class SeedSettingsTest(unittest.TestCase):
    def test_every_enabled_plugin_is_pinned_and_every_pin_enabled(self):
        enabled = json.loads((SEEDED / "community-plugins.json").read_text())
        self.assertEqual(sorted(enabled), sorted(PINNED))

    def test_seeded_plugin_settings_belong_to_pinned_plugins(self):
        for folder in (SEEDED / "plugins").iterdir():
            self.assertIn(folder.name, PINNED)
            self.assertEqual(["data.json"], sorted(p.name for p in folder.iterdir()), folder)

    def test_hotkeys_call_core_or_pinned_plugin_commands(self):
        core = json.loads((SEEDED / "core-plugins.json").read_text())
        for command in json.loads((SEEDED / "hotkeys.json").read_text()):
            owner = command.split(":")[0]
            self.assertTrue(owner in PINNED or core.get(owner) is True, command)

    def test_layout_preset_has_no_open_files(self):
        text = (SEEDED / "layout-preset.json").read_text()
        self.assertNotIn('"file":', text)
        self.assertNotIn("lastOpenFiles", text)
        layout = json.loads(text)
        right = json.dumps(layout["right"])
        self.assertLess(right.index('"calendar"'), right.index('"search"'))

    def test_pins_are_complete(self):
        for pin in PINS:
            self.assertRegex(pin["version"], r"^\d+\.\d+\.\d+$")
            self.assertRegex(pin["source_commit"], r"^[0-9a-f]{40}$")
            self.assertTrue(pin["release"].startswith(pin["repository"] + "/releases/tag/"))
            self.assertIn("main.js", pin["assets"])
            self.assertIn("manifest.json", pin["assets"])
            for digest in pin["assets"].values():
                self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_seed_gitignore_tracks_plugin_settings_but_not_plugin_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copy2(KIT / "seed/common/.gitignore", root / ".gitignore")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            paths = [f"notebook/.obsidian/plugins/{pid}/{name}" for pid in PINNED
                     for name in ("data.json", "main.js", "manifest.json", "styles.css")]
            paths += ["notebook/.obsidian/plugins/unreviewed/data.json", "notebook/.obsidian/workspace.json"]
            proc = subprocess.run(["git", "check-ignore", "--no-index", *paths], cwd=root, capture_output=True, text=True)
            ignored = set(proc.stdout.split())
            for path in paths:
                self.assertEqual(not path.endswith("/data.json") or "unreviewed" in path, path in ignored, path)


class CheckObsidianTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.settings = self.root / "notebook/.obsidian"
        shutil.copytree(SEEDED, self.settings)

    def states(self):
        return {name: (state, detail) for name, state, detail in check_obsidian.compare_settings(self.root)}

    def run_check(self, *args):
        return subprocess.run([sys.executable, str(KIT / "tools/check-obsidian.py"), "--root", str(self.root), *args],
                              capture_output=True, text=True)

    def test_seed_copy_is_same_even_when_reformatted(self):
        hotkeys = self.settings / "hotkeys.json"
        hotkeys.write_text(json.dumps(json.loads(hotkeys.read_text())))  # Obsidian rewrites formatting
        self.assertEqual({"same"}, {state for state, _ in self.states().values()})
        self.assertEqual(0, self.run_check("--strict").returncode)

    def test_reports_changed_keys_and_list_items(self):
        app = self.settings / "app.json"
        app.write_text(json.dumps({**json.loads(app.read_text()), "openBehavior": "file"}))
        plugins = self.settings / "community-plugins.json"
        plugins.write_text(json.dumps(json.loads(plugins.read_text())[1:] + ["local-plugin"]))
        states = self.states()
        self.assertEqual(("changed", "keys: openBehavior"), states["app.json"])
        self.assertEqual("changed", states["community-plugins.json"][0])
        self.assertIn("+local-plugin", states["community-plugins.json"][1])
        self.assertEqual(0, self.run_check().returncode)
        self.assertEqual(1, self.run_check("--strict").returncode)

    def test_reports_missing_files_in_the_configured_vault(self):
        (self.root / "knowledge-base.yaml").write_text("paths:\n  vault: vault\n")
        self.assertEqual({"missing"}, {state for state, _ in self.states().values()})

    def test_plugin_states(self):
        plugins = self.settings / "plugins"
        pin = PINS[0]
        folder = plugins / pin["id"]
        (folder / "manifest.json").write_text(json.dumps({"id": pin["id"], "version": pin["version"]}))
        (folder / "main.js").write_text("not the release\n/* nosourcemap */")
        states = dict(check_obsidian.plugin_states(self.root))
        self.assertIn("main.js differs", states[pin["id"]])
        self.assertTrue(all(states[p["id"]].startswith("not installed") for p in PINS[1:]))

    def test_plugin_matching_the_release_with_the_installer_suffix(self):
        pin = PINS[0]
        body = b"release body"
        folder = self.settings / "plugins" / pin["id"]
        (folder / "manifest.json").write_text(json.dumps({"id": pin["id"], "version": pin["version"]}))
        (folder / "main.js").write_bytes(body + obs.INSTALLER_SUFFIX)
        pins = self.root / "pins.json"
        pins.write_text(json.dumps({"plugins": [{**pin, "assets": {"main.js": hashlib.sha256(body).hexdigest()}}]}))
        self.assertEqual([(pin["id"], f"installed {pin['version']}, matches the pinned release")],
                         check_obsidian.plugin_states(self.root, pins))


class MergeTest(unittest.TestCase):
    def test_kit_change_applies_where_the_workspace_kept_the_old_value(self):
        merged, applied, kept = obs.merge({"a": 1, "b": 1}, {"a": 2, "b": 2}, {"a": 1, "b": 5})
        self.assertEqual({"a": 2, "b": 5}, merged)
        self.assertEqual(["a"], applied)
        self.assertEqual(["b"], kept)

    def test_keys_added_and_removed_by_the_kit(self):
        merged, _, _ = obs.merge({"gone": 1, "x": 0}, {"x": 0, "new": 2}, {"gone": 1, "x": 0, "mine": 3})
        self.assertEqual({"x": 0, "mine": 3, "new": 2}, merged)

    def test_lists_merge_as_sets_in_local_order(self):
        merged, applied, _ = obs.merge(["a", "b"], ["a", "c"], ["b", "a", "local"])
        self.assertEqual(["a", "local", "c"], merged)
        self.assertEqual(["(file) +c", "(file) -b"], applied)

    def test_no_old_seed_adds_kit_entries_and_keeps_local_values(self):
        merged, applied, kept = obs.merge(obs.MISSING, {"k1": [1], "k2": [2]}, {"k1": [9], "mine": []})
        self.assertEqual({"k1": [9], "mine": [], "k2": [2]}, merged)
        self.assertEqual(["k2"], applied)
        self.assertEqual(["k1"], kept)

    def test_nested_objects_merge_by_path(self):
        old = {"rules": {"r1": {"enabled": False}, "r2": {"enabled": False}}}
        new = {"rules": {"r1": {"enabled": True}, "r2": {"enabled": True}}}
        local = {"rules": {"r1": {"enabled": False}, "r2": {"enabled": "custom"}}}
        merged, applied, kept = obs.merge(old, new, local)
        self.assertEqual({"r1": {"enabled": True}, "r2": {"enabled": "custom"}}, merged["rules"])
        self.assertEqual(["rules.r1.enabled"], applied)
        self.assertEqual(["rules.r2.enabled"], kept)


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


class UpgradeObsidianTest(unittest.TestCase):
    """Replays a real upgrade, v0.2.0 to v0.2.1: the old seed lacked the shortcuts, two plugins, and the layout."""

    V020_PLUGINS = ["calendar", "obsidian-linter"]
    V020_ADDED = ("hotkeys.json", "layout-preset.json", "plugins/table-editor-obsidian/data.json")

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        old_seed = self.root / ".scions/notebook-conventions/seed/common/notebook/.obsidian"
        shutil.copytree(SEEDED, old_seed)
        for name in self.V020_ADDED:
            (old_seed / name).unlink()
        (old_seed / "community-plugins.json").write_text(json.dumps(self.V020_PLUGINS))
        self.settings = self.root / "notebook/.obsidian"
        shutil.copytree(old_seed, self.settings)
        gitignore = [line for line in (KIT / "seed/common/.gitignore").read_text().splitlines()
                     if "table-editor-obsidian" not in line and "darlal-switcher-plus" not in line]
        (self.root / ".gitignore").write_text("\n".join(gitignore) + "\n")
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "add", "-A")
        git(self.root, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "v0.2.0")

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(KIT / "tools/upgrade-obsidian.py"), "--root", str(self.root),
                               "--allow-running", *args], capture_output=True, text=True)

    def check(self, *args):
        return subprocess.run([sys.executable, str(KIT / "tools/check-obsidian.py"), "--root", str(self.root),
                               *args], capture_output=True, text=True)

    def test_unchanged_vault_ends_identical_to_the_seed(self):
        proc = self.run_tool()
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertIn("create   hotkeys.json", proc.stdout)
        self.assertIn("update   community-plugins.json: (file) +table-editor-obsidian, (file) +darlal-switcher-plus",
                      proc.stdout)
        self.assertEqual(0, self.check("--strict").returncode, self.check().stdout)
        gitignore = (self.root / ".gitignore").read_text()
        self.assertIn("!notebook/.obsidian/plugins/darlal-switcher-plus/data.json", gitignore)
        self.assertLess(gitignore.index("!notebook/.obsidian/plugins/table-editor-obsidian/\n"),
                        gitignore.index("notebook/.obsidian/plugins/*/*"))

    def test_local_changes_are_kept(self):
        (self.settings / "community-plugins.json").write_text(json.dumps(["calendar", "local-plugin"]))
        app = json.loads((self.settings / "app.json").read_text())
        (self.settings / "app.json").write_text(json.dumps({**app, "openBehavior": "file"}))
        (self.settings / "hotkeys.json").write_text(json.dumps({"darlal-switcher-plus:switcher-plus:open": []}))
        self.run_tool()
        plugins = json.loads((self.settings / "community-plugins.json").read_text())
        # The workspace removed Linter itself; the kit's additions arrive; its own plugin stays.
        self.assertEqual(["calendar", "local-plugin", "table-editor-obsidian", "darlal-switcher-plus"], plugins)
        self.assertEqual("file", json.loads((self.settings / "app.json").read_text())["openBehavior"])
        hotkeys = json.loads((self.settings / "hotkeys.json").read_text())
        self.assertEqual([], hotkeys["darlal-switcher-plus:switcher-plus:open"])
        self.assertIn("global-search:open", hotkeys)

    def test_dry_run_writes_nothing_and_a_second_run_changes_nothing(self):
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file() and ".git" not in p.parts}
        self.assertIn("would create", self.run_tool("--dry-run").stdout)
        after = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file() and ".git" not in p.parts}
        self.assertEqual(before, after)
        self.run_tool()
        second = self.run_tool().stdout
        self.assertNotIn("create", second)
        self.assertNotIn("update", second)
        self.assertNotIn("add ", second)

    def test_base_seed_from_a_v01_scion_path(self):
        git(self.root, "mv", ".scions/notebook-conventions/seed/common/notebook/.obsidian",
            ".scions/notebook-conventions/seed/common/.obsidian")
        git(self.root, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "v0.1 layout")
        self.run_tool()
        self.assertEqual(0, self.check("--strict").returncode, self.check().stdout)

    def test_an_already_committed_upgrade_asks_for_the_earlier_base(self):
        shutil.rmtree(self.root / ".scions/notebook-conventions/seed/common/notebook/.obsidian")
        shutil.copytree(SEEDED, self.root / ".scions/notebook-conventions/seed/common/notebook/.obsidian")
        git(self.root, "add", "-A")
        git(self.root, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "upgrade")
        out = self.run_tool().stdout
        self.assertIn("community-plugins.json: differ from the kit", out)
        self.assertIn("--base", out)
        self.run_tool("--base", "HEAD~1")
        self.assertEqual(0, self.check("--strict").returncode, self.check().stdout)

    def run_with_obsidian_running(self, *args):
        """Runs the tool without --allow-running, with a `pgrep` on PATH that finds Obsidian."""
        bin_dir = tempfile.TemporaryDirectory()
        self.addCleanup(bin_dir.cleanup)
        stub = Path(bin_dir.name)
        (stub / "pgrep").write_text("#!/bin/sh\nexit 0\n")
        (stub / "pgrep").chmod(0o755)
        env = {**os.environ, "PATH": f"{stub}{os.pathsep}{os.environ.get('PATH', '')}"}
        return subprocess.run([sys.executable, str(KIT / "tools/upgrade-obsidian.py"), "--root", str(self.root),
                               *args], capture_output=True, text=True, env=env)

    def snapshot(self):
        return {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file() and ".git" not in p.parts}

    def test_running_obsidian_with_a_change_pending_refuses_and_writes_nothing(self):
        before = self.snapshot()
        proc = self.run_with_obsidian_running()
        self.assertNotEqual(0, proc.returncode)
        self.assertIn("Obsidian is running", proc.stderr)
        self.assertEqual(before, self.snapshot())
        dry = self.run_with_obsidian_running("--dry-run")
        self.assertEqual(0, dry.returncode, dry.stderr)
        self.assertIn("would create", dry.stdout)
        self.assertEqual(before, self.snapshot())

    def test_running_obsidian_with_nothing_to_change_exits_0(self):
        self.assertEqual(0, self.run_tool().returncode)
        before = self.snapshot()
        proc = self.run_with_obsidian_running()
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertIn("same       app.json", proc.stdout)
        self.assertNotIn("create", proc.stdout)
        self.assertEqual(before, self.snapshot())

    def test_stale_root_settings_are_reported(self):
        (self.root / ".obsidian").mkdir()
        self.assertIn("Obsidian has opened the root as a vault", self.run_tool().stdout)
        proc = self.check()
        self.assertIn("stale: .obsidian/", proc.stdout)
        self.assertFalse((self.root / ".obsidian/app.json").exists())



upgrade_obsidian = importlib.util.module_from_spec(
    spec := importlib.util.spec_from_file_location("upgrade_obsidian", KIT / "tools/upgrade-obsidian.py"))
spec.loader.exec_module(upgrade_obsidian)


class InstallPluginsTest(unittest.TestCase):
    """Installs from a stand-in for the Nix-fetched releases, with pins written for it."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.settings, self.assets, self.pins = root / "notebook/.obsidian", root / "assets", root / "pins.json"
        pins = []
        for plugin in ("alpha", "beta"):
            files = {"main.js": f"{plugin} code".encode(), "manifest.json": json.dumps({"version": "1.0"}).encode()}
            (self.assets / plugin).mkdir(parents=True)
            for name, body in files.items():
                (self.assets / plugin / name).write_bytes(body)
            pins.append({"id": plugin, "version": "1.0",
                         "assets": {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}})
        self.pins.write_text(json.dumps({"plugins": pins}))

    def install(self, enabled=("alpha", "beta"), assets="default", dry_run=False):
        return upgrade_obsidian.install_plugins(self.settings, list(enabled),
                                                self.assets if assets == "default" else assets, dry_run, self.pins)

    def test_installs_enabled_plugins_and_keeps_their_settings(self):
        (self.settings / "plugins/alpha").mkdir(parents=True)
        (self.settings / "plugins/alpha/data.json").write_text('{"mine": true}')
        installed, manual = self.install(enabled=["alpha"])
        self.assertEqual(["install  plugin alpha 1.0"], installed)
        self.assertEqual([], manual)
        self.assertEqual(b"alpha code", (self.settings / "plugins/alpha/main.js").read_bytes())
        self.assertEqual('{"mine": true}', (self.settings / "plugins/alpha/data.json").read_text())
        self.assertFalse((self.settings / "plugins/beta").exists())

    def test_second_run_and_installer_suffix_change_nothing(self):
        self.install()
        main = self.settings / "plugins/alpha/main.js"
        main.write_bytes(main.read_bytes() + obs.INSTALLER_SUFFIX)
        self.assertEqual(([], []), self.install())

    def test_a_changed_plugin_is_updated(self):
        self.install()
        (self.settings / "plugins/beta/main.js").write_text("older release")
        self.assertEqual((["update   plugin beta 1.0"], []), self.install())
        self.assertEqual(b"beta code", (self.settings / "plugins/beta/main.js").read_bytes())

    def test_dry_run_writes_nothing(self):
        installed, _ = self.install(dry_run=True)
        self.assertEqual(2, len(installed))
        self.assertFalse((self.settings / "plugins").exists())

    def test_without_assets_lists_plugins_by_hand(self):
        installed, manual = self.install(assets=None)
        self.assertEqual([], installed)
        self.assertEqual(2, len(manual))
        self.assertIn("just upgrade-obsidian", manual[0])

    def test_assets_not_matching_the_pin_are_refused(self):
        (self.assets / "alpha/main.js").write_text("tampered")
        installed, manual = self.install(enabled=["alpha"])
        self.assertEqual([], installed)
        self.assertIn("do not match the pin", manual[0])
        self.assertFalse((self.settings / "plugins/alpha").exists())

    def test_upgrade_installs_what_the_merged_settings_enable(self):
        root = self.settings.parent.parent
        self.settings.mkdir(parents=True)
        (self.settings / "community-plugins.json").write_text(json.dumps(["calendar"]))
        report = upgrade_obsidian.upgrade(root, None, dry_run=True, assets=self.assets)
        # The merge adds the kit's plugins to the vault's list, so every pin is attempted. These stand-in assets
        # do not match the real pins, so each is refused rather than installed.
        refused = {m.split()[1] for m in report["manual"] if m.startswith("plugin ")}
        self.assertEqual({p["id"] for p in PINS}, refused)
        self.assertEqual([], report["plugins"])


if __name__ == "__main__":
    unittest.main()
