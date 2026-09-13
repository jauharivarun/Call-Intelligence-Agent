import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.calls.choices import CallDomain, CallStatus
from apps.calls.models import Call
from apps.calls.services.processing import process_call
from apps.transcripts.models import TranscriptSegment


@pytest.fixture
def api_client(db):
    user = User.objects.create_user(username="tester", password="pass1234")
    token = Token.objects.create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client, user


@pytest.mark.django_db
def test_health_public():
    client = APIClient()
    res = client.get("/api/health/")
    assert res.status_code == 200
    assert res.data["status"] == "ok"


@pytest.mark.django_db
def test_auth_me(api_client):
    client, user = api_client
    res = client.get("/api/auth/me/")
    assert res.status_code == 200
    assert res.data["username"] == user.username


@pytest.mark.django_db
def test_viewer_can_see_others_calls_but_not_delete():
    admin = User.objects.create_user(username="owner_admin", password="pass1234", is_staff=True)
    viewer = User.objects.create_user(username="viewer_see", password="pass1234", is_staff=False)
    call = Call.objects.create(
        user=admin,
        title="Admin upload",
        domain=CallDomain.DEBT_COLLECTION,
        call_date="2026-07-01",
        recording_path="/tmp/x.mp3",
        status=CallStatus.COMPLETED,
    )
    viewer_client = APIClient()
    viewer_client.credentials(
        HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=viewer).key}"
    )
    assert viewer_client.get(f"/api/calls/{call.id}/").status_code == 200
    listed = viewer_client.get("/api/calls/")
    assert listed.status_code == 200
    assert any(row["id"] == str(call.id) for row in listed.data)
    assert viewer_client.delete(f"/api/calls/{call.id}/").status_code == 403
    assert Call.objects.filter(pk=call.id).exists()


@pytest.mark.django_db
def test_pipeline_with_mock_providers(tmp_path, settings):
    settings.OPENAI_API_KEY = "sk-your-key-here"
    user = User.objects.create_user(username="pipe", password="pass1234")
    audio = tmp_path / "sample.wav"
    audio.write_bytes(b"RIFF....WAVEfmt ")
    call = Call.objects.create(
        user=user,
        title="Mock call",
        domain=CallDomain.DEBT_COLLECTION,
        call_date="2026-07-01",
        recording_path=str(audio),
        status=CallStatus.UPLOADED,
    )
    process_call(str(call.id), use_llm_verify=False)
    call.refresh_from_db()
    assert call.status == CallStatus.COMPLETED
    assert TranscriptSegment.objects.filter(call=call).count() >= 3
    assert hasattr(call, "analysis")
    assert call.analysis.action_items.count() >= 1
    assert call.review_items.count() >= 1


@pytest.mark.django_db
def test_search_transcripts(api_client):
    client, user = api_client
    call = Call.objects.create(
        user=user,
        title="Searchable",
        domain=CallDomain.DEBT_COLLECTION,
        call_date="2026-07-01",
        recording_path="/tmp/x.mp3",
        status=CallStatus.COMPLETED,
    )
    TranscriptSegment.objects.create(
        call=call,
        line_number=1,
        speaker_label="Consumer",
        text="Please stop calling me.",
    )
    res = client.get("/api/search/transcripts/?q=stop calling")
    assert res.status_code == 200
    assert res.data["count"] == 1


@pytest.mark.django_db
def test_me_includes_role():
    admin = User.objects.create_user(username="admin1", password="pass1234", is_staff=True)
    viewer = User.objects.create_user(username="viewer1", password="pass1234", is_staff=False)
    admin_client = APIClient()
    admin_client.credentials(
        HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=admin).key}"
    )
    viewer_client = APIClient()
    viewer_client.credentials(
        HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=viewer).key}"
    )
    assert admin_client.get("/api/auth/me/").data["role"] == "admin"
    assert viewer_client.get("/api/auth/me/").data["role"] == "viewer"


