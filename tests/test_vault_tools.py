"""Tests for the vault tools: index generation, moving notes, and converting a v0.1 workspace.

Fixtures are synthetic. The bundle and .okfignore come from knowledge-base-kit's checker (KBI_SRC; skipped if unset).
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "tools"))

import vault  # noqa: E402

KB_YAML = 'rules:\n  checks:\n    okf:\n      bundle: notebook\n      version: "0.2"\n'


@unittest.skipUnless(os.environ.get("KBI_SRC"), "KBI_SRC not set")
class VaultTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "knowledge-base.yaml").write_text(KB_YAML)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def read(self, rel):
        return (self.root / rel).read_text()

    def tool(self, name, *args):
        return subprocess.run([sys.executable, str(KIT / "tools" / name), "--root", str(self.root), *args],
                              capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


class IndexTest(VaultTestCase):
    def test_folder_indexes_from_frontmatter(self):
        self.write("notebook/.okfignore", "templates/\n")
        self.write("notebook/templates/daily.md", "# {{date}}\n")
        self.write("notebook/.obsidian/x.md", "x\n")
        self.write("notebook/wiki/b.md", "---\ntype: Topic\ntitle: Bee [notes]\ndescription: About\n  bees.\n---\n")
        self.write("notebook/wiki/a.md", "---\ntype: Topic\n---\n# Ants\n")
        self.write("notebook/records/daily/2026-11/2026-11-05.md", "---\ntype: Daily Note\n---\n")
        self.write("notebook/records/daily/2026-11/2026-11-06.md", "---\ntype: Daily Note\n---\n")
        self.write("notebook/records/sessions/2026-11/2026-11-06-x/tool.py", "print()\n")
        indexes = vault.expected_indexes(self.root)
        self.assertEqual(
            sorted(indexes),
            ["notebook/index.md", "notebook/records/daily/2026-11/index.md", "notebook/records/daily/index.md",
             "notebook/records/index.md", "notebook/wiki/index.md"],
        )
        self.assertTrue(indexes["notebook/index.md"].startswith('---\nokf_version: "0.2"\n---\n\n# Notebook\n'))
        self.assertIn("* [records](records/) - Dated notes, written once", indexes["notebook/index.md"])
        self.assertNotIn("templates", indexes["notebook/index.md"])
        self.assertEqual(
            "# Wiki\n\n## Notes\n\n* [Ants](a.md)\n* [Bee (notes)](b.md) - About bees.\n",
            indexes["notebook/wiki/index.md"],
        )
        daily = indexes["notebook/records/daily/2026-11/index.md"]
        self.assertLess(daily.index("2026-11-06"), daily.index("2026-11-05"), "dated notes newest first")

    def test_names_with_spaces_are_encoded(self):
        self.write("notebook/wiki/people/Pat Lee.md", "---\ntype: Person\ntitle: Pat Lee\n---\n")
        self.assertIn("* [Pat Lee](Pat%20Lee.md)", vault.expected_indexes(self.root)["notebook/wiki/people/index.md"])

    def test_check_and_write(self):
        self.write("notebook/wiki/a.md", "---\ntype: Topic\n---\n")
        proc = self.tool("index.py", "--check")
        self.assertEqual(1, proc.returncode, proc.stdout)
        self.assertEqual(0, self.tool("index.py").returncode)
        self.assertEqual(0, self.tool("index.py", "--check").returncode)

    def test_generated_indexes_pass_the_okf_checks(self):
        kbi = os.environ["KBI_SRC"]
        self.write("notebook/wiki/a.md", "---\ntype: Topic\ndescription: A topic.\n---\n")
        self.write("notebook/tasks/2026-11/t.md", "---\ntype: Task\nstatus: ready\n---\n# T\n")
        self.tool("index.py")
        for module in ("kb_linter", "link_validator"):
            proc = subprocess.run([sys.executable, "-m", module, str(self.root)], capture_output=True, text=True,
                                  env={**os.environ, "PYTHONPATH": kbi})
            self.assertEqual([], json.loads(proc.stdout)["violations"], module)


class MoveTest(VaultTestCase):
    def setUp(self):
        super().setUp()
        self.write("notebook/wiki/people/Pat Lee.md", "---\ntype: Person\n---\nSee [the plan](../plan.md#next-steps).\n")
        self.write("notebook/wiki/plan.md", "## Next steps\n[Pat](people/Pat%20Lee.md) and [Pat](<people/Pat Lee.md> \"t\")\n"
                   "and [rooted](/wiki/people/Pat%20Lee.md) and `wiki/people/Pat Lee.md` and\n"
                   "```\n[code](people/Pat%20Lee.md)\n```\n")
        self.write("README.md", "[Pat](notebook/wiki/people/Pat%20Lee.md) [web](https://x.test/people/Pat%20Lee.md)\n")

    def test_move_a_note(self):
        proc = self.tool("move.py", "notebook/wiki/people/Pat Lee.md", "notebook/wiki/people/pat-lee.md")
        self.assertEqual(0, proc.returncode, proc.stderr)
        plan = self.read("notebook/wiki/plan.md")
        self.assertIn("[Pat](people/pat-lee.md) and [Pat](<people/pat-lee.md> \"t\")", plan)
        self.assertIn("[rooted](/wiki/people/pat-lee.md)", plan)
        self.assertIn("[code](people/Pat%20Lee.md)", plan, "links in code are not touched")
        self.assertIn("[Pat](notebook/wiki/people/pat-lee.md) [web](https://x.test/people/Pat%20Lee.md)",
                      self.read("README.md"))
        self.assertIn("mentions", proc.stdout)

    def test_move_a_folder_rewrites_links_out_of_it(self):
        self.tool("move.py", "notebook/wiki/people", "notebook/people")
        self.assertIn("[the plan](../wiki/plan.md#next-steps)", self.read("notebook/people/Pat Lee.md"))
        self.assertIn("[Pat](../people/Pat%20Lee.md)", self.read("notebook/wiki/plan.md"))

    def test_dry_run_and_refusals(self):
        proc = self.tool("move.py", "--dry-run", "notebook/wiki/plan.md", "notebook/plan.md")
        self.assertIn("Would move", proc.stdout)
        self.assertTrue((self.root / "notebook/wiki/plan.md").exists())
        self.assertNotEqual(0, self.tool("move.py", "notebook/missing.md", "notebook/x.md").returncode)
        self.assertNotEqual(0, self.tool("move.py", "notebook/wiki", "notebook/wiki/sub").returncode)
        self.assertNotEqual(0, self.tool("move.py", "README.md", "notebook/wiki/plan.md").returncode)


class ConvertTest(VaultTestCase):
    """A v0.1 workspace: notebook/{daily,sessions,tasks,wiki,raw} with READMEs, .obsidian/ at the root."""

    def setUp(self):
        super().setUp()
        seed_readme = KIT / "tests/fixtures/v0.1-daily-README.md"
        self.write("notebook/daily/README.md", seed_readme.read_text())
        self.write("notebook/daily/2026-11/2026-11-06.md", "Daily note.\n\n- [Session](../../sessions/2026-11/2026-11-06-x/README.md)\n")
        self.write("notebook/sessions/README.md", "# Agent sessions\n\nLocal list.\n")
        self.write("notebook/sessions/2026-11/2026-11-06-x/README.md",
                   "# X\n\n[Tool](tool.py) [Task](../../../tasks/2026-11/t.md)\n")
        self.write("notebook/sessions/2026-11/2026-11-06-x/tool.py", "print()\n")
        self.write("notebook/tasks/README.md", "---\nstatus: living\n---\n\n# Tasks\n\n## Ready\n\n- [T](2026-11/t.md)\n")
        self.write("notebook/tasks/2026-11/t.md", "---\nstatus: ready\n---\n\n# T\n")
        self.write("notebook/wiki/topic.md", "---\nstatus: draft\n---\n\n# Topic\n")
        self.write("notebook/templates/daily.md", (KIT / "tests/fixtures/v0.1-daily-template.md").read_text())
        self.write(".obsidian/daily-notes.json", json.dumps({"folder": "notebook/daily", "template": "notebook/templates/daily"}))
        self.write(".obsidian/templates.json", json.dumps({"folder": "notebook/templates"}))
        self.write(".gitignore", ".obsidian/workspace*.json\n!.obsidian/plugins/calendar/\n.trash/\n")
        self.write("AGENTS.md", "[Tasks](notebook/tasks/README.md)\n")

    def test_convert(self):
        proc = self.tool("convert.py")
        self.assertEqual(0, proc.returncode, proc.stderr)
        session = "notebook/records/sessions/2026-11/2026-11-06-x.md"
        self.assertIn("[Tool](2026-11-06-x/tool.py) [Task](../../../tasks/2026-11/t.md)", self.read(session))
        self.assertTrue(self.read(session).startswith("---\ntype: Session\n---\n"))
        self.assertTrue((self.root / "notebook/records/sessions/2026-11/2026-11-06-x/tool.py").is_file())
        self.assertIn("(../../sessions/2026-11/2026-11-06-x.md)", self.read("notebook/records/daily/2026-11/2026-11-06.md"))
        self.assertEqual("[Tasks](notebook/tasks/index.md)\n", self.read("AGENTS.md"))
        self.assertTrue(self.read("notebook/tasks/2026-11/t.md").startswith("---\ntype: Task\nstatus: ready\n"))
        self.assertIn("type: Topic", self.read("notebook/wiki/topic.md"))
        self.assertEqual(self.read("notebook/templates/daily.md"), (KIT / "templates/daily.md").read_text())
        self.assertEqual("templates/", self.read("notebook/.okfignore").strip().splitlines()[-1])
        daily = json.loads(self.read("notebook/.obsidian/daily-notes.json"))
        self.assertEqual({"folder": "records/daily", "template": "templates/daily"}, daily)
        self.assertEqual({"folder": "templates"}, json.loads(self.read("notebook/.obsidian/templates.json")))
        self.assertEqual("notebook/.obsidian/workspace*.json\n!notebook/.obsidian/plugins/calendar/\n.trash/\n",
                         self.read(".gitignore"))
        self.assertFalse(any(self.root.glob("notebook/**/README.md")), "seeded READMEs become indexes")
        self.assertIn("by hand: notebook/records/sessions/README.md had local prose", proc.stdout)
        self.assertNotIn("by hand: notebook/records/daily/README.md", proc.stdout, "unchanged seed READMEs go silently")
        self.assertIn("add a one-line `description`", proc.stdout)
        self.assertEqual(0, self.tool("index.py", "--check").returncode)
        again = self.tool("convert.py")
        self.assertIn("Converted: 0 steps done", again.stdout)


if __name__ == "__main__":
    unittest.main()


class ReviewRegressionTest(VaultTestCase):
    """Cases from the 2026-11-06 review of the vault tools."""

    def test_link_forms_the_scanner_must_find(self):
        text = ("A [long link\ntext](b.md), [in [x]](b.md), [![img](i.png)](b.md), [p](p(1).md)\n"
                "[ref]: b.md\n  [r2]: <b.md> \"T\"\n`[code](b.md)`\n    \n")
        self.assertEqual(["b.md", "b.md", "i.png", "b.md", "p(1).md", "b.md", "<b.md>"],
                         [link.destination for link in vault.links(text)])

    def test_move_rewrites_every_link_form(self):
        self.write("notebook/wiki/b.md", "# B\n")
        self.write("notebook/wiki/p(1).md", "# P\n")
        self.write("notebook/wiki/a.md", "[long\ntext](b.md) [![i](i.png)](b.md) [p](p(1).md)\n[ref]: b.md\n")
        self.tool("move.py", "notebook/wiki/b.md", "notebook/wiki/sub/b.md")
        self.tool("move.py", "notebook/wiki/p(1).md", "notebook/wiki/sub/p(1).md")
        self.assertEqual("[long\ntext](sub/b.md) [![i](i.png)](sub/b.md) [p](sub/p%281%29.md)\n[ref]: sub/b.md\n",
                         self.read("notebook/wiki/a.md"))

    def test_rooted_links_outside_the_bundle_are_left_alone(self):
        self.write("notebook/wiki/b.md", "# B\n")
        self.write("README.md", "[b](/wiki/b.md)\n")
        self.tool("move.py", "notebook/wiki/b.md", "notebook/wiki/c.md")
        self.assertEqual("[b](/wiki/b.md)\n", self.read("README.md"))

    def test_index_entries_encode_parentheses(self):
        self.write("notebook/wiki/Untitled (1).md", "---\ntype: Topic\ntitle: x\\\n---\n")
        self.assertIn("* [x](Untitled%20%281%29.md)", vault.expected_indexes(self.root)["notebook/wiki/index.md"])

    def test_tasks_outside_the_bundle_get_an_index(self):
        (self.root / "knowledge-base.yaml").write_text(KB_YAML + "    tasks:\n      path: work/tasks\n")
        self.write("notebook/wiki/a.md", "---\ntype: Topic\n---\n")
        self.write("work/tasks/2026-11/t.md", "---\nstatus: ready\n---\n# T\n")
        self.assertIn("work/tasks/index.md", vault.expected_indexes(self.root))

    def test_convert_keeps_folder_notes_and_hand_written_indexes(self):
        self.write("notebook/wiki/README.md", (KIT / "tests/fixtures/v0.1-wiki-README.md").read_text())
        self.write("notebook/wiki/kafka/README.md", "---\nstatus: stable\n---\n# Kafka\n\nProse.\n")
        self.write("notebook/wiki/index.md", "# Hand-written map\n\n[Kafka](kafka/README.md)\n")
        self.write(".gitignore", "/.obsidian/workspace.json\n")
        proc = self.tool("convert.py")
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertIn("Prose.", self.read("notebook/wiki/kafka/README.md"))
        self.assertIn("# Hand-written map", self.read("notebook/wiki/map.md"))
        self.assertIn("now map.md", proc.stdout)
        self.assertIn("a note named README.md", proc.stdout)
        self.assertNotIn("wiki/README.md had local prose", proc.stdout)
        self.assertIn("* [Hand-written map](map.md)", self.read("notebook/wiki/index.md"))
        self.assertEqual("/notebook/.obsidian/workspace.json\n", self.read(".gitignore"))
