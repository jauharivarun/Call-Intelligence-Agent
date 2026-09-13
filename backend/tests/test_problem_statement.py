"""Feature checks aligned to the problem statement (required + bonus)."""

from datetime import date
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.calls.choices import CallDomain, CallStatus
from apps.calls.models import Call
from apps.calls.services.processing import _apply_sentiment, process_call
from apps.compliance.services.rules import run_compliance_rules
from apps.intelligence.models import ActionItem, SentimentAnalysis
from apps.intelligence.services.dates import resolve_relative_date
from apps.transcripts.models import TranscriptSegment


def _seg(n: int, text: str):
    return SimpleNamespace(line_number=n, text=text)


# --- Required: relative dates from the problem-statement example ---


def test_problem_statement_date_examples():
    """Wednesday 1 July 2026 → Friday = 2026-07-03, 15th of next month = 2026-08-15."""
    meeting = date(2026, 7, 1)
    friday = resolve_relative_date(meeting, "Friday")
    assert friday.status == "RESOLVED"
    assert friday.normalized_date == date(2026, 7, 3)

    installment = resolve_relative_date(meeting, "15th of next month")
    assert installment.status == "RESOLVED"
    assert installment.normalized_date == date(2026, 8, 15)


# --- Required: domain compliance categories from the brief ---


def test_cease_and_desist_phrase_variants():
    phrases = [
        "Stop calling me",
        "Don't call me ever again",
        "Don't bother me",
        "Take me off from your list",
        "Don't contact me",
        "I told you guys not to call anymore",
    ]
    for i, phrase in enumerate(phrases, start=1):
        hits = run_compliance_rules([_seg(i, phrase)])
        assert any(h.category == "CEASE_AND_DESIST" for h in hits), phrase


def test_legal_and_bankruptcy_mentions():
    hits = run_compliance_rules(
        [
            _seg(1, "I will sue you"),
            _seg(2, "Contact my attorney"),
            _seg(3, "I am bankrupt"),
        ]
    )
    cats = {h.category for h in hits}
    assert "LEGAL_MENTION" in cats
    assert "BANKRUPTCY" in cats


def test_wrong_number_mention():
    hits = run_compliance_rules([_seg(1, "Sorry, you have the wrong number.")])
    assert any(h.category == "WRONG_NUMBER" for h in hits)


# --- Bonus: sentiment / profanity / angry customer ---


@pytest.mark.django_db
def test_sentiment_angry_and_profanity_signals():
    user = User.objects.create_user(username="sent1", password="pass1234")
    call = Call.objects.create(
        user=user,
        title="Angry call",
        domain=CallDomain.DEBT_COLLECTION,
        call_date="2026-07-01",
        recording_path="/tmp/s.mp3",
        status=CallStatus.COMPLETED,
    )
    segments = [
        TranscriptSegment.objects.create(
            call=call,
            line_number=1,
            speaker_label="Consumer",
            text="I am furious and this is damn ridiculous.",
        ),
        TranscriptSegment.objects.create(
            call=call,
            line_number=2,
            speaker_label="Agent",
            text="I understand.",
        ),
    ]
    _apply_sentiment(call, segments)
    sentiment = SentimentAnalysis.objects.get(call=call)
    assert sentiment.angry_customer_detected is True
    assert sentiment.profanity_detected is True
    assert sentiment.overall_sentiment in {"NEGATIVE", "MIXED"}


@pytest.mark.django_db
def test_sentiment_positive_path():
    user = User.objects.create_user(username="sent2", password="pass1234")
    call = Call.objects.create(
        user=user,
        title="Happy call",
        domain=CallDomain.CUSTOMER_SUPPORT,
        call_date="2026-07-01",
        recording_path="/tmp/s2.mp3",
        status=CallStatus.COMPLETED,
    )
    segments = [
        TranscriptSegment.objects.create(
            call=call,
            line_number=1,
            speaker_label="Consumer",
            text="Thank you, I really appreciate the great help.",
        )
    ]
    _apply_sentiment(call, segments)
    sentiment = SentimentAnalysis.objects.get(call=call)
    assert sentiment.overall_sentiment == "POSITIVE"
    assert sentiment.angry_customer_detected is False
    assert sentiment.profanity_detected is False


# --- Required end-to-end: structured notes + grounding + review + dates ---


@pytest.mark.django_db
def test_pipeline_produces_grounded_structured_outputs(tmp_path, settings):
    settings.OPENAI_API_KEY = "sk-your-key-here"
    user = User.objects.create_user(username="ps_pipe", password="pass1234")
    audio = tmp_path / "sample.wav"
    audio.write_bytes(b"RIFF....WAVEfmt ")
    call = Call.objects.create(
        user=user,
        title="Problem statement pipeline",
        domain=CallDomain.DEBT_COLLECTION,
        call_date="2026-07-01",
        recording_path=str(audio),
        status=CallStatus.UPLOADED,
    )
    process_call(str(call.id), use_llm_verify=False)
    call.refresh_from_db()

    assert call.status == CallStatus.COMPLETED
    analysis = call.analysis
    assert analysis.tag
    assert analysis.summary
    assert analysis.decisions.count() >= 1
    assert analysis.action_items.count() >= 1
    assert analysis.blockers.count() >= 1
    assert analysis.compliance_observations.count() >= 1
    assert call.review_items.count() >= 1

    # Line-level grounding: at least one action item links transcript evidence
    grounded = ActionItem.objects.filter(analysis=analysis).prefetch_related("evidence")
    assert any(item.evidence.exists() for item in grounded)

    # Relative due date from mock "Friday" with call_date 2026-07-01
    friday_item = grounded.filter(original_due_phrase__icontains="Friday").first()
    assert friday_item is not None
    assert str(friday_item.due_date) == "2026-07-03"

    # Bonus: sentiment row created
    assert SentimentAnalysis.objects.filter(call=call).exists()

    # API surfaces analysis with evidence for an authenticated user
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=user).key}")
    res = client.get(f"/api/calls/{call.id}/analysis/")
    assert res.status_code == 200
    assert res.data["tag"]
    assert res.data["action_items"]
    assert res.data["action_items"][0]["evidence"]
    assert "sentiment" in res.data
    assert res.data["review_items"]
