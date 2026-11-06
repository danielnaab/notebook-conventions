---
status: working
---

# Workspace layout and layers

A workspace is a Git repository of Markdown that people browse in Obsidian and agents maintain.
Work memory lives under `notebook/`. Workspace operating guidance lives in `docs/`; local tooling
in `scripts/` and `tests/`. The repository root is the Obsidian vault.

## Layers

| Layer | Location | Purpose | Lifetime |
| --- | --- | --- | --- |
| Tasks | `notebook/tasks/` | Stable task records and a small active-work index; authoritative next actions and blockers. | Living; records are kept after completion |
| Daily ledger | `notebook/daily/YYYY-MM/YYYY-MM-DD.md` | Activity across the day, linked to canonical records. | Historical |
| Sessions | `notebook/sessions/YYYY-MM/YYYY-MM-DD-<topic>/README.md` | Goal, outcomes, decisions, checks, blockers, next actions, and an artifact index. | Historical snapshots |
| Wiki | `notebook/wiki/` | Durable synthesis, updated as evidence changes. | Durable |
| Raw captures | `notebook/raw/` | Requested source inputs with provenance; originals preserved. | Durable |
| Templates | `notebook/templates/` | Note structures shared by Obsidian and agents. | Durable |
| Workspace docs | `docs/` | How people and agents use this workspace. Includes the local conformance table. | Durable |

Each layer maps to a meta-KB temporal layer: sessions and daily notes are ephemeral or historical,
tasks are tracking, and wiki and docs are durable. See [conformance](conformance.md).

## Authority

- Project code and configuration, and identified original sources, outrank every note here.
- Wiki pages interpret; they link to their sources and say how fresh they are.
- Session plans and daily entries are dated snapshots. A proposal is not an adopted decision, and an
  inventory snapshot is not proof of live state.
- Project implementation stays in the target repository. Link to it; do not copy code here.

## Naming and links

- Descriptive slugs: `2026-11-05-repository-layout`, not `session-3`.
- Real relative Markdown links, never wikilinks, so the same text works in Obsidian, Git hosts, and agent tools.
- Backticks are for literal paths, patterns, and code, not for navigation.
- Task records keep their creation-month path when their status changes. The path is the identifier.

## Sources

- [Meta-KB authority policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.0.1/docs/policies/authority.md)
- [Meta-KB temporal layers policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.0.1/docs/policies/temporal-layers.md)
- [Meta-KB linking policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.0.1/docs/policies/linking.md)
- [Meta-KB intent-revealing structure policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.0.1/docs/policies/intent-revealing-structure.md)
