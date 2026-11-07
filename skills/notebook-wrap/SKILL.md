---
name: notebook-wrap
description: Preserve useful work memory and lookup-use signals in a Markdown work-memory workspace with proportional no-log, daily-only, or session-plus-daily records. Use for user-initiated information requests worth retaining, outcomes, task or blocker changes, meaningful work or handoffs, and wrap or remember requests. Skip incidental agent mechanics and repetitive chatter.
---

# Save useful work memory

Read `AGENTS.md`, `knowledge-base.yaml`, and the workspace's `docs/conventions.md` before editing; the kit's
[workflow](../../docs/workflow.md) and [tasks](../../docs/tasks.md) define the rules. Reuse them when already
read. Read only affected records and reuse verified evidence. Use `date +%F` and the
templates in `notebook/templates/`.

1. Choose the [logging level](../../docs/workflow.md#logging-levels) by future usefulness, not reply length:
   incidental mechanics or chatter → no log; a useful small result or a lookup signal → daily-only;
   reasoning, artifacts, or a handoff worth preserving → session + daily. If nothing merits retention and the
   user has not asked to remember it, stop without notes, sessions, tasks, or a logging-only commit.
   Answer first; no ceremony after every response.
2. Follow the [persistence checkpoints](../../docs/workflow.md#persistence-and-checkpoints): save critical
   decisions, authorization boundaries, changed blockers or next actions, and handoffs promptly in their
   canonical record; batch routine summaries at milestones, decisions, topic changes, or known pauses.
3. Sessions: start or resume a minimal goal and source index at
   `notebook/records/sessions/YYYY-MM/YYYY-MM-DD-<topic>.md`, artifacts in a sibling `YYYY-MM-DD-<topic>/` folder;
   add reasoning and artifacts at milestones. Every note gets a `type`; agent-written notes record `generated`
   ([layout](../../docs/layout.md#notes)). Daily-only
   outcomes create no session. For delegation record the repo, handle, session, ownership, completion condition,
   and disposition.
4. Distinguish proposed, changed, committed, pushed, merged, and activated work. State exact verification and
   unrun checks.
5. Update durable `notebook/wiki/` pages when understanding changes, with lifecycle status and provenance
   (`sources` frontmatter or `## Sources`). Links stay inside `notebook/`; move notes with `nix run .#move`.
6. In `notebook/records/daily/YYYY-MM/YYYY-MM-DD.md` use Activity for work and decisions and
   [Lookups](../../docs/workflow.md#lookup-signals) for compact request intent, outcome, and source.
   Sanitize topics, group related requests, never invent counts, and never duplicate what Activity or a session
   already holds. List sessions only when they were active that day. Preserve existing entries.
7. Update affected task records under [tasks](../../docs/tasks.md), then regenerate indexes with
   `nix run .#index`. Capture confirmed TODOs,
   not a task per answered question; verify evidence before closing; keep paths stable. Validate with
   `nix run .#check-tasks` when task records change.
8. Update the root dashboard only when current priorities or open threads change. Never store secrets or full
   transcripts. Commit coherent, reviewed checkpoints only where the workspace's instructions authorize it;
   leave unrelated dirty work. Batch small related entries; do not commit per reply.
9. Batch related edits, review the diff, check affected links, and run only the relevant checks
   (`nix run .#check-kb` for links, status, and Sources). Report briefly what was saved and what is open.
   If persistence is unavailable, return the brief in chat and say it was not saved.

Saving a checkpoint does not end managed coordination or permit destructive cleanup. The orchestrating agent is
the single writer of shared indexes; workers return note-ready summaries.
