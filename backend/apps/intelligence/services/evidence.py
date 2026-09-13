from __future__ import annotations

from decimal import Decimal

from apps.calls.choices import VerificationStatus
from apps.intelligence.models import EvidenceVerification
from apps.transcripts.models import TranscriptSegment
from ai.providers import get_llm_provider


def lines_for_numbers(call_id, line_numbers: list[int]) -> list[TranscriptSegment]:
    return list(
        TranscriptSegment.objects.filter(call_id=call_id, line_number__in=line_numbers).order_by(
            "line_number"
        )
    )


def evidence_text(segments: list[TranscriptSegment]) -> str:
    return "\n".join(f"{s.line_number}: {s.speaker_label}: {s.text}" for s in segments)


def verify_claim(
    *,
    call,
    claim_type: str,
    claim_id,
    claim_text: str,
    evidence_line_numbers: list[int],
    use_llm: bool = True,
) -> dict:
    segments = lines_for_numbers(call.id, evidence_line_numbers)
    if not segments:
        status = VerificationStatus.UNSUPPORTED
        score = Decimal("0.0")
        reason = "No evidence lines found for cited line numbers."
    else:
        text = evidence_text(segments)
        if use_llm:
            result = get_llm_provider().verify_entailment(claim_text, text)
            status = result.get("status", VerificationStatus.REVIEW)
            if status not in VerificationStatus.values:
                status = VerificationStatus.REVIEW
            score = Decimal(str(result.get("score", 0.5)))
            reason = result.get("reason", "")
        else:
            # Deterministic fallback for tests
            claim_tokens = set(claim_text.lower().split())
            evidence_tokens = set(text.lower().split())
            overlap = len(claim_tokens & evidence_tokens)
            if overlap >= max(2, len(claim_tokens) // 3):
                status = VerificationStatus.SUPPORTED
                score = Decimal("0.85")
                reason = "Keyword overlap supports claim."
            else:
                status = VerificationStatus.UNSUPPORTED
                score = Decimal("0.2")
                reason = "Insufficient evidence overlap."

    EvidenceVerification.objects.create(
        call=call,
        claim_type=claim_type,
        claim_id=claim_id,
        verification_status=status,
        score=score,
        verifier_reason=reason,
    )
    return {"status": status, "score": score, "reason": reason, "segments": segments}
