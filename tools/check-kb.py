#!/usr/bin/env python3
"""Run knowledge-base-integrity's link validator and KB linter on this repository.

The tools come from the pinned flake input (KBI_SRC points at its src/); scopes and rules
come from knowledge-base.yaml (rules.checks). Exit 0 clean, 1 findings, 2 configuration error.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

TOOLS = ("link_validator", "kb_linter")


def run_tool(module: str, src: str, root: Path) -> tuple[int, list[str], str]:
    env = {**os.environ, "PYTHONPATH": src, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run(
        [sys.executable, "-m", module, str(root)], capture_output=True, text=True, env=env
    )
    if proc.returncode == 2:
        return 2, [], proc.stderr.strip() or f"{module}: configuration error"
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return 2, [], f"{module}: unexpected output: {proc.stderr.strip() or proc.stdout[:200]}"
    lines = []
    for v in report["violations"]:
        detail = v.get("target") or v.get("message", "")
        lines.append(f"{module}: {v['rule']}: {v['file']}: {detail}")
    return proc.returncode, lines, json.dumps(report["summary"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", type=Path)
    parser.add_argument("--src", default=os.environ.get("KBI_SRC"), help="knowledge-base-integrity src/")
    args = parser.parse_args()
    if not args.src:
        print("check-kb: set KBI_SRC or pass --src (use `nix run .#check-kb`)", file=sys.stderr)
        return 2

    status = 0
    for module in TOOLS:
        code, lines, summary = run_tool(module, args.src, args.root)
        if code == 2:
            print(f"check-kb: {summary}", file=sys.stderr)
            return 2
        print(f"{module}: {summary}")
        for line in lines:
            print(f"  {line}")
        status = max(status, code)
    return status


if __name__ == "__main__":
    sys.exit(main())
