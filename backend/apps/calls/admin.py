from django.contrib import admin

from apps.calls.models import Call, ProcessingJob
from apps.intelligence.models import (
    ActionItem,
    Analysis,
    Blocker,
    ComplianceObservation,
    Decision,
    EvidenceVerification,
    SentimentAnalysis,
)
from apps.reviews.models import ReviewItem
from apps.transcripts.models import TranscriptSegment


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "domain", "call_date", "status", "created_at")
    list_filter = ("status", "domain")
    search_fields = ("title", "id")


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ("id", "call", "stage", "status", "started_at", "completed_at")


@admin.register(TranscriptSegment)
class TranscriptSegmentAdmin(admin.ModelAdmin):
    list_display = ("call", "line_number", "speaker_label", "text")


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ("call", "tag", "overall_confidence", "created_at")


admin.site.register(Decision)
admin.site.register(ActionItem)
admin.site.register(Blocker)
admin.site.register(ComplianceObservation)
admin.site.register(ReviewItem)
admin.site.register(EvidenceVerification)
admin.site.register(SentimentAnalysis)
