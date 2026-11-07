"""Tests for the shared Obsidian settings: the seed, the plugin pins, and the drift check. Fixtures are synthetic."""

import hashlib
import importlib.util
import json
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
        (folder / "main.js").write_bytes(body + check_obsidian.INSTALLER_SUFFIX)
        pins = self.root / "pins.json"
        pins.write_text(json.dumps({"plugins": [{**pin, "assets": {"main.js": hashlib.sha256(body).hexdigest()}}]}))
        self.assertEqual([(pin["id"], f"installed {pin['version']}, matches the pinned release")],
                         check_obsidian.plugin_states(self.root, pins))


if __name__ == "__main__":
    unittest.main()
