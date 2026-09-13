from __future__ import annotations

EXTRACTION_SCHEMA = {
    "name": "call_intelligence_extraction",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "tag": {"type": "string"},
            "summary": {"type": "string"},
            "decisions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "text": {"type": "string"},
                        "confidence": {"type": "number"},
                        "evidence_line_numbers": {
                            "type": "array",
                            "items": {"type": "integer"},
                        },
                    },
                    "required": ["text", "confidence", "evidence_line_numbers"],
                },
            },
            "action_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "task": {"type": "string"},
                        "owner_name": {"type": "string"},
                        "owner_type": {
                            "type": "string",
                            "enum": ["agent", "customer", "supervisor", "other", "unknown"],
                        },
                        "due_phrase": {"type": "string"},
                        "confidence": {"type": "number"},
                        "evidence_line_numbers": {
                            "type": "array",
                            "items": {"type": "integer"},
                        },
                    },
                    "required": [
                        "task",
                        "owner_name",
                        "owner_type",
                        "due_phrase",
                        "confidence",
                        "evidence_line_numbers",
                    ],
                },
            },
            "blockers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "text": {"type": "string"},
                        "impact": {"type": "string"},
                        "confidence": {"type": "number"},
                        "evidence_line_numbers": {
                            "type": "array",
                            "items": {"type": "integer"},
                        },
                    },
                    "required": ["text", "impact", "confidence", "evidence_line_numbers"],
                },
            },
            "compliance_candidates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": [
                                "CONSENT",
                                "CEASE_AND_DESIST",
                                "LEGAL_MENTION",
                                "BANKRUPTCY",
                                "WRONG_NUMBER",
                                "SETTLEMENT_APPROVAL",
                                "OTHER",
                            ],
                        },
                        "observation": {"type": "string"},
                        "severity": {"type": "string", "enum": ["GREEN", "YELLOW", "RED"]},
                        "confidence": {"type": "number"},
                        "evidence_line_numbers": {
                            "type": "array",
                            "items": {"type": "integer"},
                        },
                    },
                    "required": [
                        "category",
                        "observation",
                        "severity",
                        "confidence",
                        "evidence_line_numbers",
                    ],
                },
            },
            "review_candidates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "category": {"type": "string"},
                        "reason": {"type": "string"},
                        "severity": {"type": "string", "enum": ["GREEN", "YELLOW", "RED"]},
                        "confidence": {"type": "number"},
                        "evidence_line_numbers": {
                            "type": "array",
                            "items": {"type": "integer"},
                        },
                    },
                    "required": [
                        "category",
                        "reason",
                        "severity",
                        "confidence",
                        "evidence_line_numbers",
                    ],
                },
            },
        },
        "required": [
            "tag",
            "summary",
            "decisions",
            "action_items",
            "blockers",
            "compliance_candidates",
            "review_candidates",
        ],
    },
}


def build_extraction_prompt(*, call, segments) -> str:
    lines = "\n".join(
        f"{s.line_number}: {s.speaker_label}: {s.text}" for s in segments
    )
    return (
        f"Call ID: {call.id}\n"
        f"Call date: {call.call_date.isoformat()}\n"
        f"Domain: {call.domain}\n"
        f"Title: {call.title or 'N/A'}\n\n"
        f"Numbered transcript:\n{lines}\n\n"
        "Extract structured intelligence. "
        "evidence_line_numbers must reference the transcript line numbers above."
    )
