"""Vault identities: backwards-compatible rendering, safe labels, theme variants, and upgrade/check lifecycle."""

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
sys.path.insert(0, str(KIT / "tools"))
import obsidian_settings as obs  # noqa: E402

spec = importlib.util.spec_from_file_location("identity_upgrade", KIT / "tools/upgrade-obsidian.py")
upgrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade)

CONFIG = {"identity": {"label": "Workspace A", "accent": {"light": "#3366cc", "dark": "#99bbff"},
                       "stripe": ["#3366cc", "#ffffff", "#cc6633"]}}


class IdentityRendererTest(unittest.TestCase):
    def validate(self, config):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "declaration.json"
            path.write_text(json.dumps(config))
            return obs.workspace_config(path)

    def test_old_single_color_identity_is_byte_for_byte_unchanged(self):
        config = self.validate({"identity": {"accent": "#3366cc"}})
        self.assertEqual(obs.IDENTITY_HEADER + '\nbody::before {\n'
                         '  content: "";\n  position: fixed;\n  inset: 0 0 auto 0;\n  height: 3px;\n'
                         '  background: linear-gradient(to right, #3366cc 0% 100%);\n'
                         '  z-index: 1000;\n  pointer-events: none;\n}\n', obs.identity_css(config))
        self.assertEqual("#3366cc", obs.declared_settings(config)["appearance.json"]["accentColor"])
        self.validate({"identity": {"accent": "rebeccapurple"}})  # legacy CSS colors still work
        self.assertIsNone(obs.identity_css({}))

    def test_variants_set_the_static_fallback_but_switch_accent_variables_by_theme(self):
        config = self.validate(CONFIG)
        self.assertEqual("#3366cc", obs.declared_settings(config)["appearance.json"]["accentColor"])
        css = obs.identity_css(config)
        for theme, color in CONFIG["identity"]["accent"].items():
            self.assertIn(f"body.theme-{theme} {{", css)
            self.assertIn(f"--color-accent: {color} !important;", css)
            self.assertIn(f"--color-accent-1: {color} !important;", css)
        for variable in ("accent-h", "accent-s", "accent-l", "color-accent-hsl", "color-accent-2",
                         "text-accent", "text-accent-hover", "interactive-accent", "interactive-accent-hover",
                         "text-on-accent", "text-on-accent-inverted"):
            self.assertEqual(2, css.count(f"--{variable}:"), variable)
        self.assertIn('content: "Workspace A";', css)
        self.assertIn("body:not(.is-mobile) .status-bar::before", css)
        self.assertIn("order: -1;", css)
        self.assertIn("background-color: #3366cc;", css)  # badge does not lighten with dark-mode accents
        self.assertIn("color: #ffffff;", css)
        self.assertEqual(2, css.count("pointer-events: none;"))

    def test_default_stripe_uses_the_light_color_not_a_serialized_object(self):
        config = {"identity": {"accent": CONFIG["identity"]["accent"]}}
        self.assertIn("#3366cc 0% 100%", obs.identity_css(config))
        self.assertNotIn("status-bar", obs.identity_css(config))

    def test_label_quotes_and_backslashes_are_escaped_not_executable_css(self):
        label = 'Workspace "A" \\ "; } body { display: none; } /*'
        config = self.validate({"identity": {"accent": "#3366cc", "label": label}})
        expected = label.replace("\\", "\\\\").replace('"', '\\"')
        self.assertIn(f'content: "{expected}";', obs.identity_css(config))
        unicode_config = self.validate({"identity": {"accent": "#3366cc", "label": "Workspace — Ω"}})
        self.assertIn('content: "Workspace — Ω";', obs.identity_css(unicode_config))

    def test_invalid_variant_shapes_and_css_injection_are_refused(self):
        for accent in ({}, {"light": "#3366cc"}, {"light": "#3366cc", "dark": "#99bbff", "other": "#000000"},
                       {"light": "#3366cc", "dark": "red"}, {"light": "#3366cc", "dark": 3},
                       {"light": "#3366cc", "dark": "#99bbff; } body {display:none}"},
                       {"light": "#3366cc", "dark": "#zzzfff"}):
            with self.subTest(accent=accent), self.assertRaisesRegex(ValueError, "light.*dark"):
                self.validate({"identity": {"accent": accent}})
        for label in ("", "  ", "multi\nline", "x\r", "x\x00", "x\x7f", "x" * 65, 123, None):
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, "identity.label"):
                self.validate({"identity": {"accent": "#3366cc", "label": label}})

    def test_hover_direction_and_control_foreground(self):
        for theme, color, background in (("light", "#3366cc", "#ffffff"), ("dark", "#99bbff", "#282828")):
            _, hover, foreground = obs._accent_states(color, theme)
            if theme == "light":
                self.assertLess(obs._luminance(hover), obs._luminance(color))
                self.assertEqual("#ffffff", foreground)
            else:
                self.assertGreater(obs._luminance(hover), obs._luminance(color))
                self.assertEqual("#000000", foreground)
            for state in (color, hover):
                for surface in (background, foreground):
                    a, b = sorted((obs._luminance(state), obs._luminance(surface)))
                    self.assertGreaterEqual((b + 0.05) / (a + 0.05), 4.5)
        self.assertEqual("#ffffff", obs._foreground(["#000000"]))
        self.assertEqual("#000000", obs._foreground(["#ffffff"]))


class IdentityLifecycleTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.settings = self.root / "notebook/.obsidian"
        shutil.copytree(obs.SEEDED, self.settings)
        shutil.copytree(obs.SEEDED, self.root / ".scions/notebook-kit/seed/common/notebook/.obsidian")
        shutil.copy2(KIT / "seed/common/.gitignore", self.root / ".gitignore")
        for args in (("init", "-q", "-b", "main"), ("add", "-A"),
                     ("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", "seed")):
            subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)
        self.config_path = self.root / "declaration.json"
        self.css = self.settings / "snippets/vault-identity.css"

    def apply(self, config, dry_run=False):
        self.config_path.write_text(json.dumps(config))
        return upgrade.upgrade(self.root, "HEAD", dry_run, plugins=False, config=config)

    def check(self):
        env = {**os.environ, obs.WORKSPACE_ENV: str(self.config_path)}
        return subprocess.run([sys.executable, str(KIT / "tools/check-obsidian.py"), "--root", str(self.root),
                               "--strict"], env=env, capture_output=True, text=True)

    def snapshot(self):
        return {p.relative_to(self.settings): p.read_bytes() for p in self.settings.rglob("*") if p.is_file()}

    def test_dry_run_apply_strict_check_drift_and_idempotence(self):
        before = self.snapshot()
        report = self.apply(CONFIG, dry_run=True)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(["create   snippets/vault-identity.css"], report["identity"])
        self.apply(CONFIG)
        self.assertEqual(obs.identity_css(CONFIG), self.css.read_text())
        self.assertEqual(0, self.check().returncode, self.check().stdout)
        before = self.snapshot()
        report = self.apply(CONFIG)
        self.assertEqual([], report["identity"])
        self.assertEqual({}, report["declared"])
        self.assertEqual(before, self.snapshot())
        self.css.write_text(self.css.read_text().replace("Workspace A", "Workspace B"))
        self.assertEqual(1, self.check().returncode)
        self.apply(CONFIG)
        self.assertEqual(0, self.check().returncode, self.check().stdout)
        self.css.unlink()
        self.assertEqual(1, self.check().returncode)

    def test_changing_or_removing_label_and_variants_regenerates_css(self):
        self.apply(CONFIG)
        config = {"identity": {**CONFIG["identity"], "label": "Workspace B"}}
        self.apply(config)
        self.assertIn('content: "Workspace B"', self.css.read_text())
        self.assertEqual(0, self.check().returncode, self.check().stdout)
        config = {"identity": {"accent": "#3366cc"}}
        self.apply(config)
        self.assertNotIn("status-bar", self.css.read_text())
        self.assertNotIn("theme-dark", self.css.read_text())
        self.assertEqual(0, self.check().returncode, self.check().stdout)
        appearance = json.loads((self.settings / "appearance.json").read_text())
        appearance["enabledCssSnippets"].insert(0, "local-snippet")
        (self.settings / "appearance.json").write_text(json.dumps(appearance))
        self.apply({})
        self.assertFalse(self.css.exists())
        appearance = json.loads((self.settings / "appearance.json").read_text())
        self.assertEqual(["local-snippet"], appearance["enabledCssSnippets"])


if __name__ == "__main__":
    unittest.main()
