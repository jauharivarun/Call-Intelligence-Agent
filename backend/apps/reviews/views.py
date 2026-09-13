from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.calls.choices import ReviewStatus
from apps.calls.serializers import TranscriptSegmentSerializer
from apps.reviews.models import ReviewItem


class ReviewItemSerializer(serializers.ModelSerializer):
    evidence = TranscriptSegmentSerializer(many=True, read_only=True)
    call_title = serializers.CharField(source="call.title", read_only=True)
    reviewer_username = serializers.SerializerMethodField()
    is_resolved = serializers.SerializerMethodField()

    class Meta:
        model = ReviewItem
        fields = [
            "id",
            "call",
            "call_title",
            "analysis",
            "category",
            "reason",
            "severity",
            "confidence",
            "status",
            "is_resolved",
            "source_type",
            "source_id",
            "reviewer",
            "reviewer_username",
            "reviewer_note",
            "reviewed_at",
            "evidence",
            "created_at",
            "updated_at",
        ]

    def get_reviewer_username(self, obj) -> str | None:
        return obj.reviewer.username if obj.reviewer_id else None

    def get_is_resolved(self, obj) -> bool:
        return obj.status in {
            ReviewStatus.APPROVED,
            ReviewStatus.REJECTED,
            ReviewStatus.ESCALATED,
        }


class ReviewDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(
        choices=["APPROVED", "REJECTED", "ESCALATED", "OPEN"]
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")


RESOLVED_STATUSES = (
    ReviewStatus.APPROVED,
    ReviewStatus.REJECTED,
    ReviewStatus.ESCALATED,
)
OPEN_STATUSES = (ReviewStatus.OPEN, ReviewStatus.IN_REVIEW)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def review_list(request):
    qs = (
        ReviewItem.objects.all()
        .select_related("call", "analysis", "reviewer")
        .prefetch_related("evidence")
    )
    status_filter = (request.query_params.get("status") or "").strip().upper()
    if status_filter == "RESOLVED":
        qs = qs.filter(status__in=RESOLVED_STATUSES)
    elif status_filter == "OPEN":
        qs = qs.filter(status__in=OPEN_STATUSES)
    elif status_filter:
        qs = qs.filter(status=status_filter)
    return Response(ReviewItemSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def review_detail(request, review_id):
    try:
        item = (
            ReviewItem.objects.select_related("reviewer")
            .prefetch_related("evidence")
            .get(pk=review_id)
        )
    except ReviewItem.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(ReviewItemSerializer(item).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def review_decision(request, review_id):
    """Create or update a review decision.

    Resolved items can be edited (new outcome/note) or reopened with decision=OPEN
    to correct accidental resolutions.
    """
    try:
        item = ReviewItem.objects.select_related("reviewer").get(pk=review_id)
    except ReviewItem.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ReviewDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    decision = serializer.validated_data["decision"]
    note = serializer.validated_data.get("note") or ""

    if decision == "OPEN":
        item.status = ReviewStatus.OPEN
        item.reviewer = None
        item.reviewer_note = note
        item.reviewed_at = None
    else:
        item.status = decision
        item.reviewer = request.user
        item.reviewer_note = note
        item.reviewed_at = timezone.now()

    item.save()
    item.refresh_from_db()
    return Response(ReviewItemSerializer(item).data)
