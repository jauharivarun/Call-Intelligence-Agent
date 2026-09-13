import uuid

from django.conf import settings
from django.db import models

from .choices import CallDomain, CallStatus, JobStage, JobStatus


class Call(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calls",
    )
    title = models.CharField(max_length=255, blank=True, default="")
    domain = models.CharField(max_length=64, choices=CallDomain.choices)
    call_date = models.DateField()
    recording_path = models.CharField(max_length=1024)
    recording_duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=CallStatus.choices,
        default=CallStatus.UPLOADED,
    )
    error_message = models.TextField(blank=True, default="")
    provider_metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["call_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.title or self.id} ({self.status})"


class ProcessingJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    call = models.ForeignKey(Call, on_delete=models.CASCADE, related_name="jobs")
    stage = models.CharField(max_length=32, choices=JobStage.choices)
    status = models.CharField(
        max_length=16,
        choices=JobStatus.choices,
        default=JobStatus.PENDING,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["started_at", "id"]

    def __str__(self) -> str:
        return f"{self.call_id} · {self.stage} · {self.status}"
