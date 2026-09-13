# Call Intelligence AI Agent — Backend Schema Document

## 1. Database Choice

Use **PostgreSQL**.

The transcript is stored as structured rows rather than one giant text field so that individual lines can be:
- Referenced as evidence.
- Highlighted.
- Searched.
- Indexed.
- Linked to analysis items.

No vector database is required for MVP.

## 2. Entity Relationship Overview

```text
User
 |
 +----< Call
          |
          +----< TranscriptSegment
          |
          +----< Analysis
          |       |
          |       +----< Decision
          |       +----< ActionItem
          |       +----< Blocker
          |       +----< ComplianceObservation
          |       +----< ReviewItem
          |
          +----< SentimentAnalysis
```

## 3. User

Django's built-in User model should be used.

Relevant fields are provided by Django:
- id
- username/email depending on configuration
- password hash
- is_active
- timestamps as applicable

Do not create a custom user table unless a real requirement appears.

## 4. Call

Represents one uploaded recording and its analysis lifecycle.

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| user_id | FK User | Required |
| title | varchar | Optional |
| domain | varchar/enum | Required |
| call_date | date | Required |
| recording_path | varchar | Required |
| recording_duration_seconds | integer | Optional |
| status | enum | Required |
| error_message | text | Nullable |
| created_at | datetime | Required |
| updated_at | datetime | Required |

Suggested statuses:

```text
UPLOADED
PROCESSING
TRANSCRIBING
DIARIZING
ANALYZING
VERIFYING
COMPLIANCE_CHECK
COMPLETED
FAILED
```

Indexes:
- `(user_id, created_at)`
- `(user_id, status)`
- `(call_date)`

## 5. TranscriptSegment

Represents a stable numbered transcript line.

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| call_id | FK Call | Required |
| line_number | integer | Required |
| speaker_label | varchar | Required |
| start_time_seconds | decimal | Nullable |
| end_time_seconds | decimal | Nullable |
| text | text | Required |
| created_at | datetime | Required |

Constraints:
- Unique `(call_id, line_number)`.

Indexes:
- `(call_id, line_number)`
- `(call_id, speaker_label)`
- Full-text/search index on `text` if enabled.

Important:
`text` must contain the original stored transcript text. Do not modify it for evidence display.

## 6. Analysis

One final/active analysis result for a call.

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| call_id | OneToOne/FK | Required |
| tag | varchar | Required |
| summary | text | Required |
| overall_confidence | decimal | Optional |
| analysis_version | varchar | Required |
| created_at | datetime | Required |
| updated_at | datetime | Required |

## 7. Decision

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| analysis_id | FK Analysis | Required |
| text | text | Required |
| confidence | decimal | Optional |
| verification_status | enum | Required |
| created_at | datetime | Required |

Suggested verification statuses:
- PENDING
- SUPPORTED
- PARTIAL
- UNSUPPORTED
- REVIEW

## 8. DecisionEvidence

Many-to-many relationship between a decision and transcript lines.

| Field | Type |
|---|---|
| id | UUID |
| decision_id | FK |
| transcript_segment_id | FK |

Constraint:
- Unique `(decision_id, transcript_segment_id)`.

## 9. ActionItem

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| analysis_id | FK Analysis | Required |
| task | text | Required |
| owner_name | varchar | Nullable |
| owner_type | enum | Optional |
| start_date | date | Nullable |
| due_date | date | Nullable |
| original_due_phrase | varchar | Nullable |
| confidence | decimal | Optional |
| verification_status | enum | Required |
| review_required | boolean | Default false |
| created_at | datetime | Required |

`original_due_phrase` is important for auditability:
- "Friday"
- "15th of next month"

The normalized date should never replace the original phrase.

## 10. ActionItemEvidence

| Field | Type |
|---|---|
| id | UUID |
| action_item_id | FK |
| transcript_segment_id | FK |

Unique `(action_item_id, transcript_segment_id)`.

## 11. Blocker

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| analysis_id | FK | Required |
| text | text | Required |
| impact | text | Nullable |
| confidence | decimal | Optional |
| verification_status | enum | Required |
| review_required | boolean | Default false |

## 12. BlockerEvidence

| Field | Type |
|---|---|
| id | UUID |
| blocker_id | FK |
| transcript_segment_id | FK |

## 13. ComplianceObservation

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| analysis_id | FK | Required |
| category | varchar | Required |
| severity | enum | Required |
| observation | text | Required |
| rationale | text | Nullable |
| confidence | decimal | Optional |
| review_required | boolean | Default false |
| created_at | datetime | Required |

Severity:
- GREEN
- YELLOW
- RED

