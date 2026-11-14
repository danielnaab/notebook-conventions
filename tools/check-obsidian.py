#!/usr/bin/env python3
"""Report how a workspace's shared Obsidian settings differ from the kit's seeded copies.

The seed's `notebook/.obsidian/` files are copied once; `upgrade-obsidian` applies later kit changes to them.
This read-only check compares each seeded settings file with the vault's copy as JSON (Obsidian rewrites
formatting) and lists it as same, changed, or missing. A workspace declares its deliberate deviations in
`obsidian` in its notebook-kit.yaml: the check compares against the seed with those applied, marks
a file that carries them `(declared: ...)`, and checks the identity snippet they render. Changed is not an error: a
workspace may adapt a setting without declaring it. It also lists each pinned community plugin's installed state from
docs/obsidian-plugins.json; `upgrade-obsidian` installs them, and their state never affects the exit code.
It warns when a `.obsidian/` at the repository root shows Obsidian has the old vault open.
Use --strict to exit 1 on missing or changed settings files, or that stale folder.
"""

import argparse
import json
import sys
from pathlib import Path

import obsidian_settings as obs
from obsidian_settings import PINS, SEEDED, vault_folder


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


def compare_settings(root: Path, seeded: Path = SEEDED, config: dict | None = None) -> list[tuple[str, str, str]]:
    vault = root / vault_folder(root) / ".obsidian"
    declared = obs.declared_settings(obs.workspace_config(root) if config is None else config)
    result = []
    for name in sorted({*obs.seeded_files(seeded), *declared}):
        local = vault / name
        if not local.is_file():
            result.append((name, "missing", ""))
            continue
        try:
            kit_value = json.loads((seeded / name).read_text()) if (seeded / name).is_file() else {}
            local_value = json.loads(local.read_text())
        except json.JSONDecodeError as error:
            result.append((name, "invalid", str(error)))
            continue
        if name in declared:
            kit_value = obs.overlay(kit_value, declared[name])
        note = f"declared: {', '.join(sorted(declared[name]))}" if name in declared else ""
        if kit_value == local_value:
            result.append((name, "same", note))
        else:
            result.append((name, "changed", "; ".join(filter(None, [describe(kit_value, local_value), note]))))
    return result


def identity_state(root: Path, config: dict | None = None) -> tuple[str, str] | None:
    """The identity snippet's state, or None when the workspace declares no identity and none was rendered."""
    css = obs.identity_css(obs.workspace_config(root) if config is None else config)
    path = root / vault_folder(root) / ".obsidian/snippets" / f"{obs.IDENTITY_SNIPPET}.css"
    name = f"snippets/{obs.IDENTITY_SNIPPET}.css"
    if css is None:
        return (name, "stale") if path.is_file() else None
    if not path.is_file():
        return name, "missing"
    return name, "same" if path.read_text() == css else "changed"


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
        if obs.asset_matches(folder / "main.js", pin["assets"]["main.js"]):
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
    try:
        config = obs.workspace_config(root)
    except (OSError, ValueError) as error:
        sys.exit(f"check-obsidian: {error}")
    settings = compare_settings(root, config=config)
    identity = identity_state(root, config)
    print(f"settings (kit seed + workspace declarations vs {vault_folder(root)}/.obsidian):")
    for name, state, detail in settings:
        print(f"  {state:8} {name}" + (f"  ({detail})" if detail else ""))
    if identity:
        name, state = identity
        hint = {"missing": "run just upgrade-obsidian", "changed": "run just upgrade-obsidian",
                "stale": "no identity declared; just upgrade-obsidian removes it"}.get(state)
        print(f"  {state:8} {name}" + (f"  ({hint})" if hint else ""))
    print("plugins (docs/obsidian-plugins.json):")
    for plugin, state in plugin_states(root):
        print(f"  {plugin}: {state}")
    stale = obs.stale_root_settings(root)
    if stale:
        print(f"stale: {stale.relative_to(root)}/ at the repository root: Obsidian has opened the root as a vault, "
              f"with default settings. Open {vault_folder(root)}/ as the vault, remove the old one from Obsidian's "
              f"list, then delete {stale.relative_to(root)}/.")
    if args.strict and (stale or any(state != "same" for _, state, _ in settings)
                        or (identity and identity[1] != "same")):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
