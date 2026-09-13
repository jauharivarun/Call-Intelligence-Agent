from django.db import models


class CallStatus(models.TextChoices):
    UPLOADED = "UPLOADED", "Uploaded"
    PROCESSING = "PROCESSING", "Processing"
    TRANSCRIBING = "TRANSCRIBING", "Transcribing"
    DIARIZING = "DIARIZING", "Diarizing"
    ANALYZING = "ANALYZING", "Analyzing"
    VERIFYING = "VERIFYING", "Verifying"
    COMPLIANCE_CHECK = "COMPLIANCE_CHECK", "Compliance check"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class CallDomain(models.TextChoices):
    DEBT_COLLECTION = "debt_collection", "Debt collection"
    CUSTOMER_SUPPORT = "customer_support", "Customer support"
    SALES = "sales", "Sales"
    INTERNAL = "internal", "Internal"
    OTHER = "other", "Other"


class VerificationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUPPORTED = "SUPPORTED", "Supported"
    PARTIAL = "PARTIAL", "Partial"
    UNSUPPORTED = "UNSUPPORTED", "Unsupported"
    REVIEW = "REVIEW", "Review"


class OwnerType(models.TextChoices):
    AGENT = "agent", "Agent"
    CUSTOMER = "customer", "Customer"
    SUPERVISOR = "supervisor", "Supervisor"
    OTHER = "other", "Other"
    UNKNOWN = "unknown", "Unknown"


class Severity(models.TextChoices):
    GREEN = "GREEN", "Green"
    YELLOW = "YELLOW", "Yellow"
    RED = "RED", "Red"


class ComplianceCategory(models.TextChoices):
    CONSENT = "CONSENT", "Consent"
    CEASE_AND_DESIST = "CEASE_AND_DESIST", "Cease and desist"
    LEGAL_MENTION = "LEGAL_MENTION", "Legal mention"
    BANKRUPTCY = "BANKRUPTCY", "Bankruptcy"
    WRONG_NUMBER = "WRONG_NUMBER", "Wrong number"
    SETTLEMENT_APPROVAL = "SETTLEMENT_APPROVAL", "Settlement approval"
    OTHER = "OTHER", "Other"


class ReviewStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    IN_REVIEW = "IN_REVIEW", "In review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    ESCALATED = "ESCALATED", "Escalated"


class JobStage(models.TextChoices):
    TRANSCRIPTION = "TRANSCRIPTION", "Transcription"
    DIARIZATION = "DIARIZATION", "Diarization"
    EXTRACTION = "EXTRACTION", "Extraction"
    VERIFICATION = "VERIFICATION", "Verification"
    COMPLIANCE = "COMPLIANCE", "Compliance"
    SENTIMENT = "SENTIMENT", "Sentiment"
    FINALIZATION = "FINALIZATION", "Finalization"


class JobStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    RUNNING = "RUNNING", "Running"
    SUCCEEDED = "SUCCEEDED", "Succeeded"
    FAILED = "FAILED", "Failed"


class SentimentLabel(models.TextChoices):
    POSITIVE = "POSITIVE", "Positive"
    NEGATIVE = "NEGATIVE", "Negative"
    NEUTRAL = "NEUTRAL", "Neutral"
    MIXED = "MIXED", "Mixed"
    UNKNOWN = "UNKNOWN", "Unknown"
