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
- Opening the repository root as the vault mixes notes with code, dependencies, and workspace tooling, and the
  vault root differs from any bundle root, so neither Obsidian nor OKF tools agree on what `/` means.
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
- Links inside the bundle are rooted at the bundle root: `[Name](/wiki/people/Name.md)`. Paths with spaces use
  angle brackets: `[Name](</wiki/people/Some Name.md>)`. Obsidian resolves `/` from the vault root natively; the
  [Better Markdown Links](https://github.com/mnaoumov/obsidian-better-markdown-links) plugin writes them, with
  "Absolute path in vault" and "Should use leading slash for absolute paths" on.
- A link may point at a note that does not exist yet (OKF §6.1). Checks report it as unwritten instead of failing.
- Links out of the bundle (workspace docs, the kit) use absolute URLs.
- Relative links stay the fallback if Git-host browsing becomes important.

### Display names and aliases

- `title` holds the display name; filenames may be dated slugs. Agents write the title as link text.
- `aliases` make a note findable through `[[` autocomplete, which inserts a Markdown link with the alias as text.
- People notes carry an `@Full Name` alias, so `[[@` lists people.

### Index files

- Folders inside the bundle use OKF `index.md` listings (§8): headed sections of
  `* [Title](path) - description`, with no frontmatter. `README.md` has no special meaning inside the bundle and
  is not used there. Guidance prose currently in folder READMEs moves to the kit docs.
- Index files may be generated from note frontmatter. The task index, `tasks/index.md`, is generated from each
  task's `status` and `description`, sectioned by status, so it cannot drift.

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
- Implementation options, to decide: extend
  [knowledge-base-integrity](https://github.com/danielnaab/knowledge-base-integrity) with OKF conformance and link
  classes, run with `notebook/` as its root, or adopt the `okf` CLI shipped with the
  [OKF Wiki](https://github.com/ysasiwat/obsidian-okf-wiki) plugin, which already reports broken links as `info`.
  The CLI expects `index.md` and `log.md` in a bundle and has no exclusion support yet.

## Seed changes

- `.obsidian/` moves to `notebook/.obsidian/`. `app.json`: `useMarkdownLinks: true`, `newLinkFormat: absolute`,
  the template and daily-note folders under the new layout (`templates`, `records/daily`).
- The seed `flake.nix` imports `nix/workspace.nix` from the pinned kit input instead of `.scions/`, so the dev
  shell and checks exist before the first graft, and `.envrc` is a plain `use flake`.
- `knowledge-base.yaml` `paths` and `rules` move to the new folders; the write rules can express "create, never
  modify" for `records/**`.

## Conformance changes

New deliberate deviations from the meta-KB:

- **Linking:** root-anchored links do not render on Git hosts, whose `/` is the repository root. The meta-KB
  linking policy favours Git-host browsing; this kit favours a vault-native, move-stable form.
- **Provenance:** inside the bundle, `sources` frontmatter and footnotes replace the `## Sources` section.

## Upgrading (outline)

A release would ship steps an agent can apply: move folders to the new layout; add `type` to every note; convert
links to the root-anchored form; replace folder READMEs with `index.md`; flatten session folders; move
`.obsidian/`; add `.okfignore`; reopen the vault at `notebook/`. A conversion script in the kit is likely worth it.

## Open questions

- Which checker implements conformance and link classes.
- Where index generation lives: a kit tool, or each workspace's own code.
- Workspaces that cannot install Obsidian community plugins type root-anchored links by hand. Is that acceptable,
  or should such workspaces use relative links?
- How the kit tracks OKF versions after v0.2.

## Sources

- [OKF v0.2 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
- [OKF issue #58: excluding non-concept Markdown files](https://github.com/GoogleCloudPlatform/open-knowledge-format/issues/58)
- [OKF Wiki plugin](https://github.com/ysasiwat/obsidian-okf-wiki)
- [Better Markdown Links plugin](https://github.com/mnaoumov/obsidian-better-markdown-links)
- [Meta-KB linking policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.0.1/docs/policies/linking.md)
- [Meta-KB temporal layers policy](https://github.com/danielnaab/meta-knowledge-base/blob/v1.0.1/docs/policies/temporal-layers.md)
- [Layout and layers](layout.md)
