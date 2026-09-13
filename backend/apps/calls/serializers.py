from rest_framework import serializers

from apps.calls.choices import CallDomain
from apps.calls.models import Call, ProcessingJob
from apps.intelligence.models import (
    ActionItem,
    Analysis,
    Blocker,
    ComplianceObservation,
    Decision,
    SentimentAnalysis,
)
from apps.reviews.models import ReviewItem
from apps.transcripts.models import TranscriptSegment


class TranscriptSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptSegment
        fields = [
            "id",
            "line_number",
            "speaker_label",
            "start_time_seconds",
            "end_time_seconds",
            "text",
        ]


class ProcessingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingJob
        fields = [
            "id",
            "stage",
            "status",
            "started_at",
            "completed_at",
            "error_message",
        ]


class CallListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Call
        fields = [
            "id",
            "title",
            "domain",
            "call_date",
            "status",
            "error_message",
            "recording_duration_seconds",
            "created_at",
            "updated_at",
        ]


class CallDetailSerializer(serializers.ModelSerializer):
    jobs = ProcessingJobSerializer(many=True, read_only=True)

    class Meta:
        model = Call
        fields = [
            "id",
            "title",
            "domain",
            "call_date",
            "status",
            "error_message",
            "recording_path",
            "recording_duration_seconds",
            "created_at",
            "updated_at",
            "jobs",
        ]


class CallUploadSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    domain = serializers.ChoiceField(choices=CallDomain.choices)
    call_date = serializers.DateField()
    recording = serializers.FileField()


class DecisionSerializer(serializers.ModelSerializer):
    evidence = TranscriptSegmentSerializer(many=True, read_only=True)

    class Meta:
        model = Decision
        fields = [
            "id",
            "text",
            "confidence",
            "verification_status",
            "evidence",
            "created_at",
        ]


class ActionItemSerializer(serializers.ModelSerializer):
    evidence = TranscriptSegmentSerializer(many=True, read_only=True)

    class Meta:
        model = ActionItem
        fields = [
            "id",
            "task",
            "owner_name",
            "owner_type",
            "start_date",
            "due_date",
            "original_due_phrase",
            "confidence",
            "verification_status",
            "review_required",
            "evidence",
            "created_at",
        ]


class BlockerSerializer(serializers.ModelSerializer):
    evidence = TranscriptSegmentSerializer(many=True, read_only=True)

    class Meta:
        model = Blocker
        fields = [
            "id",
            "text",
            "impact",
            "confidence",
            "verification_status",
            "review_required",
            "evidence",
        ]


class ComplianceObservationSerializer(serializers.ModelSerializer):
    evidence = TranscriptSegmentSerializer(many=True, read_only=True)

    class Meta:
        model = ComplianceObservation
        fields = [
            "id",
            "category",
            "severity",
            "observation",
            "rationale",
            "confidence",
            "review_required",
            "evidence",
            "created_at",
        ]


class ReviewItemBriefSerializer(serializers.ModelSerializer):
    evidence = TranscriptSegmentSerializer(many=True, read_only=True)
    is_resolved = serializers.SerializerMethodField()
    reviewer_username = serializers.SerializerMethodField()

    class Meta:
        model = ReviewItem
        fields = [
            "id",
            "category",
            "reason",
            "severity",
            "confidence",
            "status",
            "is_resolved",
            "source_type",
            "source_id",
            "reviewer_username",
            "reviewer_note",
            "reviewed_at",
            "evidence",
            "created_at",
        ]

    def get_is_resolved(self, obj) -> bool:
        return obj.status in {"APPROVED", "REJECTED", "ESCALATED"}

    def get_reviewer_username(self, obj) -> str | None:
        return obj.reviewer.username if obj.reviewer_id else None


class SentimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SentimentAnalysis
        fields = [
            "overall_sentiment",
            "customer_sentiment",
            "agent_sentiment",
            "profanity_detected",
            "angry_customer_detected",
            "confidence",
        ]


class AnalysisSerializer(serializers.ModelSerializer):
    decisions = DecisionSerializer(many=True, read_only=True)
    action_items = ActionItemSerializer(many=True, read_only=True)
    blockers = BlockerSerializer(many=True, read_only=True)
    compliance_observations = ComplianceObservationSerializer(many=True, read_only=True)
    review_items = ReviewItemBriefSerializer(many=True, read_only=True)

    class Meta:
        model = Analysis
        fields = [
            "id",
            "tag",
            "summary",
            "overall_confidence",
            "analysis_version",
            "created_at",
            "updated_at",
            "decisions",
            "action_items",
            "blockers",
            "compliance_observations",
            "review_items",
        ]
