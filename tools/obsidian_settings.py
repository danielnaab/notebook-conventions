"""Shared helpers for a vault's Obsidian settings: where they live, the kit's seeded copies, and a three-way merge."""

from __future__ import annotations

import colorsys
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import yaml

KIT = Path(__file__).resolve().parents[1]
SEEDED = KIT / "seed/common/notebook/.obsidian"
SEED_GITIGNORE = KIT / "seed/common/.gitignore"
PINS = KIT / "docs/obsidian-plugins.json"
DEFAULT_VAULT = "notebook"
# The pinned release assets, one folder per plugin id, which the kit's Nix wiring fetches and checks against PINS
# (nix/workspace.nix). Unset when a tool runs outside it.
PLUGIN_ASSETS_ENV = "OBSIDIAN_PLUGIN_ASSETS"
# The workspace's declared Obsidian deviations, the `obsidian` argument to nix/workspace.nix as JSON. Unset when
# the workspace declares none or a tool runs outside the kit's Nix wiring.
WORKSPACE_ENV = "OBSIDIAN_WORKSPACE"
# The CSS snippet rendered from `obsidian.identity`: stripe, optional label, and theme-aware accents.
IDENTITY_SNIPPET = "vault-identity"
IDENTITY_HEADER = "/* Rendered by notebook-kit upgrade-obsidian from obsidian.identity in the workspace's flake. */"
# Obsidian's in-app installer appends this to main.js; the pinned hashes are of the release assets.
INSTALLER_SUFFIX = b"\n/* nosourcemap */"
# Where kit versions kept the seeded settings inside the scion: v1.0 and later, then the same layouts under the
# kit's earlier name (v0.2 to v0.7, then v0.1). An upgrade from notebook-conventions reads its old seed by git ref.
SCION_SEED_PATHS = (".scions/notebook-kit/seed/common/notebook/.obsidian",
                    ".scions/notebook-kit/seed/common/.obsidian",
                    ".scions/notebook-conventions/seed/common/notebook/.obsidian",
                    ".scions/notebook-conventions/seed/common/.obsidian")


class Missing:
    """A key or file that is absent, distinct from a JSON null."""

    def __repr__(self) -> str:
        return "absent"


MISSING = Missing()


def plugin_assets() -> Path | None:
    value = os.environ.get(PLUGIN_ASSETS_ENV)
    return Path(value) if value else None


def asset_matches(path: Path, sha256: str) -> bool:
    """Whether a plugin file is the pinned release asset, allowing the in-app installer's main.js suffix."""
    if not path.is_file():
        return False
    data = path.read_bytes()
    if path.name == "main.js" and data.endswith(INSTALLER_SUFFIX):
        data = data[: -len(INSTALLER_SUFFIX)]
    return hashlib.sha256(data).hexdigest() == sha256


def workspace_config(path: Path | None = None) -> dict:
    """The workspace's declared deviations: `settings` (settings file -> partial JSON) and `identity`."""
    if path is None:
        value = os.environ.get(WORKSPACE_ENV)
        if not value:
            return {}
        path = Path(value)
    config = json.loads(path.read_text())
    if not isinstance(config, dict):
        raise ValueError(f"{path}: expected an object with `settings` and `identity`")
    unknown = sorted(set(config) - {"settings", "identity"})
    if unknown:
        raise ValueError(f"{path}: unknown keys {', '.join(unknown)}; expected `settings` and `identity`")
    for name, value in (config.get("settings") or {}).items():
        if not name.endswith(".json") or not isinstance(value, dict):
            raise ValueError(f"{path}: settings.{name} must be a JSON settings file name mapped to an object")
    identity = config.get("identity")
    if identity is not None:
        if not isinstance(identity, dict):
            raise ValueError(f"{path}: identity needs `accent`, a CSS color or a light/dark color object")
        accent = identity.get("accent")
        if isinstance(accent, dict):
            if (set(accent) != {"light", "dark"}
                    or any(not isinstance(c, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", c)
                           for c in accent.values())):
                raise ValueError(f"{path}: identity.accent needs exactly `light` and `dark` #RRGGBB colors")
        elif not isinstance(accent, str):
            raise ValueError(f"{path}: identity needs `accent`, a CSS color or a light/dark color object")
        stripe = identity.get("stripe", [identity_accent(identity)])
        if not (isinstance(stripe, list) and stripe and all(isinstance(c, str) for c in stripe)):
            raise ValueError(f"{path}: identity.stripe must be a non-empty list of CSS colors")
        if "label" in identity:
            label = identity["label"]
            if (not isinstance(label, str) or not label.strip() or not label.isprintable()
                    or len(label) > 64):
                raise ValueError(f"{path}: identity.label must be 1–64 printable characters on one line")
    return config


def identity_accent(identity: dict) -> str:
    """The stable stripe/badge color and appearance fallback; theme variants use their light color."""
    accent = identity["accent"]
    return accent["light"] if isinstance(accent, dict) else accent


def _rgb(color: str) -> tuple[float, float, float]:
    return tuple(int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))


