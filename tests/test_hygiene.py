"""The kit is public and generic: no agency, employer, machine, or person-specific context."""

import re
import subprocess
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".scions", ".direnv"}
SELF = {"tests/test_hygiene.py"}
DENY = [
    r"\bGSA\b", r"\bTTS\b", r"\bGFE\b", r"\bFlexion\b", r"cloud\.gov", r"\bUSAi\b", r"tts-assistant",
    r"gsa-notebook", r"/Users/", r"/home/\w+", r"\bDan\b", r"\bDaniel\b", r"homelab", r"\bforgejo\b.*\.(?:com|net)",
]


def tracked_text_files():
    names = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=KIT, capture_output=True,
                           text=True).stdout.split("\n")
    for name in filter(None, names):
        path = KIT / name
        if SKIP_PARTS & set(path.relative_to(KIT).parts) or name in SELF or not path.is_file():
            continue
        try:
            yield name, path.read_text()
        except UnicodeDecodeError:
            continue


class HygieneTest(unittest.TestCase):
    def test_no_context_specific_terms(self):
        hits = []
        for name, text in tracked_text_files():
            for pattern in DENY:
                for match in re.finditer(pattern, text, re.I if pattern.islower() else 0):
                    hits.append(f"{name}: {match.group(0)}")
        self.assertEqual([], hits)


if __name__ == "__main__":
    unittest.main()
