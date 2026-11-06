---
status: working
---

# Work-memory workflow

How to decide what to record, when to save it, and where it goes. The layers are in
[layout](layout.md). Existing authorization, data, and secrecy boundaries of the workspace always apply.

## Logging levels

Choose the smallest record that preserves useful work memory or a useful signal about how the
workspace is used. Daily notes are a meaningful ledger, not an exhaustive conversation log.

| Level | When | Record |
| --- | --- | --- |
| No log | Incidental agent operations, routine tool chatter, or an exchange with no result or lookup signal worth keeping | No note, session, task, or logging-only commit |
| Daily-only | A useful small result or decision, or a user-initiated lookup that reveals usage patterns even when the answer is familiar | One concise daily entry: lookups under `## Lookups`, work and decisions under `## Activity` |
| Session + daily | Investigation, planning, design, implementation, validation, or handoff whose reasoning or artifacts matter | A coherent session with useful artifacts; the daily entry links to it |

- Need the reasoning later → session. Need the result or a lookup signal → daily. Need neither → no log.
- Decide by future usefulness, not elapsed time, reply length, or tool count.
- A small task-state update can live in the task record plus a daily entry. Do not create a session or task
  because a question was answered.
- "Remember this" overrides omission but selects the appropriate safe record, not a forced session or transcript.
- Answer first. Avoid a visible logging ritual after every reply.

## Persistence and checkpoints

This is an interaction-time workflow. It is not a background writer, a timer, or a guarantee against interruption.

- **Persist promptly:** accepted consequential decisions, authorization boundaries, changed blockers or next
  actions, and handoffs that must survive interruption. Update the canonical task or session; a concise daily
  entry suffices if nothing else is needed.
- **Session start:** begin with a minimal goal and source index. Add reasoning, evidence, and artifacts at milestones.
- **Batch summaries:** group routine daily and lookup entries at a completed deliverable, an accepted decision
  or handoff, a topic change, or a known pause. Flush pending useful entries before leaving the thread.
  A reply alone is not a checkpoint.
- **Write once, link elsewhere:** tasks own current state, sessions own reasoning, wiki pages own durable
  synthesis. The daily ledger carries a short outcome and a link.
- **Commit at a coherent checkpoint:** saving a critical fact need not create its own commit. Batch related
  reviewed changes; never make a commit per answer or lookup.

### Efficient maintenance

- Reuse evidence, source paths, and check results already gathered. Distinguish earlier evidence from a new live check.
- Reread instructions only when missing, changed, or uncertain. Read only affected records.
- Prepare related edits together, then verify once: review the diff and affected links and claims.
- Run the checks that match the change: the task check for task records, the integrity check for links, status,
  and Sources. Reserve broad builds for configuration or dependency changes.

## Lookup signals

A user-initiated information request can merit a compact daily record even when the answer is not new.

- Record distinct intent, a short outcome (answered, source found, unresolved), and a source link if there is one.
- Use `## Lookups` in that day's note, separate from `## Activity`. One sentence or bullet each.
- Sanitize topic labels. Do not copy questions, transcripts, or sensitive output.
- File listings, command-help checks, `git status`, and other agent mechanics are not lookups.
- Group related requests. Note recurrence only when actually observed. Never invent counts.
- If Activity or a session already captures the request, link to it instead of duplicating.
- At a requested workflow review, look for recurring questions, navigation friction, and unsuccessful searches.
  Propose improvements only when the signal justifies them. There is no automatic review job or metrics.

## Plan → Patch → Verify

1. Read only the notes relevant to the work, and the policies that apply before editing.
2. For non-trivial work, state scope, uncertainties, and intended changes. Start a session only if it merits one.
3. Use the [templates](../templates/). Resolve placeholders when writing: use the real date and title.
   Never leave `{{...}}` in a saved note and never rewrite a historical note's date.
4. Patch the smallest useful set of documents. Ground important claims and operational guidance in linked
   evidence, preferably in `## Sources`.
5. Verify links, claims, and exact checks. Distinguish proposed, changed, committed, pushed, merged,
   deployed, and activated states.

## Daily notes

- Append work and results worth retaining, including meetings and other non-agent activity.
- One short Activity bullet may be enough. Link to a source, task, or canonical document.
- Add times only when observed. Never invent activity, requests, or counts. Skip routine chatter and tool-by-tool logs.
- List sessions under `## Agent sessions` only when they were active that day.
- Preserve existing entries; avoid repeating an outcome across sections.

## Sessions and closure

- One folder per coherent thread with an intent-revealing slug, not per question, chat, or lookup.
  Avoid colliding with an unrelated session; use a more specific slug and never overwrite.
- A session resumed on another date keeps its original folder. Update its index and link it from each
  active day's note. Date significant follow-ups; do not silently rewrite earlier decisions.
- Artifacts are snapshots. Promote lasting insight into a wiki page and link the evidence back.
  Deleting a completed session requires authorization.
- Log outcomes, decisions and rationale, evidence, blockers and owners, and next actions. For delegated work
  record the repo, handle, session, ownership, completion condition, and disposition.
- At a checkpoint update only the applicable records: affected tasks and index or wiki pages, a concise daily
  entry, and the session index if one exists. Verify evidence before closing a task.
- Workers return note-ready summaries; the orchestrating agent is the single writer of shared indexes.

## Durable notes

- Start with focused topic pages and a map, not a fixed taxonomy. Add folders when repeated navigation pain warrants them.
- Use lifecycle `status: draft | working | stable | deprecated`. Stable means reviewed and aligned with sources.
  Keep freshness limits visible.
- Update or mark outdated synthesis when evidence changes. Do not copy a transient task list into many documents.

## Safety

- Read and write only data suitable for this workspace. External access sends requests: confirm account,
  resource, and provider before transfer.
- No transcripts, secrets, or sensitive message dumps. Never store credentials.
- Honor write boundaries and dirty work. If persistence is unavailable, return a note-ready brief and say it was not saved.

## Sources

- [Meta-KB agent workflow playbook](https://github.com/danielnaab/meta-knowledge-base/blob/v1.0.1/docs/playbooks/agent-workflow.md)
- [Meta-KB provenance policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.0.1/docs/policies/provenance.md)
- [Meta-KB lifecycle policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.0.1/docs/policies/lifecycle.md)
- [Meta-KB evolve-a-KB playbook](https://github.com/danielnaab/meta-knowledge-base/blob/v1.0.1/docs/playbooks/evolve-kb.md)