def _luminance(color: str) -> float:
    channels = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in _rgb(color)]
    return sum(v * weight for v, weight in zip(channels, (0.2126, 0.7152, 0.0722)))


def _foreground(colors: list[str]) -> str:
    """Black or white with the best worst-case contrast across the accent and its hover state."""
    if any(not re.fullmatch(r"#[0-9a-fA-F]{6}", c) for c in colors):
        return "var(--text-on-accent)"  # legacy single CSS colors need not be hex
    black = min((_luminance(c) + 0.05) / 0.05 for c in colors)
    white = min(1.05 / (_luminance(c) + 0.05) for c in colors)
    return "#000000" if black > white else "#ffffff"


def _accent_states(color: str, theme: str) -> tuple[tuple[float, float, float], str, str]:
    """HSL, hover color, and control foreground. Hover darkens in light mode, lightens in dark mode."""
    h, lightness, saturation = colorsys.rgb_to_hls(*_rgb(color))
    hover_rgb = colorsys.hls_to_rgb(h, min(1, lightness * (0.9 if theme == "light" else 1.1)), saturation)
    hover = "#" + "".join(f"{round(v * 255):02x}" for v in hover_rgb)
    return (h * 360, saturation * 100, lightness * 100), hover, _foreground([color, hover])


def declared_settings(config: dict) -> dict[str, dict]:
    """Settings file -> the values the workspace declares, with `identity` expanded into appearance.json."""
    settings = {name: value for name, value in (config.get("settings") or {}).items()}
    identity = config.get("identity")
    if identity:
        settings["appearance.json"] = overlay(
            {"accentColor": identity_accent(identity), "enabledCssSnippets": [IDENTITY_SNIPPET]},
            settings.get("appearance.json", {}))
    return settings


def identity_css(config: dict) -> str | None:
    """The non-clickable stripe, optional desktop status-bar badge, and theme-scoped accent variables."""
    identity = config.get("identity")
    if not identity:
        return None
    accent = identity_accent(identity)
    colors = identity.get("stripe") or [accent]
    width = 100 / len(colors)
    stops = ", ".join(f"{c} {i * width:g}% {(i + 1) * width:g}%" for i, c in enumerate(colors))
    css = (f"{IDENTITY_HEADER}\n"
            "body::before {\n"
            "  content: \"\";\n"
            "  position: fixed;\n"
            "  inset: 0 0 auto 0;\n"
            "  height: 3px;\n"
            f"  background: linear-gradient(to right, {stops});\n"
            "  z-index: 1000;\n"
            "  pointer-events: none;\n"
            "}\n")
    if isinstance(identity["accent"], dict):
        for theme in ("light", "dark"):
            color = identity["accent"][theme]
            (h, s, lightness), hover, foreground = _accent_states(color, theme)
            inverse = "#ffffff" if foreground == "#000000" else "#000000"
            # Obsidian writes accent HSL inline on body. Theme-scoped !important beats that static fallback.
            # Explicit accent/hover states avoid the app's mode-specific brightening reducing link contrast.
            css += (f"\nbody.theme-{theme} {{\n"
                    f"  --accent-h: {h:.6f} !important;\n"
                    f"  --accent-s: {s:.6f}% !important;\n"
                    f"  --accent-l: {lightness:.6f}% !important;\n"
                    f"  --color-accent-hsl: {h:.6f}, {s:.6f}%, {lightness:.6f}% !important;\n"
                    f"  --color-accent: {color} !important;\n"
                    f"  --color-accent-1: {color} !important;\n"
                    f"  --color-accent-2: {hover} !important;\n"
                    f"  --text-accent: {color} !important;\n"
                    f"  --text-accent-hover: {hover} !important;\n"
                    f"  --interactive-accent: {color} !important;\n"
                    f"  --interactive-accent-hover: {hover} !important;\n"
                    f"  --text-on-accent: {foreground} !important;\n"
                    f"  --text-on-accent-inverted: {inverse} !important;\n"
                    "}\n")
    if identity.get("label"):
        # A CSS string, not markup or executable CSS; control characters were refused by workspace_config.
        label = identity["label"].replace("\\", "\\\\").replace('"', '\\"')
        css += ("\nbody:not(.is-mobile) .status-bar::before {\n"
                f'  content: "{label}";\n'
                f"  background-color: {accent};\n"
                f"  color: {_foreground([accent])};\n"
                "  order: -1;\n"
                "  flex: 0 1 auto;\n"
                "  min-width: 0;\n"
                "  max-width: 18em;\n"
                "  align-self: center;\n"
                "  padding: 3px 6px;\n"
                "  border-radius: 3px;\n"
                "  font-size: var(--font-ui-smaller);\n"
                "  font-weight: 600;\n"
                "  line-height: 1;\n"
                "  white-space: nowrap;\n"
                "  overflow: hidden;\n"
                "  text-overflow: ellipsis;\n"
                "  pointer-events: none;\n"
                "}\n")
    return css


