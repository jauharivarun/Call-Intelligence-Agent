from pathlib import Path
import mimetypes

from django.conf import settings
from django.core.files.storage import default_storage
from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminRole, is_admin_user
from apps.calls.choices import CallStatus
from apps.calls.models import Call
from apps.calls.serializers import (
    AnalysisSerializer,
    CallDetailSerializer,
    CallListSerializer,
    CallUploadSerializer,
    SentimentSerializer,
    TranscriptSegmentSerializer,
)
from apps.calls.tasks import process_call_task
from apps.intelligence.models import Analysis, SentimentAnalysis


def _accessible_calls(user):
    """All authenticated users can list/view calls; only admins can delete."""
    return Call.objects.all()


def _delete_call_and_recording(call: Call) -> None:
    recording_path = call.recording_path
    call_id = call.id
    call.delete()
    if recording_path:
        media_root = Path(settings.MEDIA_ROOT)
        try:
            path = Path(recording_path)
            if path.is_file():
                # Prefer storage delete when path is under MEDIA_ROOT.
                try:
                    relative = path.relative_to(media_root)
                    default_storage.delete(str(relative))
                except ValueError:
                    path.unlink(missing_ok=True)
        except OSError:
            pass
    # Also try storage key used at upload time.
    for ext in settings.ALLOWED_AUDIO_EXTENSIONS:
        default_storage.delete(f"recordings/{call_id}{ext}")


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def call_list_create(request):
    if request.method == "GET":
        qs = _accessible_calls(request.user)
        return Response(CallListSerializer(qs, many=True).data)

    serializer = CallUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    recording = serializer.validated_data["recording"]
    ext = Path(recording.name).suffix.lower()
    if ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
        return Response(
            {"detail": f"Unsupported file type '{ext}'."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if recording.size and recording.size > settings.MAX_UPLOAD_SIZE_BYTES:
        return Response(
            {"detail": "File exceeds 25MB limit."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    content_type = getattr(recording, "content_type", "") or ""
    if (
        content_type
        and content_type not in settings.ALLOWED_AUDIO_CONTENT_TYPES
        and not content_type.startswith("audio/")
    ):
        return Response(
            {"detail": f"Unsupported content type '{content_type}'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    call = Call(
        user=request.user,
        title=serializer.validated_data.get("title") or recording.name,
        domain=serializer.validated_data["domain"],
        call_date=serializer.validated_data["call_date"],
        recording_path="",
        status=CallStatus.UPLOADED,
    )
    call.save()

    relative_path = f"recordings/{call.id}{ext}"
    saved_path = default_storage.save(relative_path, recording)
    absolute = str(Path(settings.MEDIA_ROOT) / saved_path)
    call.recording_path = absolute
    call.status = CallStatus.PROCESSING
    call.save(update_fields=["recording_path", "status", "updated_at"])

    try:
        process_call_task.delay(str(call.id))
    except Exception:
        from apps.calls.services.processing import process_call

        process_call(str(call.id))

    return Response(CallDetailSerializer(call).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def call_detail(request, call_id):
    try:
        call = _accessible_calls(request.user).prefetch_related("jobs").get(pk=call_id)
    except Call.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "DELETE":
        if not is_admin_user(request.user):
            return Response(
                {"detail": "Only admins can delete analysis/calls."},
                status=status.HTTP_403_FORBIDDEN,
            )
        _delete_call_and_recording(call)
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(CallDetailSerializer(call).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def call_transcript(request, call_id):
    try:
        call = _accessible_calls(request.user).get(pk=call_id)
    except Call.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    segments = call.segments.all()
    return Response(TranscriptSegmentSerializer(segments, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def call_analysis(request, call_id):
    """Viewers and admins may view analysis; mutation is not allowed here."""
    try:
        call = _accessible_calls(request.user).get(pk=call_id)
    except Call.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    try:
        analysis = Analysis.objects.prefetch_related(
            "decisions__evidence",
            "action_items__evidence",
            "blockers__evidence",
            "compliance_observations__evidence",
            "review_items__evidence",
        ).get(call=call)
    except Analysis.DoesNotExist:
        return Response(
            {"detail": "Analysis not ready."},
            status=status.HTTP_404_NOT_FOUND,
        )
    data = AnalysisSerializer(analysis).data
    try:
        data["sentiment"] = SentimentSerializer(call.sentiment).data
    except SentimentAnalysis.DoesNotExist:
        data["sentiment"] = None
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def call_recording(request, call_id):
    """Stream the stored recording for in-app playback (authenticated)."""
    try:
        call = _accessible_calls(request.user).get(pk=call_id)
    except Call.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    path = Path(call.recording_path) if call.recording_path else None
    if not path or not path.is_file():
        for ext in settings.ALLOWED_AUDIO_EXTENSIONS:
            candidate = Path(settings.MEDIA_ROOT) / f"recordings/{call.id}{ext}"
            if candidate.is_file():
                path = candidate
                break
    if not path or not path.is_file():
        return Response(
            {"detail": "Recording file not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    content_type, _ = mimetypes.guess_type(str(path))
    if not content_type or not content_type.startswith(("audio/", "video/")):
        suffix = path.suffix.lower()
        content_type = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".ogg": "audio/ogg",
            ".webm": "audio/webm",
            ".flac": "audio/flac",
            ".mp4": "audio/mp4",
        }.get(suffix, "application/octet-stream")

    response = FileResponse(path.open("rb"), content_type=content_type)
    response["Content-Disposition"] = f'inline; filename="{path.name}"'
    response["Accept-Ranges"] = "bytes"
    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminRole])
def call_reanalyze(request, call_id):
    try:
        call = _accessible_calls(request.user).get(pk=call_id)
    except Call.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    call.status = CallStatus.PROCESSING
    call.error_message = ""
    call.save(update_fields=["status", "error_message", "updated_at"])
    try:
        process_call_task.delay(str(call.id))
    except Exception:
        from apps.calls.services.processing import process_call

        process_call(str(call.id))
    return Response(CallDetailSerializer(call).data)
