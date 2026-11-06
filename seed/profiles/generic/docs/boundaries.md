---
status: draft
---

# Boundaries

Fill this in before the workspace is used for real work. It states what agents and people may do here. The kit
supplies no boundaries because they depend on this workspace's context. Replace each `<<...>>` and delete this note.

## Scope

- Purpose of this workspace: <<WHAT_WORK_BELONGS_HERE>>.
- Work that does not belong here: <<WHAT_STAYS_ELSEWHERE>>.

## Data

- Data suitable for this workspace: <<SUITABLE_DATA>>.
- Data that must never enter it: <<EXCLUDED_DATA>>.
- Before transferring any data to a tool, provider, or destination, confirm it is suitable for that destination.
  If classification or authorization is unclear, stop and ask <<OWNER>>.

## Accounts, services, and tools

- Approved inference, accounts, and services: <<APPROVED_SERVICES>>.
- Not to be used or connected, even if reachable: <<EXCLUDED_SERVICES>>.
- Installing tools or widening permissions requires approval.

## Secrets

- Never read credential files, private keys, tokens, or secret values into context. Use references only.
- Do not dump the environment, shell traces, or auth and configuration files that may contain secrets.

## Actions needing explicit approval

- Publication, pushes, pull requests, external messages, deployment, cloud changes, and destructive cleanup.
- Project requirements do not override these boundaries.

## Sources

- [Agent instructions](../AGENTS.md)
- [Local conventions](conventions.md)
