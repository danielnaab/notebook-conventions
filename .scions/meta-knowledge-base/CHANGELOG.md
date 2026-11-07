# Changelog

## [Unreleased]

## v1.1.0 - 2026-11-06

Additive: existing knowledge bases need no changes.

### Added
- **Provenance policy**: structured provenance. A `sources` frontmatter list, with footnotes keyed
  to its `id`s, counts the same as a `## Sources` section. It follows OKF v0.2 (§5.1).
- **Temporal layers policy**: two optional layers. Raw sources are kept as captured and never
  edited; historical records are dated, written once, and corrected with a dated correction.
  Neither carries a lifecycle `status`; the path marks them.

### Changed
- **Lifecycle policy**: raw sources and historical records carry no status.
- **Temporal layers policy**: the layers are one table; the content of the existing three is unchanged.
- **README**: the temporal layers summary names the two optional layers.

## v1.0.1 - 2026-11-03

### Changed
- **Manage KB dependencies playbook**: grafted copies live in `scions/` (graft 2.1's default),
  not `vendor/`.

## v1.0.0 - 2026-11-02

The first tagged release: what repos graft (https://github.com/danielnaab/graft/tree/v2).

### Changed
- **Exports**: `.gitattributes` defines what this repo exports: README, CHANGELOG, `docs/`,
  `adapters/` and `examples/`. `AGENTS.md`, `knowledge-base.yaml` and `notes/` are this repo's own.
- **Manage KB dependencies playbook**: take a dependency by grafting its export at a pinned
  commit into `vendor/`, link into the grafted copy, and provide one by declaring `export-ignore`
  rules and tagging releases.

### Removed
- `graft.yaml` here and in `examples/meal-planner/`: graft v1 is retired.

### Added
- **Intent-revealing structure policy** - File and directory naming that communicates purpose
  - Names reveal content without opening files
  - Hybrid names (number + intent) are acceptable
  - Addresses navigation pain at structural level
  - Policy condensed to 44 lines; detailed examples in exploration doc
  - Motivation and examples: `notes/2026-01-11-intent-revealing-structure.md` in this repo (not exported)
- **Track spec-impl relationship playbook** - Concrete patterns for specification-to-implementation tracking
  - CHANGELOG.md pattern for surfacing specification changes
  - Three pinning options (config file, build metadata, text file)
  - Reference format standard (`repo@commit`, `file.md#section`)
  - Sync workflow and anti-patterns

### Upgrading

For a repo that linked into this one before v1.0.0, through graft v1's `.graft/meta-knowledge-base/`
or GitHub `main`, as of the 2026-01-05 entry below. These moves happened in January 2026, before
the tag, and were not listed above.

1. Take it as a graft v2 scion pinned to a tag: in the repo's graft `flake.nix`,
   `inputs.meta-knowledge-base = { url = "github:danielnaab/meta-knowledge-base/v1.0.1"; flake = false; };`
   and `"meta-knowledge-base"` in `deps`; `nix run .#graft`; commit `flake.nix`, `flake.lock`
   and the grafted directory (`scions/` from graft 2.1, `vendor/` before). Remove the
   `meta-knowledge-base` entry from `graft.yaml` and its `.graft/meta-knowledge-base`.
2. Point links at the grafted copy, with these moves applied:
   - `policies/<name>.md` is `docs/policies/<name>.md` (all of them, `README.md` included).
   - `playbooks/<name>.md` is `docs/playbooks/<name>.md` (all of them, `README.md` included).
   - `docs/meta.md` is gone: its content is in `README.md`. `docs/README.md` is gone too; use
     `README.md`.
   - `meta.yaml` is `knowledge-base.yaml`, and it is not exported: drop imports of it.
   - `examples/meal-planner/docs/agents.md` is `examples/meal-planner/AGENTS.md`.
   - Removed with no replacement: `starter-kits/`, `examples/graft-project/`, `examples/minimal/`.
     The examples are now `api-catalog`, `meal-planner`, `research-notes` and `team-handbook`.
   - `AGENTS.md`, `knowledge-base.yaml` and `notes/` are not exported: link them on GitHub if you
     need them.

Done when `grep -rnE --exclude-dir=scions 'meta-knowledge-base/(policies|playbooks|starter-kits)/|docs/meta\.md|meta\.yaml|\.graft/meta-knowledge-base' .`
finds nothing and `nix flake check` passes.

## 2026-01-05 - Evolution for evolving knowledge bases

Based on analysis of Graft project evolution (53 commits, 84 files, 15k+ lines), added guidance for knowledge bases that evolve significantly.

### New policies

**Temporal layers** - three-tier organization:
- Ephemeral (notes/): scratch work, days to weeks
- Tracking (status/): implementation progress, weeks to months
- Durable (docs/): architecture and guides, indefinite

**Generated content** - when to automate:
- Pain triggers: synchronization, scale, consistency
- Three levels: indexes, extracted summaries, fully generated
- Mark generated content, separate concerns

### Enhanced playbooks

**Evolve KB** - evidence-based evolution:
- Five pain types with thresholds
- Minimal interventions before adding complexity
- Evolution moves ordered by cost
- Require 3+ examples before infrastructure

**Manage KB dependencies** - cross-repository coordination:
- Four relationship types: foundational, canonical-source, peer, generated-from
- Three sync policies: interpret, extend, reference
- Cross-repository provenance patterns

**Multi-agent coordination** (experimental):
- Three coordination patterns: sequential, concurrent, collaborative
- Communication protocols
- Best practices and anti-patterns

### Updated core

**meta.md** - new dimensions (2026):
- Temporal layers
- KB dependencies
- Evolution triggers
- Generated content
- Multi-agent coordination

**style.md** - enhanced:
- Conciseness targets (policies: 20-40 lines, playbooks: 50-100 lines)
- Context size management for LLM consumption

### Philosophy maintained

All additions:
- Optional, not mandatory
- Evidence-driven (from real project pain)
- Minimal intervention approach preserved
- Stable entrypoint unchanged (meta.md)

### Evidence base

- Graft project: 53 commits, 84 files, 15,768 lines
- Observed gaps: status/ lifecycle, cross-repo coordination, evolution triggers
- Real pain points, not theoretical needs
