"""Shared helpers for a vault's Obsidian settings: where they live, the kit's seeded copies, and a three-way merge."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml

KIT = Path(__file__).resolve().parents[1]
SEEDED = KIT / "seed/common/notebook/.obsidian"
SEED_GITIGNORE = KIT / "seed/common/.gitignore"
PINS = KIT / "docs/obsidian-plugins.json"
DEFAULT_VAULT = "notebook"
# Where earlier kit versions kept the seeded settings inside the scion: v0.2 and later, then v0.1.
SCION_SEED_PATHS = (".scions/notebook-conventions/seed/common/notebook/.obsidian",
                    ".scions/notebook-conventions/seed/common/.obsidian")


class Missing:
    """A key or file that is absent, distinct from a JSON null."""

    def __repr__(self) -> str:
        return "absent"


MISSING = Missing()


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
