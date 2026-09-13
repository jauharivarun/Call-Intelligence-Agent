import uuid

from django.db import models

from apps.calls.choices import (
    ComplianceCategory,
    OwnerType,
    SentimentLabel,
    Severity,
    VerificationStatus,
)
from apps.calls.models import Call
from apps.transcripts.models import TranscriptSegment


class Analysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    call = models.OneToOneField(Call, on_delete=models.CASCADE, related_name="analysis")
    tag = models.CharField(max_length=255)
    summary = models.TextField()
    overall_confidence = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True
    )
    analysis_version = models.CharField(max_length=64, default="v1")
    raw_extraction = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Analysis for {self.call_id}: {self.tag}"


class Decision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(
        Analysis, on_delete=models.CASCADE, related_name="decisions"
    )
    text = models.TextField()
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    verification_status = models.CharField(
        max_length=16,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    evidence = models.ManyToManyField(
        TranscriptSegment,
        through="DecisionEvidence",
        related_name="decisions",
        blank=True,
    )


class DecisionEvidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    decision = models.ForeignKey(Decision, on_delete=models.CASCADE)
    transcript_segment = models.ForeignKey(TranscriptSegment, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["decision", "transcript_segment"],
                name="unique_decision_evidence",
            )
        ]


class ActionItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(
        Analysis, on_delete=models.CASCADE, related_name="action_items"
    )
    task = models.TextField()
    owner_name = models.CharField(max_length=255, blank=True, default="")
    owner_type = models.CharField(
        max_length=32,
        choices=OwnerType.choices,
        default=OwnerType.UNKNOWN,
        blank=True,
    )
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    original_due_phrase = models.CharField(max_length=255, blank=True, default="")
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    verification_status = models.CharField(
        max_length=16,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    review_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    evidence = models.ManyToManyField(
        TranscriptSegment,
        through="ActionItemEvidence",
        related_name="action_items",
        blank=True,
    )


class ActionItemEvidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action_item = models.ForeignKey(ActionItem, on_delete=models.CASCADE)
    transcript_segment = models.ForeignKey(TranscriptSegment, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["action_item", "transcript_segment"],
                name="unique_action_item_evidence",
            )
        ]


class Blocker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(
        Analysis, on_delete=models.CASCADE, related_name="blockers"
    )
    text = models.TextField()
    impact = models.TextField(blank=True, default="")
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    verification_status = models.CharField(
        max_length=16,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    review_required = models.BooleanField(default=False)
    evidence = models.ManyToManyField(
        TranscriptSegment,
        through="BlockerEvidence",
        related_name="blockers",
        blank=True,
    )


class BlockerEvidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(Blocker, on_delete=models.CASCADE)
    transcript_segment = models.ForeignKey(TranscriptSegment, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["blocker", "transcript_segment"],
                name="unique_blocker_evidence",
            )
        ]


class ComplianceObservation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(
        Analysis, on_delete=models.CASCADE, related_name="compliance_observations"
    )
    category = models.CharField(max_length=64, choices=ComplianceCategory.choices)
    severity = models.CharField(max_length=16, choices=Severity.choices)
    observation = models.TextField()
    rationale = models.TextField(blank=True, default="")
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    review_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    evidence = models.ManyToManyField(
        TranscriptSegment,
        through="ComplianceEvidence",
        related_name="compliance_observations",
        blank=True,
    )


class ComplianceEvidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    compliance_observation = models.ForeignKey(
        ComplianceObservation, on_delete=models.CASCADE
    )
    transcript_segment = models.ForeignKey(TranscriptSegment, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["compliance_observation", "transcript_segment"],
                name="unique_compliance_evidence",
            )
        ]


class EvidenceVerification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    call = models.ForeignKey(
        Call, on_delete=models.CASCADE, related_name="verifications"
    )
    claim_type = models.CharField(max_length=64)
    claim_id = models.UUIDField()
    verification_status = models.CharField(
        max_length=16, choices=VerificationStatus.choices
    )
    score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    verifier_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)


class SentimentAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    call = models.OneToOneField(
        Call, on_delete=models.CASCADE, related_name="sentiment"
    )
    overall_sentiment = models.CharField(
        max_length=16, choices=SentimentLabel.choices, default=SentimentLabel.UNKNOWN
    )
    customer_sentiment = models.CharField(
        max_length=16, choices=SentimentLabel.choices, default=SentimentLabel.UNKNOWN
    )
    agent_sentiment = models.CharField(
        max_length=16, choices=SentimentLabel.choices, default=SentimentLabel.UNKNOWN
    )
    profanity_detected = models.BooleanField(default=False)
    angry_customer_detected = models.BooleanField(default=False)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    evidence = models.ManyToManyField(
        TranscriptSegment,
        through="SentimentEvidence",
        related_name="sentiment_signals",
        blank=True,
    )


class SentimentEvidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sentiment_analysis = models.ForeignKey(SentimentAnalysis, on_delete=models.CASCADE)
    transcript_segment = models.ForeignKey(TranscriptSegment, on_delete=models.CASCADE)
    signal_type = models.CharField(max_length=64, blank=True, default="")
