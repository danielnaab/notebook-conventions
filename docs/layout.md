---
status: working
---

# Workspace layout and layers

A workspace is a Git repository of Markdown that people browse in Obsidian and agents maintain. Work memory lives
in `notebook/`, which is both the Obsidian vault and an [OKF v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
bundle. Workspace operating guidance lives in `docs/`; tooling in `scripts/` and `tests/`. Those, the root
`README.md` and `AGENTS.md`, and the pinned `.scions/` stay outside the vault.

## Layers

The top level of the vault names a lifecycle; the domain is one level down. Write rules and checks are path globs.

| Folder | Lifecycle | Holds |
| --- | --- | --- |
| `raw/` | Sources, preserved as captured; never edited | `raw/<domain>/YYYY-MM/…`: transcripts, exports, clippings |
| `records/` | Dated, written once, corrected rather than revised | `records/daily/YYYY-MM/YYYY-MM-DD.md`, `records/sessions/YYYY-MM/YYYY-MM-DD-<slug>.md`, `records/<domain>/` |
| `tasks/` | Tracking: changes until closed | `tasks/YYYY-MM/<slug>.md` (see [tasks](tasks.md)) |
| `wiki/` | Maintained knowledge with lifecycle status | `wiki/people/`, topic pages |
| `templates/` | Note structures, excluded from the bundle | see [Templates](#templates) |

- These are the meta-KB [temporal layers](https://github.com/danielnaab/meta-knowledge-base/blob/v1.1.0/docs/policies/temporal-layers.md):
  raw sources, historical records, tracking, and durable knowledge. Raw sources and records carry no lifecycle
  `status`; their path marks them.
- A session is one file. Artifacts it owns (scripts, data) go in a sibling folder with the same name:
  `records/sessions/2026-11/2026-11-06-plan.md` and `records/sessions/2026-11/2026-11-06-plan/`.
- A second tracking kind moves `tasks/` under a `tracking/` parent, mirroring `records/`.
- `YYYY-MM` folders are time buckets: they keep chronological ledgers browsable and task paths stable.

## Notes

Every note in the bundle is OKF frontmatter plus a Markdown body.

| Field | Use |
| --- | --- |
| `type` | Required. `Daily Note`, `Session`, `Task`, `Topic`, `Person`, `Source`, or another descriptive name. |
| `title`, `description` | Recommended. The display name, and one sentence that the folder index shows. |
| `aliases` | Other names for `[[` autocomplete in Obsidian; people notes carry `@Full Name`. |
| `sources` | Provenance: each entry has a `resource` (URL or path) and an `id` that footnotes cite (`[^id]`). |
| `generated` | Agent-written notes: `{ by: <producer>/<version>, at: <ISO 8601 with offset> }`. |
| `verified` | A review: `{ by: human:<id>, at: … }`; `process:<id>` names an automated check. |
| `stale_after` | When a note about something time-bound stops being trustworthy. |
| `resource` | For a raw source: the URL or document it was captured from. |

- Filenames may be dated slugs; `title` holds the real name, and agents write it as link text.
- Wiki pages also carry `status` (`draft`, `working`, `stable`, `deprecated`) and provenance: `sources`
  frontmatter or a `## Sources` section.

## Links

- Markdown links only, relative to the linking note: `[Pat Lee](../../wiki/people/Pat%20Lee.md)`. Obsidian writes
  them natively, and they work on Git hosts and in OKF tools. Wikilinks are off.
- A link may point at a note that does not exist yet (OKF §6.1). The check reports it as unwritten and does not
  fail; a link whose note exists under the same name elsewhere fails as misdirected.
- Links out of the vault (workspace docs, the kit) are absolute URLs or backticked paths, since the vault is
  opened on its own.
- Move notes with `nix run .#move -- OLD NEW`: it rewrites every relative link to and from them. Obsidian does
  the same for renames made inside Obsidian.
- Backticks are for literal paths, patterns, and code, not for navigation.

## Index files

- Folders use OKF `index.md` listings: headed sections of `* [Title](path) - description`, no frontmatter. The
  vault root's `index.md` declares `okf_version`. `README.md` has no special meaning inside the vault.
- `nix run .#index` generates them from note frontmatter (`title`, else the first `#` heading, and
  `description`); `--check` reports stale ones. `tasks/index.md` lists active tasks by status, and the task
  check fails when it is stale.

## Templates

- Templates live in `notebook/templates/`, because Obsidian's Templates and Daily notes plugins need a visible
  folder. Each carries the `type` of the note it produces.
- `notebook/.okfignore` (`.gitignore` syntax) lists `templates/`, so the OKF checks skip it. This is option B of
  the open [OKF issue #58](https://github.com/GoogleCloudPlatform/open-knowledge-format/issues/58); a later
  release follows OKF if it adopts another mechanism.

## Authority

- Project code and configuration, and identified original sources, outrank every note here.
- Wiki pages interpret; they cite their sources and say how fresh they are.
- Records are dated snapshots. A proposal is not an adopted decision, and an inventory snapshot is not proof of
  live state.
- Project implementation stays in the target repository. Link to it; do not copy code here.

## Naming

- Descriptive slugs: `2026-11-05-repository-layout`, not `session-3`.
- Task records keep their creation-month path when their status changes. The path is the identifier.

## Sources

- [OKF v0.2 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
- [OKF issue #58: excluding non-concept Markdown files](https://github.com/GoogleCloudPlatform/open-knowledge-format/issues/58)
- [Meta-KB temporal layers policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.1.0/docs/policies/temporal-layers.md)
- [Meta-KB provenance policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.1.0/docs/policies/provenance.md)
- [Meta-KB authority policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.1.0/docs/policies/authority.md)
- [Meta-KB linking policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.1.0/docs/policies/linking.md)
