---
status: working
---

# Local conventions

This workspace follows the pinned [notebook-kit](../.scions/notebook-kit/docs/README.md) kit and
[knowledge-base-kit](../.scions/knowledge-base-kit/README.md). This file states only local rules and differences.
Local rules take precedence. [Boundaries](boundaries.md) are separate and override everything.

## Local rules

_None yet. Add a rule here only when the kit's default does not fit, with the reason._

## knowledge-base-kit conformance

The seven core policies bind. Application is the kit's default
([conformance](../.scions/notebook-kit/docs/conformance.md#default-application)) except as listed.

- **Deliberate deviations:** the kit's two (task status vocabulary, `YYYY-MM` folders).
  Add local deviations here with a reason.
- **Added locally:** [boundaries](boundaries.md) and anything under Local rules.
- **Verification:** `just check`: check-kb (links, status, provenance, OKF conformance), check-tasks,
  `index --check`, and check-obsidian; the pre-commit hook runs check-kb.
  Write boundaries and `askFirst` approvals are checked by hand.
- **Ask-first changes** need <<OWNER>>'s approval for the specific change, recorded in the task, session, daily
  note, or commit message.

## Sources

- [Kit conformance guide](../.scions/notebook-kit/docs/conformance.md)
- [KB configuration](../knowledge-base.yaml)
