# Call Intelligence AI Agent — Technical Requirements Document (TRD)

## 1. Technical Objective

Build a small, maintainable web application for post-call intelligence. The architecture should favor clear separation between deterministic processing, AI extraction, evidence verification, compliance rules, persistence, and human review.

The system should **not introduce RAG or a vector database unless a later requirement genuinely needs external knowledge retrieval**.

## 2. Recommended Stack

### Backend
- Python 3.12+
- Django
- Django REST Framework
- Celery for asynchronous processing
- Redis as Celery broker/result backend
- PostgreSQL

### Frontend
- React
- Vite
- TypeScript

The frontend communicates with Django through REST APIs.

### AI / ML
Use provider abstractions so the implementation is not tightly coupled to one vendor:
- Speech-to-text provider.
- Speaker diarization component/provider.
- LLM provider for structured extraction and semantic evidence verification.
- Optional sentiment/classification model.

### Storage
- PostgreSQL for application data.
- Object/file storage for recordings.
- No vector database for MVP.

### Local development
- Docker Compose for PostgreSQL, Redis, Django, and frontend where practical.

## 3. High-Level Architecture

```text
React/Vite UI
      |
      | REST API
      v
Django + DRF
      |
      +---- PostgreSQL
      |
      +---- Recording Storage
      |
      +---- Celery ---- Redis
      |       |
      |       +--> Transcription
      |       +--> Diarization
      |       +--> Intelligence Extraction
      |       +--> Evidence Verification
      |       +--> Compliance Analysis
      |
      +---- LLM / Speech Providers
```

## 4. Processing Pipeline

### Stage 1 — Upload
1. API receives audio.
2. Validate extension/MIME type and size.
3. Create Call record with `PROCESSING` status.
4. Store recording.
5. Enqueue processing task.

### Stage 2 — Transcription
1. Send recording to STT provider.
2. Receive transcript segments and timestamps.
3. Persist raw transcription result.
4. Continue to diarization/attribution.

### Stage 3 — Speaker Diarization
1. Determine speaker segments.
2. Map transcript segments to speaker labels.
3. Generate normalized transcript lines.
4. Persist lines.

### Stage 4 — Context Preparation
Prepare a context package:
- call ID
- call date
- domain
- speakers
- numbered transcript

This is the context supplied to extraction.

### Stage 5 — Intelligence Extraction
LLM produces structured JSON:
- tag
- summary
- decisions
- action items
- blockers
- compliance candidates
- review candidates

The LLM must return evidence line IDs for claims rather than inventing quotations.

### Stage 6 — Evidence Verification
For each factual claim:
1. Retrieve candidate lines using normal text/keyword retrieval.
2. If necessary, use semantic similarity/entailment through the LLM.
3. Verify that the evidence supports the claim.
4. Persist verification status and score.
5. Reject or route unsupported claims to review.

### Stage 7 — Date Resolution
Use deterministic date logic for phrases identified by the LLM:
- Preserve original phrase.
- Resolve against call date.
- Store normalized date.
- Mark ambiguous dates for review.

### Stage 8 — Compliance
Run domain-specific rules/classifiers.
For debt collection, include at minimum:
- cease-and-desist
- legal mention
- bankruptcy
- wrong number
- consent/recording ambiguity
- settlement/approval concerns

### Stage 9 — Finalization
Create final analysis:
- accepted structured outputs
- review queue items
- sentiment signals if enabled
- processing metadata

## 5. Agent Design

Do not build a complex multi-agent architecture for MVP.

Use one orchestration service with specialized processing functions/services:

```text
CallAnalysisOrchestrator
    |
    +-- TranscriptionService
    +-- DiarizationService
    +-- ExtractionService
    +-- EvidenceService
    +-- DateResolutionService
    +-- ComplianceService
    +-- ReviewService
```

Each service should have a clear input/output contract.

## 6. LLM Responsibilities

The LLM may:
- Extract decisions.
- Extract action items.
- Identify possible owners.
- Identify date phrases.
- Identify blockers.
- Classify compliance candidates.
- Generate concise summaries.
- Perform semantic support/entailment checks.

The LLM must not be trusted as the final authority for factual grounding.

## 7. Deterministic Responsibilities

Prefer deterministic code for:
- File validation.
- Status transitions.
- Line numbering.
- Database persistence.
- Date arithmetic once a date expression is identified.
- Evidence line retrieval.
- Permission checks.
- Review status transitions.
- API validation.
- Audit fields.

## 8. Evidence Verification Design

### Claim object

