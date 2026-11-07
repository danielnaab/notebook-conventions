---
status: working
---

# Conformance with the meta-KB

A workspace extends the [meta-knowledge-base](https://github.com/danielnaab/meta-knowledge-base/tree/v1.1.0)
(`sync_policy: extend`). Its seven core policies bind unless a documented deviation says otherwise. A workspace
records this in a short **Meta-KB conformance** section of its local `docs/conventions.md`.

## What the section contains

- A table of the seven policies with how the workspace applies each.
- **Inherited versus added:** inherited means the meta-KB policies and the pinned kit; added means local
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

Records without `status` are no longer a deviation: meta-KB v1.1.0 adds the raw-sources and historical layers.

## Verification

- `nix run .#check-kb` runs [knowledge-base-integrity](https://github.com/danielnaab/knowledge-base-integrity)
  over the scopes in `rules.checks`: links and heading anchors, lifecycle `status`, provenance, and OKF
  conformance of the vault (`type` on every note, index shapes, link classes). Links to notes not written yet
  are counted, not failed.
- `nix run .#index -- --check` reports stale folder indexes.
- `nix run .#check-tasks` validates task records and the index.
- `nix run .#check-templates` reports drift between a workspace's templates and the kit's canonical copies.
- Write boundaries and `askFirst` approvals are not machine-checked. Verify them in Plan → Patch → Verify.

## Sources

- [Meta-KB README](https://github.com/danielnaab/meta-knowledge-base/blob/v1.1.0/README.md)
- [Meta-KB dependency playbook: the extend policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.1.0/docs/playbooks/manage-kb-dependencies.md)
- [Meta-KB evolve-a-KB playbook](https://github.com/danielnaab/meta-knowledge-base/blob/v1.1.0/docs/playbooks/evolve-kb.md)
- [knowledge-base-integrity configuration](https://github.com/danielnaab/knowledge-base-integrity/blob/v0.4.0/docs/README.md#configuring-scan-scopes)
- [Meta-KB temporal layers policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.1.0/docs/policies/temporal-layers.md)
