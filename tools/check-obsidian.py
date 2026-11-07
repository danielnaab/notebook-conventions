#!/usr/bin/env python3
"""Report how a workspace's shared Obsidian settings differ from the kit's seeded copies.

The seed's `notebook/.obsidian/` files are copied once, so later kit changes reach a workspace only when it
copies them again. This read-only check compares each seeded settings file with the vault's copy as JSON
(Obsidian rewrites formatting) and lists it as same, changed, or missing. Changed is not an error: a
workspace may adapt a setting. It also lists each pinned community plugin's installed state from
docs/obsidian-plugins.json; installation is per machine and never affects the exit code.
Use --strict to exit 1 on missing or changed settings files.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

KIT = Path(__file__).resolve().parents[1]
SEEDED = KIT / "seed/common/notebook/.obsidian"
PINS = KIT / "docs/obsidian-plugins.json"
DEFAULT_VAULT = "notebook"
# Obsidian's in-app installer appends this to main.js; the pinned hashes are of the release assets.
INSTALLER_SUFFIX = b"\n/* nosourcemap */"


def vault_folder(root: Path) -> str:
    config = root / "knowledge-base.yaml"
    if config.is_file():
        data = yaml.safe_load(config.read_text()) or {}
        value = (data.get("paths") or {}).get("vault")
        if isinstance(value, str) and value.strip("/"):
            return value.strip("/")
    return DEFAULT_VAULT


def describe(kit_value, local_value) -> str:
    """A short note on what differs: top-level keys for objects, added and removed items for lists."""
    if isinstance(kit_value, dict) and isinstance(local_value, dict):
        keys = sorted(k for k in kit_value.keys() | local_value.keys() if kit_value.get(k) != local_value.get(k))
        return "keys: " + ", ".join(keys)
    if isinstance(kit_value, list) and isinstance(local_value, list):
        added = [str(v) for v in local_value if v not in kit_value]
        removed = [str(v) for v in kit_value if v not in local_value]
        parts = [f"+{v}" for v in added] + [f"-{v}" for v in removed]
        return " ".join(parts) if parts else "order"
    return "value"


def compare_settings(root: Path, seeded: Path = SEEDED) -> list[tuple[str, str, str]]:
    vault = root / vault_folder(root) / ".obsidian"
    result = []
    for kit_file in sorted(p for p in seeded.rglob("*.json") if p.is_file()):
        name = kit_file.relative_to(seeded).as_posix()
        local = vault / name
        if not local.is_file():
            result.append((name, "missing", ""))
            continue
        try:
            kit_value, local_value = json.loads(kit_file.read_text()), json.loads(local.read_text())
        except json.JSONDecodeError as error:
            result.append((name, "invalid", str(error)))
            continue
        if kit_value == local_value:
            result.append((name, "same", ""))
        else:
            result.append((name, "changed", describe(kit_value, local_value)))
    return result


def plugin_states(root: Path, pins: Path = PINS) -> list[tuple[str, str]]:
    plugins = root / vault_folder(root) / ".obsidian/plugins"
    result = []
    for pin in json.loads(pins.read_text())["plugins"]:
        folder = plugins / pin["id"]
        manifest = folder / "manifest.json"
        if not manifest.is_file():
            result.append((pin["id"], f"not installed (pinned {pin['version']})"))
            continue
        version = json.loads(manifest.read_text()).get("version")
        if version != pin["version"]:
            result.append((pin["id"], f"installed {version}, pinned {pin['version']}"))
            continue
        main = folder / "main.js"
        data = main.read_bytes() if main.is_file() else b""
        if data.endswith(INSTALLER_SUFFIX):
            data = data[: -len(INSTALLER_SUFFIX)]
        if hashlib.sha256(data).hexdigest() == pin["assets"]["main.js"]:
            result.append((pin["id"], f"installed {version}, matches the pinned release"))
        else:
            result.append((pin["id"], f"installed {version}, main.js differs from the pinned release"))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    settings = compare_settings(root)
    print(f"settings (kit seed vs {vault_folder(root)}/.obsidian):")
    for name, state, detail in settings:
        print(f"  {state:8} {name}" + (f"  ({detail})" if detail else ""))
    print("plugins (docs/obsidian-plugins.json):")
    for plugin, state in plugin_states(root):
        print(f"  {plugin}: {state}")
    if args.strict and any(state != "same" for _, state, _ in settings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
