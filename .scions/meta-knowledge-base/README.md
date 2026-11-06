# meta-knowledge-base

Operating instructions for evolving knowledge bases with human and agent collaboration.

## What this system standardizes

This system does **not** mandate document taxonomies. It standardizes:

- **Entrypoints**: where humans and agents begin
- **Authority**: what counts as canonical truth
- **Provenance**: how to ground important claims in sources
- **Lifecycle**: draft → working → stable → deprecated
- **Strategy**: how to choose an organization approach and evolve it with evidence
- **Linking**: how to keep browser navigation intuitive
- **Temporal layers**: organizing ephemeral, tracking, and durable knowledge
- **KB dependencies**: managing cross-repository knowledge relationships
- **Evolution triggers**: evidence-based approach to adding complexity
- **Generated content**: when and how to automate documentation
- **Multi-agent coordination**: patterns for specialized agent collaboration

## Core Policies

Essential patterns for all knowledge bases:

- [Authority](docs/policies/authority.md) - What counts as canonical truth
- [Provenance](docs/policies/provenance.md) - Grounding claims in sources
- [Lifecycle](docs/policies/lifecycle.md) - Document status progression
- [Linking](docs/policies/linking.md) - Navigation and references
- [Intent-revealing structure](docs/policies/intent-revealing-structure.md) - File and directory naming
- [Write boundaries](docs/policies/writes.md) - Safe agent editing zones
- [Style](docs/policies/style.md) - Plain language and structure

## Extended Policies

For evolving and complex knowledge bases:

- [Temporal layers](docs/policies/temporal-layers.md) - Organizing ephemeral, tracking, and durable knowledge
- [Generated content](docs/policies/generated-content.md) - When to automate documentation

## Organization Strategies

Choose your approach:

- [Knowledge organization strategies](docs/strategies/README.md)
  - Handbook (curated onboarding)
  - Atomic notes + maps (research/exploration)
  - Source-first synthesis (auditability)
  - Metadata + generated views (scale)

## Playbooks

Step-by-step guidance:

- [Choose a strategy](docs/playbooks/choose-strategy.md) - Initial organization decisions
- [Evolve a knowledge base](docs/playbooks/evolve-kb.md) - Evidence-based evolution
- [Evolve a UI](docs/playbooks/evolve-ui.md) - Safe UI introduction
- [Manage KB dependencies](docs/playbooks/manage-kb-dependencies.md) - Cross-repository coordination
- [Track spec-impl relationship](docs/playbooks/track-spec-impl-relationship.md) - Specification-to-implementation tracking
- [Agent workflow](docs/playbooks/agent-workflow.md) - Plan → Patch → Verify pattern
- [Multi-agent coordination](docs/playbooks/multi-agent-coordination.md) - Specialized agent collaboration

## Quick Start

### For a new knowledge base

1. Create `knowledge-base.yaml` with entrypoints
2. Add `README.md` and optional `AGENTS.md`
3. Evolve based on pain (see [Evolve KB playbook](docs/playbooks/evolve-kb.md))

### For an evolving knowledge base

1. Review [Evolution triggers](docs/playbooks/evolve-kb.md#evidence-based-evolution-triggers)
2. Add what you need based on observed pain
3. Start with low-cost moves (entrypoints, lifecycle markers)
4. Iterate based on evidence

### For multi-repository projects

1. Separate specs from implementation if needed (see [KB dependencies](docs/playbooks/manage-kb-dependencies.md))
2. Declare relationship types in knowledge-base.yaml
3. Establish sync policies
4. Track drift explicitly

### For agent-augmented development

1. Define human and agent entrypoints
2. Set write boundaries
3. Use Plan → Patch → Verify pattern (see [Agent workflow](docs/playbooks/agent-workflow.md))
4. Consider multi-agent patterns if you have role separation (see [Multi-agent coordination](docs/playbooks/multi-agent-coordination.md))

## Philosophy

**Minimal intervention:** Only standardize operations, not structure

**Evidence-driven:** Evolve based on observed pain, not speculation

**Support evolution:** Knowledge bases that grow and adapt over time

**Agent-friendly:** Clear entrypoints, boundaries, and coordination patterns

**Human-centered:** Git is source of truth, UIs are views

## Examples

See [examples/](examples/) for complete knowledge bases demonstrating each strategy.

## Using this in your repository

Add a `knowledge-base.yaml` at your repo root:

```yaml
apiVersion: meta-kb/v1
name: your-project

entrypoints:
  human: README.md
  agent: AGENTS.md

imports:
  - kind: local
    path: ../meta-knowledge-base
```

## Navigation

- [Strategies](docs/strategies/README.md)
- [Policies](docs/policies/README.md)
- [Playbooks](docs/playbooks/README.md)
- [Examples](examples/README.md)
- [Adapters](adapters/claude-code/README.md)
