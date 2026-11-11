---
status: working
---

# Conformance with knowledge-base-kit

A workspace extends the [knowledge-base-kit](https://github.com/danielnaab/knowledge-base-kit/tree/v2.0.0)
(`sync_policy: extend`). Its seven core policies bind unless a documented deviation says otherwise. A workspace
records this in a short **knowledge-base-kit conformance** section of its local `docs/conventions.md`.

## What the section contains

- A table of the seven policies with how the workspace applies each.
- **Inherited versus added:** inherited means knowledge-base-kit's policies and the pinned notebook-kit; added means local
  rules, boundaries, and tooling.
- **Deliberate deviations,** each with a reason.
- **Verification:** which checks run and what stays manual.
- **Ask-first changes:** who approves changes to `askFirst` paths, and where the approval is recorded.
- **New structure** needs a named, repeated pain, recorded where it is added.

## Default application

| Policy | Application in a workspace following this kit |
| --- | --- |
| Authority | Layers declared under `sources` in `knowledge-base.yaml`. Code, configuration, and original sources outrank notes. |
| Provenance | `sources` frontmatter with footnotes, or `## Sources`, in docs, wiki pages, task records, and session records. `README.md`, `AGENTS.md`, and `index.md` listings are exempt. |
| Lifecycle | `status: draft \| working \| stable \| deprecated` on `docs/` and wiki pages. Raw sources and records carry none; their path marks them. |
| Linking | Relative Markdown links; backticks for literal paths and code only. |
| Intent-revealing structure | Descriptive file and session slugs. |
| Write boundaries | `rules.writes` in `knowledge-base.yaml`; unlisted paths get conservative, documentation-only edits. |
| Style | Concise bullets; trim long sections when touched. |

## Deviations this kit makes

- Task `status` uses its own vocabulary ([tasks](tasks.md#metadata)).
- `YYYY-MM` folders are time buckets. They keep chronological ledgers browsable and task paths stable.

Records without `status` are no longer a deviation: knowledge-base-kit's temporal layers include raw sources and historical records (since meta-knowledge-base v1.1.0).

## Verification

- `just check-kb` runs [knowledge-base-kit's checker](https://github.com/danielnaab/knowledge-base-kit/blob/v2.0.0/docs/tools.md)
  over the scopes in `rules.checks`: links and heading anchors, lifecycle `status`, provenance, and OKF
  conformance of the vault (`type` on every note, index shapes, link classes). Links to notes not written yet
  are counted, not failed.
- `just index --check` reports stale folder indexes.
- `just check-tasks` validates task records and the index.
- `just check-templates` reports drift between a workspace's templates and the kit's canonical copies.
- `just check-obsidian` reports drift between the vault's shared Obsidian settings and the kit's seed.
- Write boundaries and `askFirst` approvals are not machine-checked. Verify them in Plan → Patch → Verify.

## Sources

- [knowledge-base-kit README](https://github.com/danielnaab/knowledge-base-kit/blob/v2.0.0/README.md)
- [knowledge-base-kit dependency playbook: the extend policy](https://github.com/danielnaab/knowledge-base-kit/blob/v2.0.0/docs/playbooks/manage-kb-dependencies.md)
- [knowledge-base-kit evolve-a-KB playbook](https://github.com/danielnaab/knowledge-base-kit/blob/v2.0.0/docs/playbooks/evolve-kb.md)
- [knowledge-base-kit checker configuration](https://github.com/danielnaab/knowledge-base-kit/blob/v2.0.0/docs/tools.md#configuring-scan-scopes)
- [knowledge-base-kit temporal layers policy](https://github.com/danielnaab/knowledge-base-kit/blob/v2.0.0/docs/policies/temporal-layers.md)
