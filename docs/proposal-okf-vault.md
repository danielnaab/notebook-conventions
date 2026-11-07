---
status: draft
---

# Proposal: the notebook as an OKF vault

A proposal for a breaking kit release, not adopted guidance. It makes `notebook/` both the Obsidian vault and an
[Open Knowledge Format (OKF) v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
bundle, and organizes it by lifecycle. Where this proposal conflicts with [layout](layout.md), [obsidian](obsidian.md),
[tasks](tasks.md), or [conformance](conformance.md), those documents stay authoritative until a release adopts it.

## Motivation

- Agents write most notes. OKF gives agent-written notes a portable shape: required `type`, and optional
  provenance (`sources`), trust (`generated`, `verified`), and freshness (`stale_after`) fields.
- Opening the repository root as the vault mixes notes with code, dependencies, and workspace tooling.
- Write rules and checks are easier to state as path globs when the path says how a note may change.

## Proposed conventions

### Vault and bundle

- Obsidian opens `notebook/`. The vault root is the bundle root. `README.md`, `AGENTS.md`, `docs/`, tooling, and
  code stay outside it.
- `notebook/index.md` declares `okf_version: "0.2"` in its frontmatter, the only frontmatter OKF allows in an
  index.

### Lifecycle-first layout

The top level of the vault names a lifecycle; the domain is one level down.

| Folder | Lifecycle | Examples |
| --- | --- | --- |
| `raw/` | Sources, preserved as captured | `raw/<domain>/YYYY-MM/…` |
| `records/` | Dated, written once, corrected rather than revised | `records/daily/`, `records/sessions/`, `records/<domain>/` |
| `tasks/` | Tracking: changes until closed | `tasks/YYYY-MM/<slug>.md` |
| `wiki/` | Maintained knowledge with lifecycle status | `wiki/people/`, topic pages |
| `templates/` | Note structures, excluded from the bundle | see [Templates](#templates) |

- A second tracking kind moves `tasks/` under a `tracking/` parent, mirroring `records/`.
- Sessions become single files, `records/sessions/YYYY-MM/YYYY-MM-DD-<slug>.md`, with a sibling `<slug>/` folder
  only for artifacts. A folder-shaped task follows the same pattern.

### Notes

- Every note in the bundle carries a non-empty `type`, such as `Daily Note`, `Session`, `Task`, or `Person`.
  `title` and `description` are recommended; `description` feeds index entries.
- Agent-written notes record `generated: { by: <producer>/<version>, at: <ISO 8601> }`. A person's review adds
  `verified: { by: human:<id>, at: … }`. `process:<id>` names automated processes.
- `sources` frontmatter (with footnotes keyed to `sources[].id`) records provenance inside the bundle. `docs/`
  keep the meta-KB `## Sources` section.
- Notes about time-bound things set `stale_after`.

### Links

- Markdown links only; Obsidian's wikilink support is off.
- Links are relative to the linking note, as today: `[Name](../../wiki/people/Some%20Name.md)`. Obsidian writes them
  natively ("Relative path to file"), and they work in Obsidian, on Git hosts, and in OKF tools (§6.1) without a
  plugin. The [Better Markdown Links](https://github.com/mnaoumov/obsidian-better-markdown-links) plugin is an
  optional nicety (a `./` prefix and angle brackets instead of `%20`).
- Moving a note rewrites every relative link to and from it. A kit command does this
  (`nix run .#move -- OLD NEW`); the conversion script for an upgrade uses the same code. Obsidian already does it
  for renames made inside Obsidian.
- A link may point at a note that does not exist yet (OKF §6.1). Checks report it as unwritten instead of failing.
- Links out of the bundle (workspace docs, the kit) use absolute URLs or are mentioned as backticked paths.
- Root-anchored (`/`) links were considered and rejected: Git hosts read `/` as the repository root, and Obsidian
  needs a community plugin to write them.

### Display names and aliases

- `title` holds the display name; filenames may be dated slugs. Agents write the title as link text.
- `aliases` make a note findable through `[[` autocomplete, which inserts a Markdown link with the alias as text.
- People notes carry an `@Full Name` alias, so `[[@` lists people.

### Index files

- Folders inside the bundle use OKF `index.md` listings (§8): headed sections of
  `* [Title](path) - description`, with no frontmatter. `README.md` has no special meaning inside the bundle and
  is not used there. Guidance prose currently in folder READMEs moves to the kit docs.
- Index files are generated from note frontmatter by a kit command (`nix run .#index`), so every workspace gets
  identical listings. The task index, `tasks/index.md`, is generated from each task's `status` and
  `description`, sectioned by status, and the task check verifies it is current.

### Templates

- Templates stay in `templates/`, because Obsidian's Templates and Daily Notes plugins cannot use a hidden folder.
- Each template carries the `type` of the note it produces, so it conforms even to tools that ignore exclusions.
- A `.okfignore` file at the bundle root, using `.gitignore` pattern rules, lists `templates/`. This is option B of
  the open [OKF issue #58](https://github.com/GoogleCloudPlatform/open-knowledge-format/issues/58). The kit's
  checks honour it; other OKF tools may not yet.

## Checks

- **OKF conformance:** every note not excluded by `.okfignore` has parseable frontmatter with a `type`; index files
  follow §8.
- **Link classes:** a missing target inside the bundle is reported as unwritten. Malformed links, links escaping
  the bundle, and missing heading anchors fail. An unwritten target close to an existing note's name is flagged
  as a likely typo.
- **Lifecycle and provenance** apply to `wiki/**`, with `sources` frontmatter accepted as provenance there.
- **Implementation:** [knowledge-base-integrity](https://github.com/danielnaab/knowledge-base-integrity) gains OKF
  conformance, `.okfignore`, link classes, and frontmatter provenance. It stays the one gate on every workspace and
  keeps implementing the meta-KB. The `okf` CLI shipped with the
  [OKF Wiki](https://github.com/ysasiwat/obsidian-okf-wiki) plugin may later run as an advisory second opinion. It
  is young, has no exclusion support, and expects `index.md` and `log.md` in every bundle.

## Seed changes

- `.obsidian/` moves to `notebook/.obsidian/`. `app.json` keeps `useMarkdownLinks: true` and
  `newLinkFormat: relative`; the template and daily-note folders follow the new layout (`templates`,
  `records/daily`).
- The seed `flake.nix` imports `nix/workspace.nix` from the pinned kit input instead of `.scions/`, so the dev
  shell and checks exist before the first graft, and `.envrc` is a plain `use flake`.
- `knowledge-base.yaml` `paths` and `rules` move to the new folders; the write rules can express "create, never
  modify" for `records/**`.

## OKF versions

Each kit release states the OKF version it targets and writes it to `notebook/index.md` (`okf_version`). Moving
to a new OKF version is a kit release with upgrade steps. Spec drafts and open proposals are not tracked, except
the `.okfignore` extension above, which a later release replaces if OKF adopts a different mechanism.

## Meta-KB changes

Instead of new kit deviations, an additive meta-KB v1.1.0 makes these sanctioned options, leaving existing
knowledge bases unaffected:

- **Provenance:** structured provenance, meaning `sources` frontmatter with footnotes keyed to it, counts the same
  as a `## Sources` section.
- **Temporal layers:** a raw-sources layer (preserved as captured) and a historical layer (dated, written once,
  retained indefinitely) beside ephemeral, tracking, and durable. This also retires the kit's existing deviation
  for daily notes and sessions.
- **Linking:** unchanged. Relative links already satisfy it.

The kit release pins meta-KB v1.1.0 and knowledge-base-integrity with the matching checks.

## Upgrading (outline)

A release ships steps an agent can apply: move folders to the new layout with the move command; add `type` to
every note; replace folder READMEs with generated `index.md` files; flatten session folders; move `.obsidian/`;
add `.okfignore`; reopen the vault at `notebook/`. A conversion script in the kit drives most of it.

## Decided in review

- Relative links everywhere; root-anchored links rejected.
- Checks live in knowledge-base-integrity; the `okf` CLI is at most advisory.
- Index generation and note moves are kit commands.
- Each kit release pins its OKF version.
- Meta-KB changes go upstream as v1.1.0 instead of kit deviations.

## Sources

- [OKF v0.2 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
- [OKF issue #58: excluding non-concept Markdown files](https://github.com/GoogleCloudPlatform/open-knowledge-format/issues/58)
- [OKF Wiki plugin](https://github.com/ysasiwat/obsidian-okf-wiki)
- [Better Markdown Links plugin](https://github.com/mnaoumov/obsidian-better-markdown-links)
- [Meta-KB linking policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.0.1/docs/policies/linking.md)
- [Meta-KB provenance policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.0.1/docs/policies/provenance.md)
- [Meta-KB temporal layers policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.0.1/docs/policies/temporal-layers.md)
- [Layout and layers](layout.md)
