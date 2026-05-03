from __future__ import annotations

import re

RISK_MITIGATION_PATTERN = re.compile(
    r"\b(mitigation|mitigate|fallback|retry|reduce|avoid|monitor)\b",
    flags=re.IGNORECASE,
)
QA_RISK_SEVERITY_PATTERN = re.compile(
    r"\bseverity\s*:?\s*(?:`|\*\*)?(critical|high|medium|low)(?:`|\*\*)?\b|"
    r"\(`?(critical|high|medium|low)`?\)|"
    r"\b(critical|high|medium|low)\s+severity\b",
    flags=re.IGNORECASE,
)
QA_EVIDENCE_ID_PATTERN = re.compile(r"\bEV-\d+\b", flags=re.IGNORECASE)
QA_OWNER_PATTERN = re.compile(r"\bowner\b", flags=re.IGNORECASE)


def is_empty_risk_entry(risk_block: str) -> bool:
    normalized = re.sub(r"[`*_]", "", risk_block).strip().lower()
    normalized = normalized.strip(" .:-")
    return normalized in {
        "none",
        "none recorded",
        "no known issues",
        "no residual risks",
        "no residual risk remains",
    }


def is_risk_metadata_entry(risk_block: str) -> bool:
    first_line = next(
        (line.strip() for line in risk_block.splitlines() if line.strip()),
        "",
    )
    return bool(
        re.match(
            r"^(severity|mitigation|owner|ownership|disposition|description|evidence)\s*:",
            first_line,
            flags=re.IGNORECASE,
        )
    )


__all__ = [
    "QA_EVIDENCE_ID_PATTERN",
    "QA_OWNER_PATTERN",
    "QA_RISK_SEVERITY_PATTERN",
    "RISK_MITIGATION_PATTERN",
    "is_empty_risk_entry",
    "is_risk_metadata_entry",
]
