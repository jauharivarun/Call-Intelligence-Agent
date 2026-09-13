from __future__ import annotations

import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from ai.providers import get_llm_provider, get_transcription_provider
from apps.calls.choices import (
    CallStatus,
    JobStage,
    JobStatus,
    OwnerType,
    ReviewStatus,
    Severity,
    VerificationStatus,
)
from apps.calls.models import Call, ProcessingJob
from apps.compliance.services.rules import run_compliance_rules
from apps.intelligence.models import (
    ActionItem,
    Analysis,
    Blocker,
    ComplianceObservation,
    Decision,
    SentimentAnalysis,
)
from apps.intelligence.services.dates import resolve_relative_date
from apps.intelligence.services.evidence import lines_for_numbers, verify_claim
from apps.intelligence.services.extraction import (
    EXTRACTION_SCHEMA,
    build_extraction_prompt,
)
from apps.reviews.models import ReviewItem
from apps.transcripts.models import TranscriptSegment

logger = logging.getLogger(__name__)


def _start_job(call: Call, stage: str) -> ProcessingJob:
    return ProcessingJob.objects.create(
        call=call,
        stage=stage,
        status=JobStatus.RUNNING,
        started_at=timezone.now(),
    )


def _finish_job(job: ProcessingJob, *, ok: bool = True, error: str = "", metadata=None):
    job.status = JobStatus.SUCCEEDED if ok else JobStatus.FAILED
    job.completed_at = timezone.now()
    job.error_message = error
    if metadata is not None:
        job.metadata = metadata
    job.save(update_fields=["status", "completed_at", "error_message", "metadata"])


def _fail_call(call: Call, message: str):
    call.status = CallStatus.FAILED
    call.error_message = message
    call.save(update_fields=["status", "error_message", "updated_at"])


def _map_speaker(label: str) -> str:
    raw = (label or "Speaker").strip()
    lowered = raw.lower()
    if lowered in {"a", "speaker_0", "speaker 0", "spk_0", "agent"}:
        return "Agent"
    if lowered in {"b", "speaker_1", "speaker 1", "spk_1", "consumer", "customer"}:
        return "Consumer"
    if raw.startswith("Speaker") or raw.startswith("speaker"):
        return raw.replace("speaker", "Speaker")
    return raw


@transaction.atomic
def persist_transcript(call: Call, transcription) -> list[TranscriptSegment]:
    call.segments.all().delete()
    created: list[TranscriptSegment] = []
    for idx, seg in enumerate(transcription.segments, start=1):
        created.append(
            TranscriptSegment.objects.create(
                call=call,
                line_number=idx,
                speaker_label=_map_speaker(seg.speaker_label),
                start_time_seconds=seg.start_time_seconds,
                end_time_seconds=seg.end_time_seconds,
                text=seg.text.strip(),
            )
        )
    if transcription.duration_seconds:
        call.recording_duration_seconds = int(transcription.duration_seconds)
    call.provider_metadata = {
        **(call.provider_metadata or {}),
        "transcription": transcription.raw,
    }
    call.save(
        update_fields=["recording_duration_seconds", "provider_metadata", "updated_at"]
    )
    return created


