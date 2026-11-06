"""Regression tests for the read-only task checker; fixtures contain no real work data."""
from datetime import date
import importlib.util
from pathlib import Path
import tempfile
import unittest

import yaml

spec = importlib.util.spec_from_file_location("check_tasks", Path(__file__).resolve().parents[1] / "tools/check-tasks.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class TasksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.folder = self.root / "notebook/tasks"
        (self.folder / "2026-11").mkdir(parents=True)
        self.meta = {
            "status": "waiting", "created": date(2026, 11, 4), "updated": "2026-11-04",
            "owner": "assistant", "project": "workspace", "contexts": ["notebook"],
        }
        self.body = """# Example task

## Goal
Preserve a useful outcome.

## Next action
Wait for the handoff.

## Waiting on
A specified writer's completion evidence.

## Resurface when
The handoff arrives during an interaction.

## Done when
The outcome is verified within authorization.

## Sources
[Task index](../README.md)
"""
        self.write()
        self.index()

    def write(self, name="example.md", meta=None, body=None):
        path = self.folder / "2026-11" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name.endswith("/README.md") and body is None:
            body = self.body.replace("../README.md", "../../README.md")
        path.write_text("---\n" + yaml.safe_dump(self.meta if meta is None else meta) + "---\n\n" + (self.body if body is None else body))
        return path

    def index(self, text="## Waiting\n\n- [Example](2026-11/example.md).\n"):
        (self.folder / "README.md").write_text("---\nstatus: living\n---\n\n# Tasks\n\n" + text)

    def errors(self):
        return checker.validate(self.root)

    def assert_error(self, text):
        self.assertTrue(any(text in error for error in self.errors()), self.errors())

    def test_valid_waiting_record(self):
        self.assertEqual([], self.errors())

    def test_nested_layout_is_required(self):
        self.assertEqual([], self.errors())
        self.folder.rename(self.root / "tasks")
        self.assertEqual(["notebook/tasks: missing directory or symlink"], self.errors())

    def test_notebook_symlink_is_rejected(self):
        outside = self.root / "outside-notebook"
        (self.root / "notebook").rename(outside)
        (self.root / "notebook").symlink_to(outside, target_is_directory=True)
        self.assertEqual(["notebook/tasks: missing directory or symlink"], self.errors())

    def test_required_fields(self):
        for field in checker.REQUIRED:
            with self.subTest(field=field):
                meta = dict(self.meta)
                del meta[field]
                self.write(meta=meta)
                self.assert_error("missing required field " + field)

    def test_invalid_status_types_do_not_crash(self):
        for status in ["draft", ["waiting"], {"state": "waiting"}, None]:
            with self.subTest(status=status):
                self.write(meta={**self.meta, "status": status})
                self.assert_error("invalid status")

    def test_creation_month_and_date_format(self):
        self.write(meta={**self.meta, "created": "2026-10-31"})
        self.assert_error("creation month")
        for value in ["2026-11-99", "2026-1-4", 20261104, "2026-11-04T12:00:00"]:
            with self.subTest(value=value):
                self.write(meta={**self.meta, "created": value})
                self.assert_error("YYYY-MM-DD")

    def test_updated_must_not_precede_created(self):
        self.write(meta={**self.meta, "updated": "2026-11-03"})
        self.assert_error("updated precedes")

    def test_optional_metadata_types(self):
        for field, value in [("contexts", "notebook"), ("blocked_by", [False]), ("priority", "urgent"), ("due", "tomorrow"), ("review_on", False)]:
            with self.subTest(field=field):
                self.write(meta={**self.meta, field: value})
                self.assertTrue(self.errors())

    def test_completed_record_requires_date_and_outcome(self):
        self.index("## Recently completed\n\n- [Example](2026-11/example.md).\n")
        self.write(meta={**self.meta, "status": "completed"})
        self.assert_error("completion date")
        self.assert_error("section Outcome")
        self.write(meta={**self.meta, "status": "completed", "completed": "2026-11-04"}, body=self.body + "\n## Outcome\nVerified. See the sources.\n")
        self.assertEqual([], self.errors())
        self.index("## Ready\n\n_None._\n")
        self.assertEqual([], self.errors(), "Closed record should survive removal from active index")

    def test_completion_chronology(self):
        self.index("## Recently completed\n\n- [Example](2026-11/example.md).\n")
        for value in ["2026-11-03", "2026-11-05"]:
            self.write(meta={**self.meta, "status": "completed", "completed": value}, body=self.body + "\n## Outcome\nVerified.\n")
            self.assertTrue(self.errors())
        self.index()
        self.write(meta={**self.meta, "completed": "2026-11-04"})
        self.assert_error("only valid for completed")

    def test_canceled_is_not_completed(self):
        self.index("## Ready\n\n_None._\n")
        self.write(meta={**self.meta, "status": "canceled"})
        self.assert_error("section Outcome")
        self.write(meta={**self.meta, "status": "canceled"}, body=self.body + "\n## Outcome\nCanceled because the goal is no longer needed.\n")
        self.assertEqual([], self.errors())

    def test_waiting_reason_and_filled_sections(self):
        self.write(body=self.body.replace("A specified writer's completion evidence.", "<!-- Fill in later. -->"))
        self.assert_error("section Waiting on")
        self.write(body=self.body.replace("The handoff arrives during an interaction.", ""))
        self.assert_error("section Resurface when")

    def test_placeholders_and_links(self):
        self.write(body=self.body + "\n{{title}}\n")
        self.assert_error("unresolved template")
        self.write(body=self.body.replace("../README.md", "missing.md"))
        self.assert_error("missing local navigation")
        self.write(body=self.body.replace("[Task index](../README.md)", "No source yet."))
        self.assert_error("Sources requires")

    def test_duplicate_yaml_and_index_state(self):
        path = self.folder / "2026-11/example.md"
        path.write_text(path.read_text().replace("status: waiting", "status: waiting\nstatus: ready"))
        self.assert_error("duplicate metadata")
        self.write()
        self.index("## Ready\n\n- [Example](2026-11/example.md).\n")
        self.assert_error("index section")

    def test_active_index_coverage_and_duplicates(self):
        self.index("## Waiting\n\n_None._\n")
        self.assert_error("missing from index")
        self.index("## Waiting\n\n- [Example](2026-11/example.md).\n- [Again](2026-11/example.md).\n")
        self.assert_error("duplicate task link")

    def test_dependencies_and_cycles(self):
        for value in ["notebook/tasks/2026-11/missing.md", "notebook/tasks/2026-11/example.md", "tasks/2026-11/other.md", "../outside.md"]:
            self.write(meta={**self.meta, "blocked_by": [value]})
            self.assert_error("another existing task identifier")
        self.write(meta={**self.meta, "blocked_by": ["notebook/tasks/2026-11/other.md"]})
        self.write("other.md", meta={**self.meta, "blocked_by": ["notebook/tasks/2026-11/example.md"]})
        self.index("## Waiting\n\n- [One](2026-11/example.md).\n- [Two](2026-11/other.md).\n")
        self.assert_error("dependency cycle")
        self.write("other.md")
        self.assertEqual([], self.errors())

    def test_recently_completed_limit(self):
        (self.folder / "2026-11/example.md").unlink()
        links = []
        for n in range(11):
            self.write(f"closed-{n}.md", meta={**self.meta, "status": "completed", "completed": "2026-11-04"}, body=self.body + "\n## Outcome\nVerified.\n")
            links.append(f"- [Closed](2026-11/closed-{n}.md).")
        self.index("## Recently completed\n\n" + "\n".join(links))
        self.assert_error("exceeds ten")

    def test_folder_record_and_adjacent_artifact(self):
        (self.folder / "2026-11/example.md").unlink()
        self.write("example/README.md")
        (self.folder / "2026-11/example/design.md").write_text("# Artifact\n")
        self.index("## Waiting\n\n- [Example](2026-11/example/README.md).\n")
        self.assertEqual([], self.errors())

    def test_invalid_path_and_symlink(self):
        path = self.folder / "2026-11/example.md"
        path.rename(path.with_name("Opaque_Name.md"))
        self.assert_error("unsupported task path")
        path.with_name("Opaque_Name.md").unlink()
        outside = self.root / "outside.md"
        outside.write_text("Not a task and must not be read as metadata.\n")
        path.symlink_to(outside)
        self.assert_error("symlinks are not allowed")

    def test_missing_and_nonliving_index(self):
        self.index()
        index = self.folder / "README.md"
        index.write_text(index.read_text().replace("status: living", "status: stable"))
        self.assert_error("status living")
        index.unlink()
        self.assert_error("missing index")


    def test_custom_path_is_read_from_knowledge_base_yaml(self):
        (self.root / "knowledge-base.yaml").write_text("rules:\n  checks:\n    tasks:\n      path: work/todo\n")
        self.assertEqual(["work/todo: missing directory or symlink"], self.errors())
        self.folder.rename(self.root / "todo-moved")
        (self.root / "work").mkdir()
        (self.root / "todo-moved").rename(self.root / "work/todo")
        self.assertEqual([], self.errors())

    def test_default_path_without_configuration(self):
        self.assertEqual("notebook/tasks", checker.tasks_path(self.root))


if __name__ == "__main__":
    unittest.main()
