---
status: stable
---
# Temporal layers policy

Knowledge bases often need three temporal layers:

## Ephemeral (notes/, explorations/)
- Purpose: scratch work, session logs
- Lifecycle: draft → archived
- Retention: days to weeks
- Archive when: insights extracted or session complete

## Tracking (status/, current-state/)
- Purpose: implementation progress, handoff
- Lifecycle: working → deprecated → archived
- Retention: weeks to months
- Archive when: milestone reached or work complete

## Durable (docs/, decisions/)
- Purpose: architecture, guides, decisions
- Lifecycle: draft → working → stable → deprecated
- Retention: indefinite
- Update when: system changes significantly

## Living documents

Some documents are always current (continue-here.md, tasks.md):
- Mark with `status: living` in frontmatter
- Snapshot before major milestones
- Latest version is always current

## Migration paths

- Ephemeral → Durable: extract insights to docs
- Tracking → Archived: snapshot when work completes
- Living → Snapshot: preserve state at milestones

Related:
- [Lifecycle policy](lifecycle.md)
- [Authority policy](authority.md)