def process_call(call_id: str, *, use_llm_verify: bool = True) -> None:
    try:
        call = Call.objects.get(pk=call_id)
    except Call.DoesNotExist:
        logger.error("Call %s not found", call_id)
        return

    try:
        call.status = CallStatus.PROCESSING
        call.error_message = ""
        call.save(update_fields=["status", "error_message", "updated_at"])

        # Stages 4–5: transcription + diarization (combined OpenAI call)
        call.status = CallStatus.TRANSCRIBING
        call.save(update_fields=["status", "updated_at"])
        job = _start_job(call, JobStage.TRANSCRIPTION)
        transcription = get_transcription_provider().transcribe(call.recording_path)
        _finish_job(job, metadata={"segment_count": len(transcription.segments)})

        call.status = CallStatus.DIARIZING
        call.save(update_fields=["status", "updated_at"])
        djob = _start_job(call, JobStage.DIARIZATION)
        segments = persist_transcript(call, transcription)
        _finish_job(djob, metadata={"lines": len(segments)})

        if not segments:
            raise RuntimeError("Transcription produced no segments.")

        # Stage 6: extraction
        call.status = CallStatus.ANALYZING
        call.save(update_fields=["status", "updated_at"])
        ejob = _start_job(call, JobStage.EXTRACTION)
        prompt = build_extraction_prompt(call=call, segments=segments)
        extraction = get_llm_provider().generate_structured(prompt, EXTRACTION_SCHEMA)
        if not isinstance(extraction, dict) or "summary" not in extraction:
            raise RuntimeError("Invalid extraction payload from LLM.")
        _finish_job(ejob)

        Analysis.objects.filter(call=call).delete()
        analysis = Analysis.objects.create(
            call=call,
            tag=extraction.get("tag") or "Untitled",
            summary=extraction.get("summary") or "",
            analysis_version="v1",
            raw_extraction=extraction,
        )

        # Stage 7–8: verify + dates
        call.status = CallStatus.VERIFYING
        call.save(update_fields=["status", "updated_at"])
        vjob = _start_job(call, JobStage.VERIFICATION)

        for item in extraction.get("decisions") or []:
            decision = Decision.objects.create(
                analysis=analysis,
                text=item.get("text", ""),
                confidence=_dec(item.get("confidence")),
            )
            result = verify_claim(
                call=call,
                claim_type="decision",
                claim_id=decision.id,
                claim_text=decision.text,
                evidence_line_numbers=item.get("evidence_line_numbers") or [],
                use_llm=use_llm_verify,
            )
            decision.verification_status = result["status"]
            decision.save(update_fields=["verification_status"])
            decision.evidence.set(result["segments"])
            if result["status"] in {
                VerificationStatus.UNSUPPORTED,
                VerificationStatus.PARTIAL,
                VerificationStatus.REVIEW,
            }:
                _create_review(
                    call,
                    analysis,
                    category="DECISION_VERIFICATION",
                    reason=result["reason"] or "Decision needs review",
                    severity=Severity.YELLOW,
                    confidence=result["score"],
                    segments=result["segments"],
                    source_type="decision",
                    source_id=decision.id,
                )

        for item in extraction.get("action_items") or []:
            due_phrase = item.get("due_phrase") or ""
            resolved = resolve_relative_date(call.call_date, due_phrase)
            owner_name = item.get("owner_name") or ""
            owner_type = item.get("owner_type") or OwnerType.UNKNOWN
            if owner_type not in OwnerType.values:
                owner_type = OwnerType.UNKNOWN
            review_required = (not owner_name) or resolved.status != "RESOLVED"
            action = ActionItem.objects.create(
                analysis=analysis,
                task=item.get("task", ""),
                owner_name=owner_name,
                owner_type=owner_type,
                due_date=resolved.normalized_date,
                original_due_phrase=resolved.original_phrase,
                confidence=_dec(item.get("confidence")),
                review_required=review_required,
            )
            result = verify_claim(
                call=call,
                claim_type="action_item",
                claim_id=action.id,
                claim_text=action.task,
                evidence_line_numbers=item.get("evidence_line_numbers") or [],
                use_llm=use_llm_verify,
            )
            action.verification_status = result["status"]
            if result["status"] != VerificationStatus.SUPPORTED:
                action.review_required = True
            action.save(update_fields=["verification_status", "review_required"])
            action.evidence.set(result["segments"])
            if action.review_required:
                _create_review(
                    call,
                    analysis,
                    category="ACTION_ITEM",
                    reason="Ambiguous owner/date or weak evidence",
                    severity=Severity.YELLOW,
                    confidence=action.confidence,
                    segments=result["segments"],
                    source_type="action_item",
                    source_id=action.id,
                )

        for item in extraction.get("blockers") or []:
            blocker = Blocker.objects.create(
                analysis=analysis,
                text=item.get("text", ""),
                impact=item.get("impact", ""),
                confidence=_dec(item.get("confidence")),
            )
            result = verify_claim(
                call=call,
                claim_type="blocker",
                claim_id=blocker.id,
                claim_text=blocker.text,
                evidence_line_numbers=item.get("evidence_line_numbers") or [],
                use_llm=use_llm_verify,
            )
            blocker.verification_status = result["status"]
            blocker.review_required = result["status"] != VerificationStatus.SUPPORTED
            blocker.save(update_fields=["verification_status", "review_required"])
            blocker.evidence.set(result["segments"])

        _finish_job(vjob)

        # Stage 9: compliance
        call.status = CallStatus.COMPLIANCE_CHECK
        call.save(update_fields=["status", "updated_at"])
        cjob = _start_job(call, JobStage.COMPLIANCE)

        # Merge rule hits + LLM candidates
        seen = set()
        for hit in run_compliance_rules(segments):
            key = (hit.category, tuple(hit.line_numbers))
            if key in seen:
                continue
            seen.add(key)
            obs = ComplianceObservation.objects.create(
                analysis=analysis,
                category=hit.category,
                severity=hit.severity,
                observation=hit.observation,
                rationale=hit.rationale,
                confidence=_dec(hit.confidence),
                review_required=hit.review_required,
            )
            obs.evidence.set(lines_for_numbers(call.id, hit.line_numbers))
            if hit.review_required:
                _create_review(
                    call,
                    analysis,
                    category=hit.category,
                    reason=hit.observation,
                    severity=hit.severity,
                    confidence=_dec(hit.confidence),
                    segments=list(obs.evidence.all()),
                    source_type="compliance",
                    source_id=obs.id,
                )

        for item in extraction.get("compliance_candidates") or []:
            category = item.get("category") or "OTHER"
            lines = item.get("evidence_line_numbers") or []
            key = (category, tuple(lines))
            if key in seen:
                continue
            seen.add(key)
            obs = ComplianceObservation.objects.create(
                analysis=analysis,
                category=category,
                severity=item.get("severity") or Severity.YELLOW,
                observation=item.get("observation", ""),
                confidence=_dec(item.get("confidence")),
                review_required=True,
            )
            segs = lines_for_numbers(call.id, lines)
            obs.evidence.set(segs)
            _create_review(
                call,
                analysis,
                category=category,
                reason=item.get("observation", "Compliance candidate"),
                severity=item.get("severity") or Severity.YELLOW,
                confidence=_dec(item.get("confidence")),
                segments=segs,
                source_type="compliance",
                source_id=obs.id,
            )

        for item in extraction.get("review_candidates") or []:
            segs = lines_for_numbers(call.id, item.get("evidence_line_numbers") or [])
            _create_review(
                call,
                analysis,
                category=item.get("category") or "GENERAL",
                reason=item.get("reason") or "Flagged for review",
                severity=item.get("severity") or Severity.YELLOW,
                confidence=_dec(item.get("confidence")),
                segments=segs,
            )

        _finish_job(cjob)

        # Bonus sentiment (heuristic + optional)
        sjob = _start_job(call, JobStage.SENTIMENT)
        _apply_sentiment(call, segments)
        _finish_job(sjob)

        fjob = _start_job(call, JobStage.FINALIZATION)
        confidences = [
            d.confidence
            for d in analysis.decisions.all()
            if d.confidence is not None
        ] + [
            a.confidence
            for a in analysis.action_items.all()
            if a.confidence is not None
        ]
        if confidences:
            analysis.overall_confidence = sum(confidences) / len(confidences)
            analysis.save(update_fields=["overall_confidence", "updated_at"])
        _finish_job(fjob)

        call.status = CallStatus.COMPLETED
        call.save(update_fields=["status", "updated_at"])
        logger.info("Call %s completed", call.id)
    except Exception as exc:
        logger.exception("Processing failed for call %s", call_id)
        _fail_call(call, str(exc))
        ProcessingJob.objects.filter(
            call=call, status=JobStatus.RUNNING
        ).update(
            status=JobStatus.FAILED,
            completed_at=timezone.now(),
            error_message=str(exc),
        )