def overlay(base, patch):
    """A declared value over another: objects key by key, lists of plain values gain the patch's items, else patch."""
    if isinstance(base, dict) and isinstance(patch, dict):
        return {**base, **{k: overlay(base.get(k, MISSING), v) for k, v in patch.items()}}
    if (isinstance(base, list) and isinstance(patch, list)
            and all(not isinstance(v, (dict, list)) for v in [*base, *patch])):
        return base + [v for v in patch if v not in base]
    return patch


def vault_folder(root: Path) -> str:
    config = root / "knowledge-base.yaml"
    if config.is_file():
        data = yaml.safe_load(config.read_text()) or {}
        value = (data.get("paths") or {}).get("vault")
        if isinstance(value, str) and value.strip("/"):
            return value.strip("/")
    return DEFAULT_VAULT


def settings_dir(root: Path) -> Path:
    return root / vault_folder(root) / ".obsidian"


def seeded_files(seeded: Path = SEEDED) -> list[str]:
    return sorted(p.relative_to(seeded).as_posix() for p in seeded.rglob("*.json") if p.is_file())


def stale_root_settings(root: Path) -> Path | None:
    """A `.obsidian/` at the repository root when the vault is a subfolder.

    Obsidian keeps its own list of vaults. After the vault moves into `notebook/`, the old entry still opens the
    repository root, and Obsidian then writes fresh default settings there: no community plugins, no shortcuts.
    """
    if vault_folder(root) in ("", "."):
        return None
    path = root / ".obsidian"
    return path if path.is_dir() else None


def base_seed(root: Path, ref: str, name: str):
    """The kit's seeded copy of a settings file in the scion at a git ref, or MISSING."""
    for folder in SCION_SEED_PATHS:
        proc = subprocess.run(["git", "-C", str(root), "show", f"{ref}:{folder}/{name}"],
                              capture_output=True, text=True)
        if proc.returncode == 0:
            try:
                return json.loads(proc.stdout)
            except json.JSONDecodeError:
                return MISSING
    return MISSING


def git_ref_exists(root: Path, ref: str) -> bool:
    return subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
                          capture_output=True).returncode == 0


def _describe(old, new, label: str) -> list[str]:
    """What the kit changed, for a value taken whole: list items added and removed, or the object keys."""
    if isinstance(new, list) and isinstance(old, list):
        return [f"{label} +{v}" for v in new if v not in old] + [f"{label} -{v}" for v in old if v not in new]
    if isinstance(new, dict) and isinstance(old, dict):
        keys = [k for k in [*old, *[k for k in new if k not in old]] if old.get(k, MISSING) != new.get(k, MISSING)]
        return [f"{label}.{k}" if label != "(file)" else k for k in keys]
    return [label]


def merge(old, new, local, path: str = "") -> tuple[object, list[str], list[str]]:
    """Three-way merge of JSON values: the kit's old seed, its new seed, and the workspace's copy.

    Returns the merged value, the paths the kit changed, and the paths kept because the workspace changed them too.
    A kit change applies where the workspace still has the old value. Objects merge key by key; lists of plain
    values merge as sets, keeping the workspace's order. Without an old seed for a whole file (new in the kit, or
    no base), the old value counts as empty, so the kit's entries are added and the workspace's values are kept.
    Inside a file, an object the old seed lacked merges the same way; any other value the workspace set is kept.
    """
    label = path or "(file)"
    if old is MISSING and local is not MISSING:
        if isinstance(new, dict) and isinstance(local, dict):
            old = {}
        elif not path and isinstance(new, list) and isinstance(local, list):
            old = []
    if new == old or local == new:
        return local, [], []
    if local == old:
        return new, _describe(old, new, label), []
    if isinstance(new, dict) and isinstance(local, dict) and isinstance(old, dict):
        result, applied, kept = {}, [], []
        for key in list(local) + [k for k in new if k not in local]:
            value, a, k = merge(old.get(key, MISSING), new.get(key, MISSING), local.get(key, MISSING),
                                f"{path}.{key}" if path else key)
            if value is not MISSING:
                result[key] = value
            applied += a
            kept += k
        return result, applied, kept
    if (isinstance(new, list) and isinstance(local, list) and isinstance(old, list)
            and all(not isinstance(v, (dict, list)) for v in [*new, *local, *old])):
        added = [v for v in new if v not in old and v not in local]
        removed = [v for v in old if v not in new]
        result = [v for v in local if v not in removed] + added
        changes = [f"{label} +{v}" for v in added] + [f"{label} -{v}" for v in removed if v in local]
        return result, changes, []
    return local, [], [label]