@pytest.mark.django_db
def test_only_admin_can_delete_call():
    admin = User.objects.create_user(username="admin2", password="pass1234", is_staff=True)
    viewer = User.objects.create_user(username="viewer2", password="pass1234", is_staff=False)
    call = Call.objects.create(
        user=viewer,
        title="To delete",
        domain=CallDomain.DEBT_COLLECTION,
        call_date="2026-07-01",
        recording_path="/tmp/y.mp3",
        status=CallStatus.COMPLETED,
    )

    viewer_client = APIClient()
    viewer_client.credentials(
        HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=viewer).key}"
    )
    forbidden = viewer_client.delete(f"/api/calls/{call.id}/")
    assert forbidden.status_code == 403
    assert Call.objects.filter(pk=call.id).exists()

    admin_client = APIClient()
    admin_client.credentials(
        HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=admin).key}"
    )
    deleted = admin_client.delete(f"/api/calls/{call.id}/")
    assert deleted.status_code == 204
    assert not Call.objects.filter(pk=call.id).exists()


@pytest.mark.django_db
def test_viewer_can_view_analysis_but_not_reanalyze():
    viewer = User.objects.create_user(username="viewer3", password="pass1234", is_staff=False)
    call = Call.objects.create(
        user=viewer,
        title="View only",
        domain=CallDomain.DEBT_COLLECTION,
        call_date="2026-07-01",
        recording_path="/tmp/z.mp3",
        status=CallStatus.COMPLETED,
    )
    from apps.intelligence.models import Analysis

    Analysis.objects.create(call=call, tag="t", summary="s", analysis_version="v1")
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=viewer).key}"
    )
    assert client.get(f"/api/calls/{call.id}/analysis/").status_code == 200
    assert client.post(f"/api/calls/{call.id}/reanalyze/").status_code == 403


@pytest.mark.django_db
def test_review_moves_to_resolved_and_allows_edit_or_reopen():
    from apps.calls.choices import ReviewStatus, Severity
    from apps.intelligence.models import Analysis
    from apps.reviews.models import ReviewItem

    user = User.objects.create_user(username="reviewer1", password="pass1234", is_staff=True)
    call = Call.objects.create(
        user=user,
        title="Review flow",
        domain=CallDomain.DEBT_COLLECTION,
        call_date="2026-07-01",
        recording_path="/tmp/r.mp3",
        status=CallStatus.COMPLETED,
    )
    analysis = Analysis.objects.create(call=call, tag="t", summary="s", analysis_version="v1")
    item = ReviewItem.objects.create(
        call=call,
        analysis=analysis,
        category="CEASE_AND_DESIST",
        reason="Check",
        severity=Severity.RED,
        status=ReviewStatus.OPEN,
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=user).key}")

    first = client.post(
        f"/api/reviews/{item.id}/decision/",
        {"decision": "ESCALATED", "note": "Needs legal"},
        format="json",
    )
    assert first.status_code == 200
    assert first.data["status"] == "ESCALATED"
    assert first.data["is_resolved"] is True
    assert first.data["reviewer_username"] == "reviewer1"

    open_list = client.get("/api/reviews/?status=OPEN")
    assert all(row["id"] != str(item.id) for row in open_list.data)

    resolved = client.get("/api/reviews/?status=RESOLVED")
    assert any(row["id"] == str(item.id) and row["status"] == "ESCALATED" for row in resolved.data)

    edited = client.post(
        f"/api/reviews/{item.id}/decision/",
        {"decision": "APPROVED", "note": "Corrected accidental escalate"},
        format="json",
    )
    assert edited.status_code == 200
    assert edited.data["status"] == "APPROVED"
    assert edited.data["reviewer_note"] == "Corrected accidental escalate"
    assert edited.data["is_resolved"] is True

    reopened = client.post(
        f"/api/reviews/{item.id}/decision/",
        {"decision": "OPEN", "note": "Send back to queue"},
        format="json",
    )
    assert reopened.status_code == 200
    assert reopened.data["status"] == "OPEN"
    assert reopened.data["is_resolved"] is False
    assert reopened.data["reviewed_at"] is None
    assert reopened.data["reviewer_username"] is None

    open_again = client.get("/api/reviews/?status=OPEN")
    assert any(row["id"] == str(item.id) for row in open_again.data)