def _create_review(
    call,
    analysis,
    *,
    category,
    reason,
    severity,
    confidence,
    segments,
    source_type="",
    source_id=None,
):
    item = ReviewItem.objects.create(
        call=call,
        analysis=analysis,
        category=category,
        reason=reason,
        severity=severity,
        confidence=confidence,
        status=ReviewStatus.OPEN,
        source_type=source_type,
        source_id=source_id,
    )
    if segments:
        item.evidence.set(segments)
    return item


def _apply_sentiment(call, segments):
    text = " ".join(s.text.lower() for s in segments)
    angry_words = ["angry", "furious", "hate", "ridiculous", "lawsuit", "sue"]
    profanity = ["damn", "hell", "crap", "shit", "fuck"]
    positive = ["thank", "thanks", "appreciate", "great", "good"]
    negative = ["angry", "upset", "frustrated", "wrong", "stop", "never"]

    angry = any(w in text for w in angry_words)
    prof = any(w in text for w in profanity)
    pos = sum(text.count(w) for w in positive)
    neg = sum(text.count(w) for w in negative)
    if angry or neg > pos + 1:
        overall = "NEGATIVE"
    elif pos > neg:
        overall = "POSITIVE"
    elif pos and neg:
        overall = "MIXED"
    else:
        overall = "NEUTRAL"

    SentimentAnalysis.objects.filter(call=call).delete()
    SentimentAnalysis.objects.create(
        call=call,
        overall_sentiment=overall,
        customer_sentiment="NEGATIVE" if angry else overall,
        agent_sentiment="NEUTRAL",
        profanity_detected=prof,
        angry_customer_detected=angry,
        confidence=Decimal("0.7"),
    )


def _dec(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None