Suggested categories:
- CONSENT
- CEASE_AND_DESIST
- LEGAL_MENTION
- BANKRUPTCY
- WRONG_NUMBER
- SETTLEMENT_APPROVAL
- OTHER

## 14. ComplianceEvidence

| Field | Type |
|---|---|
| id | UUID |
| compliance_observation_id | FK |
| transcript_segment_id | FK |

## 15. ReviewItem

Central human-review queue item.

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| call_id | FK | Required |
| analysis_id | FK | Required |
| category | varchar | Required |
| reason | text | Required |
| severity | enum | Required |
| confidence | decimal | Optional |
| status | enum | Required |
| reviewer_id | FK User | Nullable |
| reviewer_note | text | Nullable |
| reviewed_at | datetime | Nullable |
| created_at | datetime | Required |
| updated_at | datetime | Required |

Statuses:
- OPEN
- IN_REVIEW
- APPROVED
- REJECTED
- ESCALATED

The review item should reference the original source object when applicable.

## 16. ReviewEvidence

| Field | Type |
|---|---|
| id | UUID |
| review_item_id | FK |
| transcript_segment_id | FK |

## 17. EvidenceVerification

Optional central table for auditable verification.

| Field | Type |
|---|---|
| id | UUID |
| call_id | FK |
| claim_type | varchar |
| claim_id | UUID |
| verification_status | enum |
| score | decimal |
| verifier_reason | text |
| created_at | datetime |

Suggested statuses:
- SUPPORTED
- PARTIAL
- UNSUPPORTED
- REVIEW

## 18. SentimentAnalysis (Bonus)

| Field | Type |
|---|---|
| id | UUID |
| call_id | OneToOne/FK |
| overall_sentiment | enum |
| customer_sentiment | enum |
| agent_sentiment | enum |
| profanity_detected | boolean |
| angry_customer_detected | boolean |
| confidence | decimal |
| created_at | datetime |

Sentiment values:
- POSITIVE
- NEGATIVE
- NEUTRAL
- MIXED
- UNKNOWN

## 19. SentimentEvidence (Optional)

Use transcript-line relationships when a sentiment signal needs explainability.

| Field | Type |
|---|---|
| id | UUID |
| sentiment_analysis_id | FK |
| transcript_segment_id | FK |
| signal_type | varchar |

## 20. ProcessingJob

Useful for tracking asynchronous pipeline execution.

| Field | Type |
|---|---|
| id | UUID |
| call_id | FK |
| stage | varchar |
| status | enum |
| started_at | datetime |
| completed_at | datetime |
| error_message | text |
| metadata | JSONB |

Stages:
- TRANSCRIPTION
- DIARIZATION
- EXTRACTION
- VERIFICATION
- COMPLIANCE
- FINALIZATION

## 21. Permissions

Every call is owned by a user.

Default rule:

```text
User → can access own calls
User → can access own analyses
User → can access own transcripts
User → can access own review items
Reviewer → can access assigned/permitted review items
```

For MVP, a simple owner/reviewer role model is enough.

## 22. Data Ownership

A user must not be able to retrieve another user's call by guessing a UUID.

Every detail query should enforce ownership/authorization at the ORM/API layer.

## 23. Auditability

Store:
- Created/updated timestamps.
- Analysis version.
- Review decisions.
- Reviewer.
- Review timestamp.
- Evidence links.
- Original date phrase.
- Verification status.

## 24. Search

MVP:
- PostgreSQL `icontains` or full-text search on `TranscriptSegment.text`.

Potential indexes:
- PostgreSQL GIN full-text index if search scale requires it.

Do not introduce embeddings/vector search just for transcript search.

## 25. JSON Fields

Use JSONB only for flexible provider metadata or raw structured outputs that are useful for debugging.

Do not put core relational entities entirely inside one JSON blob.

Example:
`provider_metadata JSONB`

## 26. Data Retention

The MVP should provide a clear deletion path for:
- Recording.
- Transcript.
- Analysis.
- Evidence.
- Review items.

Deleting a call should cascade or explicitly clean dependent records according to application policy.

## 27. Django App Structure

Suggested Django apps:

```text
apps/
  accounts/
  calls/
  transcripts/
  intelligence/
  compliance/
  reviews/
  search/
```

Keep AI/provider integration code separate from database models where practical.

## 28. Recommended Service Layer

```text
calls/services/
  processing.py

intelligence/services/
  extraction.py
  evidence.py
  dates.py

compliance/services/
  rules.py

reviews/services/
  review.py

ai/providers/
  transcription.py
  diarization.py
  llm.py
```

The exact structure can evolve, but business logic should not be placed directly inside views.
