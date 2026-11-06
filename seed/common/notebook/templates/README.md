# Templates

These files are shared by Obsidian's core Templates and Daily notes plugins and by agents. They are copied from the
pinned kit; `nix run .#check-templates` reports how they differ from its canonical copies.

- [Daily note](daily.md): chronological activity and links to active sessions.
- [Session index](session.md): goal, artifacts, outcomes, checks, and next actions.
- [Wiki article](wiki.md): lifecycle, freshness, and provenance for durable synthesis.
- [Task record](task-record.md): canonical TODO metadata, next action, blockers, triggers, and done criteria.

Obsidian replaces `{{title}}` and `{{date:...}}`. Agents substitute real titles and dates using `date +%F`; never
leave placeholders in saved notes. Use real Markdown links relative to the resulting note, not the template.
