from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from django.conf import settings
from openai import OpenAI

from ai.providers.base import (
    LLMProvider,
    TranscriptionProvider,
    TranscriptionResult,
    TranscriptSegmentResult,
)

logger = logging.getLogger(__name__)


def get_openai_client() -> OpenAI:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=settings.OPENAI_API_KEY)


class OpenAITranscribeDiarizeProvider(TranscriptionProvider):
    """Combined STT + diarization via gpt-4o-transcribe-diarize."""

    def __init__(self, client: OpenAI | None = None):
        self.client = client or get_openai_client()
        self.model = settings.OPENAI_TRANSCRIBE_MODEL

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        path = Path(audio_path)
        with path.open("rb") as audio_file:
            kwargs: dict[str, Any] = {
                "model": self.model,
                "file": audio_file,
                "response_format": "diarized_json",
            }
            # Required for audio longer than 30s with diarize model.
            kwargs["chunking_strategy"] = "auto"
            try:
                result = self.client.audio.transcriptions.create(**kwargs)
            except TypeError:
                # Older SDKs may not accept chunking_strategy as kwarg.
                audio_file.seek(0)
                result = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    response_format="diarized_json",
                    extra_body={"chunking_strategy": "auto"},
                )

        raw = result.model_dump() if hasattr(result, "model_dump") else dict(result)
        segments_raw = raw.get("segments") or []
        segments: list[TranscriptSegmentResult] = []
        for seg in segments_raw:
            text = (seg.get("text") or "").strip()
            if not text:
                continue
            speaker = seg.get("speaker") or seg.get("speaker_label") or "Speaker"
            segments.append(
                TranscriptSegmentResult(
                    speaker_label=str(speaker),
                    text=text,
                    start_time_seconds=_as_float(seg.get("start")),
                    end_time_seconds=_as_float(seg.get("end")),
                )
            )

        if not segments and raw.get("text"):
            segments.append(
                TranscriptSegmentResult(
                    speaker_label="Speaker",
                    text=str(raw["text"]).strip(),
                )
            )

        duration = _as_float(raw.get("duration"))
        return TranscriptionResult(segments=segments, raw=raw, duration_seconds=duration)


class OpenAILLMProvider(LLMProvider):
    def __init__(self, client: OpenAI | None = None):
        self.client = client or get_openai_client()
        self.model = settings.OPENAI_LLM_MODEL

    def generate_structured(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema.get("name", "extraction"),
                    "strict": True,
                    "schema": schema["schema"],
                },
            },
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract structured call intelligence. "
                        "Only use facts grounded in the provided transcript. "
                        "Every claim must include evidence_line_numbers from the transcript. "
                        "Never invent quotations."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)

    def verify_entailment(self, claim: str, evidence: str) -> dict[str, Any]:
        schema = {
            "name": "entailment",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["SUPPORTED", "PARTIAL", "UNSUPPORTED"],
                    },
                    "score": {"type": "number"},
                    "reason": {"type": "string"},
                },
                "required": ["status", "score", "reason"],
            },
        }
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "entailment",
                    "strict": True,
                    "schema": schema["schema"],
                },
            },
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Decide whether the evidence supports the claim. "
                        "SUPPORTED if clearly supported, PARTIAL if incomplete, "
                        "UNSUPPORTED if not supported."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Claim: {claim}\n\nEvidence:\n{evidence}",
                },
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)


class MockTranscriptionProvider(TranscriptionProvider):
    """Offline fixture provider for tests and demos without OpenAI."""

    def __init__(self, segments: list[TranscriptSegmentResult] | None = None):
        self._segments = segments or [
            TranscriptSegmentResult("Agent", "Hello, this is Marcus from collections."),
            TranscriptSegmentResult(
                "Consumer", "Please stop calling. I will speak with my attorney."
            ),
            TranscriptSegmentResult(
                "Agent", "I will follow up with my supervisor by Friday."
            ),
            TranscriptSegmentResult(
                "Consumer", "Any settlement needs supervisor approval."
            ),
        ]

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        return TranscriptionResult(
            segments=list(self._segments),
            raw={"provider": "mock", "audio_path": audio_path},
            duration_seconds=60.0,
        )


class MockLLMProvider(LLMProvider):
    def generate_structured(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {
            "tag": "Debt collection follow-up",
            "summary": "Consumer requested cease contact and mentioned an attorney; agent will escalate.",
            "decisions": [
                {
                    "text": "Agent will escalate to supervisor.",
                    "confidence": 0.9,
                    "evidence_line_numbers": [3],
                }
            ],
            "action_items": [
                {
                    "task": "Follow up with supervisor",
                    "owner_name": "Marcus",
                    "owner_type": "agent",
                    "due_phrase": "Friday",
                    "confidence": 0.88,
                    "evidence_line_numbers": [3],
                }
            ],
            "blockers": [
                {
                    "text": "Settlement requires supervisor approval",
                    "impact": "Cannot finalize settlement on this call",
                    "confidence": 0.85,
                    "evidence_line_numbers": [4],
                }
            ],
            "compliance_candidates": [
                {
                    "category": "CEASE_AND_DESIST",
                    "observation": "Consumer asked to stop calling",
                    "severity": "RED",
                    "confidence": 0.92,
                    "evidence_line_numbers": [2],
                },
                {
                    "category": "LEGAL_MENTION",
                    "observation": "Consumer mentioned attorney",
                    "severity": "YELLOW",
                    "confidence": 0.9,
                    "evidence_line_numbers": [2],
                },
            ],
            "review_candidates": [
                {
                    "category": "CEASE_AND_DESIST",
                    "reason": "High-risk contact request needs human confirmation",
                    "severity": "RED",
                    "confidence": 0.92,
                    "evidence_line_numbers": [2],
                }
            ],
        }

    def verify_entailment(self, claim: str, evidence: str) -> dict[str, Any]:
        claim_l = claim.lower()
        evidence_l = evidence.lower()
        if any(tok in evidence_l for tok in claim_l.split()[:3]):
            return {"status": "SUPPORTED", "score": 0.9, "reason": "Evidence matches claim."}
        return {
            "status": "UNSUPPORTED",
            "score": 0.2,
            "reason": "Evidence does not support claim.",
        }


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
