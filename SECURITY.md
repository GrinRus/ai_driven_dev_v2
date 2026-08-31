# Security Policy

## Supported versions

AIDD is prerelease alpha software. Security fixes target the latest published prerelease and
the `main` branch. Older prereleases may be superseded without backports.

## Reporting a vulnerability

Do not open a public issue for vulnerabilities or reports that contain secrets, private
repository contents, raw provider logs, tokens, or credential material.

Use [GitHub private vulnerability reporting](https://github.com/GrinRus/ai_driven_dev_v2/security/advisories/new).
This sends the report to the maintainers without opening a public issue. If GitHub does not let
you submit the form, do not publish the details; open a redacted
[support question](https://github.com/GrinRus/ai_driven_dev_v2/issues/new?template=operator_support.yml)
asking the maintainers to restore the private reporting channel.

Useful report details:

- affected AIDD version or commit;
- installation path (`pipx`, `uv tool`, or source checkout);
- runtime id and runtime command shape, with secrets redacted;
- minimal reproduction steps;
- whether `.aidd/` artifacts or raw runtime logs contain sensitive data.

## Response expectations

The maintainers aim to acknowledge a private report within 7 calendar days and provide an
initial assessment or status update within 14 calendar days. These are best-effort targets for
an alpha project, not a guaranteed remediation deadline.

Please keep the report private while the issue is investigated. The maintainers will coordinate
disclosure timing with the reporter after a fix or mitigation is available, and will publish an
advisory when users need to take action.

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
