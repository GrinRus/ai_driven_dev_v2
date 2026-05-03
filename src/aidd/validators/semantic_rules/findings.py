from __future__ import annotations

from aidd.validators.models import SeverityLevel, ValidationFinding, ValidationIssueLocation


def validation_finding(
    *,
    code: str,
    message: str,
    severity: SeverityLevel = "high",
    location: ValidationIssueLocation | None = None,
) -> ValidationFinding:
    return ValidationFinding(
        code=code,
        message=message,
        severity=severity,
        location=location,
    )


__all__ = ["validation_finding"]
