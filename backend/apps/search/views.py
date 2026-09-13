from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.transcripts.models import TranscriptSegment


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_transcripts(request):
    q = (request.query_params.get("q") or "").strip()
    if not q:
        return Response({"detail": "Query parameter q is required."}, status=400)
    segments = (
        TranscriptSegment.objects.filter(text__icontains=q)
        .select_related("call")
        .order_by("-call__created_at", "line_number")[:100]
    )
    results = [
        {
            "call_id": str(seg.call_id),
            "call_title": seg.call.title,
            "segment_id": str(seg.id),
            "line_number": seg.line_number,
            "speaker_label": seg.speaker_label,
            "text": seg.text,
        }
        for seg in segments
    ]
    return Response({"query": q, "count": len(results), "results": results})
