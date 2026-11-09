#!/usr/bin/env python3
"""Upgrade a vault's shared Obsidian settings to the kit's seeded copies, keeping the workspace's own changes.

The seed's `notebook/.obsidian/` files are copied once; this applies later kit changes to them. For each seeded
settings file it merges three versions: the seed in the scion at a base git ref (the kit version the workspace
had), the seed in the current scion, and the vault's copy. A kit change applies where the vault still has the old
value; where the workspace changed the same setting, its value is kept and reported. Files the vault lacks are
created. It also adds the seed's `.gitignore` exceptions for plugin settings, and installs the pinned community
plugins (docs/obsidian-plugins.json) that the vault enables: each one missing or not matching its pin gets the
release's `main.js`, `manifest.json`, and `styles.css`, and its `data.json` is left alone. A plugin the vault's
`community-plugins.json` does not list is never installed, so removing it there opts the workspace out.

Run it from the workspace root on the upgrade branch, after `just upgrade`, with Obsidian closed:
Obsidian rewrites its settings files while it runs. It refuses to write while Obsidian runs, and reports and exits 0
when there is nothing to write. `--base` defaults to HEAD, which still holds the old scion
until the upgrade is committed; after that, name the commit before it. Without a base seed, the kit's entries are
added and existing values kept. Running it again changes nothing.

The release assets come from the kit's Nix wiring, which fetches each pinned release and checks its hashes; the
tool checks them again before copying. Run outside it (no $OBSIDIAN_PLUGIN_ASSETS), it lists the plugins to
install and installs none. Obsidian still asks once per vault, on each device, to trust its community plugins.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import obsidian_settings as obs


def obsidian_running() -> bool:
    if not shutil.which("pgrep"):
        return False
    return any(subprocess.run(["pgrep", "-x", name], capture_output=True).returncode == 0
               for name in ("Obsidian", "obsidian"))


def gitignore_lines(root: Path, vault: str) -> list[str]:
    """The seed's plugin-settings exceptions, anchored at this workspace's vault folder."""
    lines = []
    for line in obs.SEED_GITIGNORE.read_text().splitlines():
        if line.startswith(f"!{obs.DEFAULT_VAULT}/.obsidian/plugins/"):
            lines.append("!" + vault + line[len(obs.DEFAULT_VAULT) + 1:])
    return lines


def upgrade_gitignore(root: Path, vault: str, dry_run: bool) -> tuple[list[str], list[str]]:
    path = root / ".gitignore"
    if not path.is_file():
        return [], [".gitignore: missing; copy the Obsidian section of the seed's .gitignore"]
    lines = path.read_text().splitlines()
    added, manual = [], []
    for wanted in gitignore_lines(root, vault):
        if wanted in lines:
            continue
        # Insert after the last exception of the same shape: a folder (`…/`) or a file (`…/data.json`).
        is_dir = wanted.endswith("/")
        prefix = f"!{vault}/.obsidian/plugins/"
        anchors = [i for i, line in enumerate(lines) if line.startswith(prefix) and line.endswith("/") == is_dir]
        if not anchors:
            manual.append(f".gitignore: add `{wanted}` to the Obsidian section")
            continue
        lines.insert(anchors[-1] + 1, wanted)
        added.append(wanted)
    if added and not dry_run:
        path.write_text("\n".join(lines) + "\n")
    return added, manual


def install_plugins(settings: Path, enabled: list, assets: Path | None, dry_run: bool,
                    pins: Path = obs.PINS) -> tuple[list[str], list[str]]:
    """Install the pinned plugins the vault enables that are missing or differ from their pin."""
    installed, manual = [], []
    for pin in json.loads(pins.read_text())["plugins"]:
        if pin["id"] not in enabled:
            continue
        folder = settings / "plugins" / pin["id"]
        if all(obs.asset_matches(folder / name, sha) for name, sha in pin["assets"].items()):
            continue
        verb = "update" if (folder / "manifest.json").is_file() else "install"
        line = f"{pin['id']} {pin['version']}"
        if assets is None:
            manual.append(f"plugin {line}: not installed; run upgrade-obsidian from the kit's tools "
                          "(just upgrade-obsidian), which provide the pinned releases")
            continue
        source = assets / pin["id"]
        bad = [name for name, sha in pin["assets"].items() if not obs.asset_matches(source / name, sha)]
        if bad:
            manual.append(f"plugin {line}: {', '.join(bad)} in {source} do not match the pin; not installed")
            continue
        if not dry_run:
            folder.mkdir(parents=True, exist_ok=True)
            for name in pin["assets"]:
                (folder / name).write_bytes((source / name).read_bytes())
        installed.append(f"{verb:8} plugin {line}")
    return installed, manual


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def upgrade(root: Path, base: str | None, dry_run: bool, plugins: bool = True,
            assets: Path | None = None) -> dict:
    settings = obs.settings_dir(root)
    report = {"created": [], "updated": {}, "kept": {}, "unchanged": [], "gitignore": [], "plugins": [],
              "manual": []}
    # The vault's plugin list after the merge, which decides which pinned plugins to install.
    enabled: list = []
    have_base = base is not None and obs.git_ref_exists(root, base)
    if base is not None and not have_base:
        report["manual"].append(f"base {base!r} is not a commit here: merged without an old seed")
    same_base = []
    for name in obs.seeded_files():
        new = json.loads((obs.SEEDED / name).read_text())
        path = settings / name
        if not path.is_file():
            report["created"].append(name)
            if name == "community-plugins.json":
                enabled = new
            if not dry_run:
                write_json(path, new)
            continue
        try:
            local = json.loads(path.read_text())
        except json.JSONDecodeError as error:
            report["manual"].append(f"{name}: not valid JSON ({error}); fix it, then run again")
            continue
        old = obs.base_seed(root, base, name) if have_base else obs.MISSING
        if old == new and local != new:
            same_base.append(name)
        merged, applied, kept = obs.merge(old, new, local)
        if name == "community-plugins.json" and isinstance(merged, list):
            enabled = merged
        if kept:
            report["kept"][name] = kept
        if merged == local:
            if not kept:
                report["unchanged"].append(name)
            continue
        report["updated"][name] = applied
        if not dry_run:
            write_json(path, merged)
    if same_base:
        report["manual"].append(
            f"{', '.join(same_base)}: differ from the kit, but the seed at {base} is the same as the current one, so "
            "nothing was merged. If the upgrade is already committed, run again with --base <the commit before it>; "
            "otherwise the difference is a local choice")
    added, manual = upgrade_gitignore(root, obs.vault_folder(root), dry_run)
    report["gitignore"], report["manual"] = added, report["manual"] + manual
    if plugins:
        installed, manual = install_plugins(settings, enabled, assets, dry_run)
        report["plugins"], report["manual"] = installed, report["manual"] + manual
    stale = obs.stale_root_settings(root)
    if stale:
        report["manual"].append(
            f"{stale.relative_to(root)}/ exists at the repository root: Obsidian has opened the root as a vault. "
            f"Open {obs.vault_folder(root)}/ instead (Open folder as vault), remove the old vault from Obsidian's "
            f"list, then delete {stale.relative_to(root)}/")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base", default="HEAD", help="git ref whose scion holds the old seed (default: HEAD)")
    parser.add_argument("--dry-run", action="store_true", help="report what would change; write nothing")
    parser.add_argument("--allow-running", action="store_true", help="write even if Obsidian is running")
    parser.add_argument("--no-plugins", action="store_true", help="merge settings only; install no plugins")
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / obs.vault_folder(root)).is_dir():
        sys.exit(f"upgrade-obsidian: no {obs.vault_folder(root)}/ here; run from the workspace root")
    options = {"plugins": not args.no_plugins, "assets": obs.plugin_assets()}
    # Plan first: a running Obsidian matters only if something would be written (settings, .gitignore, plugins).
    report = upgrade(root, args.base, dry_run=True, **options)
    pending = report["created"] or report["updated"] or report["gitignore"] or report["plugins"]
    if pending and not args.dry_run:
        if not args.allow_running and obsidian_running():
            sys.exit("upgrade-obsidian: Obsidian is running and rewrites its settings; quit it (or --dry-run, "
                     "or --allow-running if no vault of this workspace is open)")
        report = upgrade(root, args.base, dry_run=False, **options)
    verb = "would " if args.dry_run else ""
    for name in report["created"]:
        print(f"{verb}create   {name}")
    for name, paths in report["updated"].items():
        print(f"{verb}update   {name}: " + ", ".join(paths))
    for name, paths in report["kept"].items():
        print(f"kept       {name}: local value for " + ", ".join(paths))
    for line in report["gitignore"]:
        print(f"{verb}add      .gitignore: {line}")
    for line in report["plugins"]:
        print(f"{verb}{line}")
    for name in report["unchanged"]:
        print(f"same       {name}")
    for line in report["manual"]:
        print(f"by hand: {line}")
    if report["plugins"] and not args.dry_run:
        print("Obsidian loads plugins when it opens the vault; it asks once per vault, on each device, to trust them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
