---
name: notebook-start
description: Orient work in a Markdown work-memory workspace using its tasks, daily, session, and wiki notes. Use when the user asks what to focus on, to pick up an earlier thread, or to plan a work session. Do not use for every small question or routine status check.
---

# Orient a work session

Read `AGENTS.md`, `knowledge-base.yaml`, the root `README.md` dashboard, and the small task index
`notebook/tasks/README.md` from the workspace root. Reuse what is already in context.

1. Infer the focus from the request and conversation; do not require arguments. Ask only if a material
   choice cannot be resolved safely.
2. Read matching task records by `project` and `contexts`, then only the daily, session, and wiki notes
   relevant to the focus. Do not bulk ingest history. The rules are in [tasks](../../docs/tasks.md) and
   [workflow](../../docs/workflow.md).
3. Surface relevant Ready actions and waiting items whose trigger may have changed. On a requested review,
   use `date +%F` for due and review dates and stale blockers; do not invent deadlines or repeat the whole
   queue every turn. With no stated focus, suggest a few actions grounded in task records and the dashboard,
   separating stale notes from evidence. If nothing useful stands out, ask what to work on.
4. For a specific task, state the desired outcome, the smallest useful next step, and whether to work locally,
   hand off one task, or coordinate independent tasks. Apply the [logging levels](../../docs/workflow.md#logging-levels):
   only work whose reasoning or artifacts matter needs a session index.
5. During a requested workflow review, read only relevant recent lookup entries to find recurring questions or
   friction. Do not turn each lookup into a TODO.

Orientation alone does not authorize launching agents, connecting services, or changing external systems.
Re-evaluate a waiting task only when relevant evidence arrives or a scoped check is requested. Task state
never grants permission for destructive action; raise data-boundary uncertainty before any transfer.
Apply `notebook-wrap` when memory is warranted or requested; orientation alone needs no note, session, or commit.
