# Security Policy

## Supported versions

AIDD is prerelease alpha software. Security fixes target the latest published prerelease and
the `main` branch. Older prereleases may be superseded without backports.

## Reporting a vulnerability

Do not open a public issue for vulnerabilities or reports that contain secrets, private
repository contents, raw provider logs, tokens, or credential material.

Use GitHub private vulnerability reporting when it is enabled for the repository. If private
reporting is not available, contact the maintainer through the repository owner profile and
include only non-sensitive reproduction metadata until a private channel is established.

Useful report details:

- affected AIDD version or commit;
- installation path (`pipx`, `uv tool`, or source checkout);
- runtime id and runtime command shape, with secrets redacted;
- minimal reproduction steps;
- whether `.aidd/` artifacts or raw runtime logs contain sensitive data.

## Security model

AIDD launches external runtime CLIs against local repositories. Runtime credentials,
provider authentication, and permission prompts are managed outside AIDD by those runtimes.
Operators should run alpha workflows from a disposable branch, sandboxed checkout, or other
controlled workspace.

The `.aidd/` workspace can contain raw runtime logs, prompts, repository context, questions,
answers, and validation evidence. Treat `.aidd/` as sensitive operator state.

## Owner/admin checklist

Repository owners should keep these GitHub settings enabled:

- dependency graph;
- Dependabot alerts and security updates;
- secret scanning and push protection;
- code scanning;
- private vulnerability reporting;
- branch protection or repository rulesets with required CI checks;
- security workflow checks after those workflows are present on the default branch.
