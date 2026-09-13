import uuid

from django.conf import settings
from django.db import models

from apps.calls.choices import ReviewStatus, Severity
from apps.calls.models import Call
from apps.intelligence.models import Analysis
from apps.transcripts.models import TranscriptSegment


class ReviewItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    call = models.ForeignKey(Call, on_delete=models.CASCADE, related_name="review_items")
    analysis = models.ForeignKey(
        Analysis, on_delete=models.CASCADE, related_name="review_items"
    )
    category = models.CharField(max_length=128)
    reason = models.TextField()
    severity = models.CharField(max_length=16, choices=Severity.choices)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=ReviewStatus.choices,
        default=ReviewStatus.OPEN,
    )
    source_type = models.CharField(max_length=64, blank=True, default="")
    source_id = models.UUIDField(null=True, blank=True)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_items",
    )
    reviewer_note = models.TextField(blank=True, default="")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    evidence = models.ManyToManyField(
        TranscriptSegment,
        through="ReviewEvidence",
        related_name="review_items",
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.category} · {self.status}"


class ReviewEvidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review_item = models.ForeignKey(ReviewItem, on_delete=models.CASCADE)
    transcript_segment = models.ForeignKey(TranscriptSegment, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["review_item", "transcript_segment"],
                name="unique_review_evidence",
            )
        ]
