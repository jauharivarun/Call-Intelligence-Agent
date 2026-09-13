import uuid

from django.db import models

from apps.calls.models import Call


class TranscriptSegment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    call = models.ForeignKey(Call, on_delete=models.CASCADE, related_name="segments")
    line_number = models.PositiveIntegerField()
    speaker_label = models.CharField(max_length=128)
    start_time_seconds = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True
    )
    end_time_seconds = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["line_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["call", "line_number"],
                name="unique_call_line_number",
            )
        ]
        indexes = [
            models.Index(fields=["call", "line_number"]),
            models.Index(fields=["call", "speaker_label"]),
        ]

    def __str__(self) -> str:
        return f"{self.line_number}: {self.speaker_label}: {self.text[:40]}"
