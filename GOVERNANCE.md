# Governance

AIDD currently uses a maintainer-led governance model. This document describes the project as it
operates today; it does not imply a committee or decision body that does not exist.

## Roles

### Maintainer

The active maintainer is listed in `.github/CODEOWNERS`. The maintainer:

- sets product and architecture direction;
- reviews and merges changes;
- manages releases, repository settings, and security reports;
- applies the Code of Conduct; and
- appoints additional maintainers when sustained contribution and project needs justify it.

### Contributors

Contributors may propose changes through issues and pull requests, participate in technical
discussion, review public changes, and take scoped work described in the roadmap or issue
tracker. A contribution does not grant repository or release privileges automatically.

## Decision process

Small, reversible changes are decided through normal pull-request review. Changes that affect
workflow semantics, architecture boundaries, document contracts, compatibility, security, or
release policy should begin with an issue or draft pull request that records the problem,
alternatives, and verification evidence.

The maintainer makes the final decision after considering product scope, compatibility,
operational risk, review feedback, and available evidence. Important decisions should remain
discoverable in the accepted pull request, architecture documentation, or an ADR when the
repository's ADR policy applies.

## Merge and release authority

Only a maintainer may merge into the default branch or publish a release. Required CI and
security checks must not be bypassed merely to complete a release. Release preparation and
evidence follow `docs/release-checklist.md`.

## Conflicts of interest

A maintainer or reviewer should disclose a material conflict that could affect a project
decision and avoid being the sole reviewer when another qualified reviewer is available. If no
independent reviewer is available, the limitation and decision rationale should be recorded
publicly unless security or privacy requires a private record.

## Security and conduct

Security reports follow `SECURITY.md`; conduct reports follow `CODE_OF_CONDUCT.md`. Sensitive
reports are handled privately and are not decided in a public issue.

## Continuity

Repository and release access should be expanded before project activity depends on an
unavailable maintainer. Adding or removing a maintainer requires updating this document,
`.github/CODEOWNERS`, package-publisher access, and the relevant security and release ownership
records in the same change or coordinated handoff.

Changes to this governance model use the same public issue and pull-request process as other
project changes.
