from __future__ import annotations

import re
from dataclasses import dataclass

from apps.calls.choices import ComplianceCategory, Severity


@dataclass
class ComplianceHit:
    category: str
    severity: str
    observation: str
    rationale: str
    confidence: float
    review_required: bool
    line_numbers: list[int]


RULES: list[dict] = [
    {
        "category": ComplianceCategory.CEASE_AND_DESIST,
        "severity": Severity.RED,
        "patterns": [
            r"stop calling",
            r"do not call",
            r"don't call",
            r"not to call",
            r"never (call|contact)",
            r"don't (bother|contact)",
            r"do not (bother|contact)",
            r"take me off",
            r"off (from |of )?your list",
            r"cease and desist",
            r"cease contact",
            r"remove me from",
        ],
        "observation": "Consumer requested contact cessation.",
        "review_required": True,
    },
    {
        "category": ComplianceCategory.LEGAL_MENTION,
        "severity": Severity.YELLOW,
        "patterns": [
            r"\battorney\b",
            r"\blawyer\b",
            r"\bsue\b",
            r"\bsuing\b",
            r"\blegal action\b",
            r"\bcounsel\b",
            r"contact my attorney",
        ],
        "observation": "Legal representation or legal action mentioned.",
        "review_required": True,
    },
    {
        "category": ComplianceCategory.BANKRUPTCY,
        "severity": Severity.RED,
        "patterns": [r"bankrupt", r"chapter\s*7", r"chapter\s*13"],
        "observation": "Bankruptcy language detected.",
        "review_required": True,
    },
    {
        "category": ComplianceCategory.WRONG_NUMBER,
        "severity": Severity.YELLOW,
        "patterns": [r"wrong number", r"wrong person", r"not (the|that) person"],
        "observation": "Possible wrong-party contact.",
        "review_required": True,
    },
    {
        "category": ComplianceCategory.CONSENT,
        "severity": Severity.YELLOW,
        "patterns": [r"recorded", r"recording", r"consent to record"],
        "observation": "Recording/consent language detected.",
        "review_required": True,
    },
    {
        "category": ComplianceCategory.SETTLEMENT_APPROVAL,
        "severity": Severity.YELLOW,
        "patterns": [
            r"supervisor approval",
            r"needs approval",
            r"cannot approve",
            r"settlement",
        ],
        "observation": "Settlement/approval constraint detected.",
        "review_required": True,
    },
]


def run_compliance_rules(segments) -> list[ComplianceHit]:
    hits: list[ComplianceHit] = []
    for rule in RULES:
        matched_lines: list[int] = []
        for seg in segments:
            text = seg.text.lower()
            if any(re.search(p, text) for p in rule["patterns"]):
                matched_lines.append(seg.line_number)
        if matched_lines:
            hits.append(
                ComplianceHit(
                    category=rule["category"],
                    severity=rule["severity"],
                    observation=rule["observation"],
                    rationale=f"Matched patterns: {', '.join(rule['patterns'][:3])}",
                    confidence=0.9,
                    review_required=rule["review_required"],
                    line_numbers=matched_lines,
                )
            )
    return hits
