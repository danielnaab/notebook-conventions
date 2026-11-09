#!/usr/bin/env python3
"""Upgrade a vault's shared Obsidian settings to the kit's seeded copies, keeping the workspace's own changes.

The seed's `notebook/.obsidian/` files are copied once; this applies later kit changes to them. For each seeded
settings file it merges three versions: the seed in the scion at a base git ref (the kit version the workspace
had), the seed in the current scion, and the vault's copy. A kit change applies where the vault still has the old
value; where the workspace changed the same setting, its value is kept and reported. Files the vault lacks are
created. It also adds the seed's `.gitignore` exceptions for plugin settings.

Run it from the workspace root on the upgrade branch, after `just upgrade`, with Obsidian closed:
Obsidian rewrites its settings files while it runs. It refuses to write while Obsidian runs, and reports and exits 0
when there is nothing to write. `--base` defaults to HEAD, which still holds the old scion
until the upgrade is committed; after that, name the commit before it. Without a base seed, the kit's entries are
added and existing values kept. Running it again changes nothing. It does not install plugins.
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


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def upgrade(root: Path, base: str | None, dry_run: bool) -> dict:
    settings = obs.settings_dir(root)
    report = {"created": [], "updated": {}, "kept": {}, "unchanged": [], "gitignore": [], "manual": []}
    have_base = base is not None and obs.git_ref_exists(root, base)
    if base is not None and not have_base:
        report["manual"].append(f"base {base!r} is not a commit here: merged without an old seed")
    same_base = []
    for name in obs.seeded_files():
        new = json.loads((obs.SEEDED / name).read_text())
        path = settings / name
        if not path.is_file():
            report["created"].append(name)
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
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / obs.vault_folder(root)).is_dir():
        sys.exit(f"upgrade-obsidian: no {obs.vault_folder(root)}/ here; run from the workspace root")
    # Plan first: a running Obsidian matters only if something would be written.
    report = upgrade(root, args.base, dry_run=True)
    pending = report["created"] or report["updated"] or report["gitignore"]
    if pending and not args.dry_run:
        if not args.allow_running and obsidian_running():
            sys.exit("upgrade-obsidian: Obsidian is running and rewrites its settings; quit it (or --dry-run, "
                     "or --allow-running if no vault of this workspace is open)")
        report = upgrade(root, args.base, dry_run=False)
    verb = "would " if args.dry_run else ""
    for name in report["created"]:
        print(f"{verb}create   {name}")
    for name, paths in report["updated"].items():
        print(f"{verb}update   {name}: " + ", ".join(paths))
    for name, paths in report["kept"].items():
        print(f"kept       {name}: local value for " + ", ".join(paths))
    for line in report["gitignore"]:
        print(f"{verb}add      .gitignore: {line}")
    for name in report["unchanged"]:
        print(f"same       {name}")
    for line in report["manual"]:
        print(f"by hand: {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