```json
{
  "claim_type": "action_item",
  "claim_text": "Agent will follow up with supervisor",
  "evidence_line_ids": [8],
  "owner": "Marcus",
  "due_date": "2026-07-03"
}
```

### Verification flow

```text
Claim
  |
  v
Candidate line retrieval
  |
  v
Semantic support check
  |
  +--> supported --> ACCEPT
  |
  +--> partially supported --> LOWER CONFIDENCE / REVIEW
  |
  +--> unsupported --> REVIEW / REJECT
```

### Important rule
Never replace original transcript evidence with an LLM-generated quote.

## 9. Confidence

Confidence should be derived from multiple signals where practical:

- Evidence support.
- Evidence specificity.
- Owner clarity.
- Date clarity.
- Extraction certainty.
- Compliance severity.
- Contradictory transcript evidence.

Do not present a false sense of mathematical precision. A simple normalized score can be used for the demo, but the UI should also explain why an item is low-confidence.

Suggested categories:
- High: safe to show as accepted.
- Medium: show with caution.
- Low: human review.

## 10. API Requirements

### Calls
- `POST /api/calls/` — create/upload call.
- `GET /api/calls/` — list calls.
- `GET /api/calls/{id}/` — call details.
- `GET /api/calls/{id}/transcript/` — transcript lines.
- `GET /api/calls/{id}/analysis/` — final intelligence.
- `POST /api/calls/{id}/reanalyze/` — rerun analysis if permitted.

### Review
- `GET /api/reviews/` — review queue.
- `GET /api/reviews/{id}/` — review item.
- `POST /api/reviews/{id}/decision/` — approve/reject/escalate with reviewer note.

### Search
- `GET /api/search/transcripts/?q=...`

### Health
- `GET /api/health/`

Exact route naming can be adjusted during implementation, but the API responsibilities should remain stable.

## 11. Authentication

For the assignment MVP:
- Django authentication/session or token-based API authentication.
- Every persisted call belongs to a user.
- Users can only access their own calls and review items unless an explicit shared-role model is introduced.

Do not over-engineer authentication before core analysis works.

## 12. Security Requirements

- Validate file type and size.
- Never execute uploaded files.
- Store recordings outside executable application paths.
- Protect API endpoints with authentication.
- Enforce object-level authorization.
- Avoid logging raw sensitive transcript content unnecessarily.
- Redact sensitive values from operational logs where practical.
- Protect API keys through environment variables/secrets.
- Restrict reviewer actions to authorized users.
- Keep audit timestamps for review decisions.

## 13. Performance Requirements

For an assignment-scale system:
- Upload should return quickly and process asynchronously.
- UI should poll or receive status updates.
- Long-running transcription/analysis must never block the web request.
- Evidence verification should operate per extracted item where possible.
- Database queries for transcript lines should be indexed by call ID and line number.
- Search should use PostgreSQL text capabilities before considering a vector store.

## 14. Failure Handling

Processing statuses:

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

On failure:
- Store a safe user-facing error.
- Preserve technical error details in logs.
- Allow retry where safe.
- Do not mark an incomplete analysis as completed.

## 15. Observability

Track:
- Call processing duration.
- Stage durations.
- Provider failures.
- Number of extracted items.
- Number of evidence-supported items.
- Number of review items.
- Compliance flags.
- Processing failures.

Avoid logging full audio/transcript contents by default.

## 16. Deployment

A simple deployment target can use:
- Django application server.
- Celery worker.
- Redis.
- PostgreSQL.
- Object storage.
- React static build.

Keep deployment provider-specific details isolated in environment configuration.

## 17. Key Technical Decision: No RAG in MVP

The transcript is the primary source of truth. The task is extraction and grounding against that source, not answering questions from an external knowledge corpus.

Therefore:
- Store transcript lines in PostgreSQL.
- Search candidate lines using conventional database search.
- Use semantic verification only when necessary.
- Do not create embeddings for every transcript line in MVP.
- Do not add Chroma/Pinecone/etc. merely because the application contains an LLM.

A future policy/document knowledge base could use RAG for compliance, but that is outside the MVP.

## 18. Provider Abstraction

Create interfaces such as:

```python
class TranscriptionProvider:
    def transcribe(self, audio_path): ...

class DiarizationProvider:
    def diarize(self, audio_path): ...

class LLMProvider:
    def generate_structured(self, prompt, schema): ...
    def verify_entailment(self, claim, evidence): ...
```

This makes the application testable and allows providers to be changed without rewriting business logic.
