# Call Intelligence AI Agent — Implementation Plan

## 1. Implementation Philosophy

Build the application in small, testable phases.

Do **not** ask Cursor to build the entire application in one prompt.

At every phase:
1. Read the existing six documents.
2. Implement only the current phase.
3. Run tests.
4. Verify the feature manually.
5. Commit the work.
6. Move to the next phase.

## 2. Phase 0 — Repository and Project Setup

### Tasks
- Create repository.
- Create Django project.
- Create React/Vite frontend.
- Configure environment variables.
- Add PostgreSQL.
- Add Redis.
- Add Celery.
- Configure CORS/API communication.
- Add basic linting/formatting.
- Add `.gitignore`.
- Add `.env.example`.
- Add Docker Compose for local infrastructure if used.

### Deliverables
```text
backend/
frontend/
docker-compose.yml
.env.example
README.md
```

### Acceptance criteria
- Django starts.
- React starts.
- PostgreSQL connection works.
- Redis connection works.
- Frontend can call Django health endpoint.

## 3. Phase 1 — Authentication and Base Layout

### Tasks
- Implement Django authentication.
- Create login/logout.
- Protect application routes.
- Create basic React shell.
- Create navigation.
- Create dashboard placeholder.

### Acceptance criteria
- Unauthenticated user cannot access protected pages.
- Authenticated user reaches dashboard.
- Logout works.

## 4. Phase 2 — Database Schema

### Tasks
Implement models from Backend Schema:
- Call.
- TranscriptSegment.
- Analysis.
- Decision.
- ActionItem.
- Blocker.
- ComplianceObservation.
- ReviewItem.
- Evidence relationships.
- ProcessingJob.
- Optional SentimentAnalysis.

### Tasks
- Create migrations.
- Add indexes/constraints.
- Register useful models in Django admin.

### Acceptance criteria
- Migrations apply cleanly.
- Foreign keys work.
- Unique transcript line constraint works.
- Ownership is enforceable.

## 5. Phase 3 — Call Upload

### Tasks
- Build upload API.
- Build upload UI.
- Validate file.
- Store recording.
- Store call date/domain/title.
- Create processing status.
- Enqueue Celery task.

### Acceptance criteria
- User can upload a valid audio file.
- Invalid file is rejected.
- Call appears in dashboard.
- Status becomes `UPLOADED`/`PROCESSING`.

## 6. Phase 4 — Transcription

### Tasks
- Implement transcription provider abstraction.
- Connect provider.
- Send audio.
- Store raw provider result if useful.
- Create transcript segments.

### Acceptance criteria
- Uploaded test recording produces transcript.
- Transcript is persisted.
- Failure changes call status to `FAILED`.
- Retry is possible.

## 7. Phase 5 — Speaker Diarization

### Tasks
- Implement diarization provider abstraction.
- Map speaker segments to transcript.
- Generate stable speaker labels.
- Preserve timestamps.
- Generate line numbers after final transcript assembly.

### Acceptance criteria
Transcript appears like:

```text
1: Agent: ...
2: Consumer: ...
3: Agent: ...
```

Every line has a stable database ID and line number.

## 8. Phase 6 — Structured Intelligence Extraction

### Tasks
Create strict output schema for:

```text
tag
summary
decisions[]
action_items[]
blockers[]
compliance_candidates[]
review_candidates[]
```

For each claim, require:
- claim text.
- evidence line IDs.
- confidence.
- relevant metadata.

### Important
Do not allow the LLM to return free-form output as the final internal representation.

### Acceptance criteria
- Valid structured JSON is produced.
- Invalid output is rejected/retried.
- No final item can be persisted without an evidence reference unless it is explicitly marked as review-required.

## 9. Phase 7 — Evidence Verification

### Tasks
Build evidence service.

For each claim:
1. Read referenced lines.
2. Optionally retrieve additional candidate lines using PostgreSQL text search.
3. Run semantic support verification when necessary.
4. Assign verification status.
5. Accept supported claims.
6. Send unsupported/partial claims to review.

### Acceptance criteria
Test cases should include:

#### Case A — Supported
Transcript:
> "I'll follow up by Friday."

Claim:
> "Agent will follow up."

Result:
`SUPPORTED`

#### Case B — Unsupported
Transcript contains no commitment.

Claim:
> "Agent will send an email tomorrow."

Result:
`UNSUPPORTED` → review/reject.

#### Case C — Partial
Transcript suggests a task but owner is unclear.

Result:
Task may be retained but:
`review_required = true`

## 10. Phase 8 — Relative Date Resolution

### Tasks
Implement deterministic date resolver.

Inputs:
- Call date.
- Original date phrase.

Outputs:
- Original phrase.
- Normalized date.
- Resolution status.

Examples:

```text
Call date: 2026-07-01
"Friday" → 2026-07-03

Call date: 2026-07-01
"15th of next month" → 2026-08-15
```

### Acceptance criteria
- Explicit dates work.
- Relative dates work.
- Ambiguous phrases are flagged.
- Original phrase is preserved.

## 11. Phase 9 — Compliance Engine

### Tasks
Implement rule/configuration driven checks.

Initial debt-collection categories:
- Cease and desist.
- Legal mention.
- Bankruptcy.
- Wrong number.
- Consent ambiguity.
- Settlement approval.

Each rule should produce:

```text
category
severity
observation
evidence_lines
confidence
review_required
```

### Acceptance criteria
Test transcript snippets trigger expected rules.
False positives should not automatically become "confirmed violations"; risky observations should be routed to review where appropriate.

## 12. Phase 10 — Human Review Queue

### Tasks
- Create review APIs.
- Create review list UI.
- Create review detail UI.
- Add evidence display.
- Add approve/reject/escalate.
- Save reviewer notes.
- Record timestamps.

### Acceptance criteria
A reviewer can:
1. Open a review item.
2. See the exact evidence.
3. Understand why it was flagged.
4. Make a decision.
5. See the updated review status.

## 13. Phase 11 — Call Analysis Dashboard

### Tasks
Build polished report UI:
- Summary.
- Decisions.
- Action items.
- Blockers.
- Compliance.
- Review.
- Transcript.

Add evidence links everywhere.

### Acceptance criteria
A reviewer can move from:
`Action Item → Evidence → Transcript lines`
in one interaction.

## 14. Phase 12 — Bonus Search

### Tasks
- Add transcript search API.
- Search PostgreSQL transcript text.
- Show matching call/line.
- Click result to open evidence.

### Acceptance criteria
Search for terms such as:
- supervisor
- attorney
- stop calling
- payment

returns relevant transcript lines.

## 15. Phase 13 — Bonus Sentiment

### Tasks
Add:
- Overall sentiment.
- Customer sentiment.
- Agent sentiment.
- Profanity.
- Angry customer.

Where possible, store supporting transcript lines.

### Acceptance criteria
Signals are visible in report without affecting the core factual extraction pipeline.

## 16. Phase 14 — Testing

### Unit tests
- Date resolver.
- Compliance rules.
- Evidence verifier.
- Permission checks.
- Status transitions.
- Schema validation.

### Integration tests
- Upload → processing.
- Transcript persistence.
- Extraction → verification.
- Review workflow.
- Search.

### End-to-end tests
Minimum scenario:

```text
Upload debt collection recording
       ↓
Transcribe
       ↓
Diarize
       ↓
Extract
       ↓
Verify evidence
       ↓
Resolve dates
       ↓
Run compliance
       ↓
Create review items
       ↓
Display report
       ↓
Reviewer approves/rejects
```

## 17. Golden Test Dataset

Create a small set of deterministic transcript fixtures.

### Fixture 1 — Clear action
Contains an explicit owner and deadline.

### Fixture 2 — Ambiguous owner
Contains a task but no clear person responsible.

### Fixture 3 — Relative date
Contains "Friday" and "next month."

### Fixture 4 — Compliance risk
Contains cease-and-desist language.

### Fixture 5 — Legal mention
Contains "I will sue you" or attorney language.

### Fixture 6 — Unsupported claim
Ensure verifier catches an invented action.

### Fixture 7 — Settlement approval
Replicate the assignment's example pattern.

## 18. Phase 15 — Security Review

Check:
- Authentication.
- Object ownership.
- File validation.
- API authorization.
- Secret management.
- Logging.
- Sensitive transcript handling.
- Review permissions.

## 19. Phase 16 — Deployment

### Tasks
- Build production React bundle.
- Configure Django production settings.
- Configure PostgreSQL.
- Configure Redis/Celery worker.
- Configure recording storage.
- Configure environment variables.
- Run migrations.
- Configure static files.
- Configure HTTPS.
- Verify health endpoint.

## 20. Phase 17 — Final Polish

Prioritize:
- Clear error messages.
- Processing progress.
- Evidence links.
- Review UX.
- Responsive behavior.
- Loading states.
- Empty states.
- README.
- Architecture diagram.
- Demo recording.

## 21. Cursor Working Method

For each phase, give Cursor a constrained instruction:

```text
Read:
- PRD
- TRD
- App Flow
- UI/UX Brief
- Backend Schema
- Implementation Plan

We are implementing Phase X only.

Before editing:
1. Inspect the existing repository.
2. Identify what already exists.
3. Do not rewrite working features.
4. Follow the schema and API contracts.
5. Implement the phase completely.
6. Add tests.
7. Run the tests.
8. Report changed files and any assumptions.
```

Then review the output before proceeding.

## 22. Recommended Build Order

The order is intentionally:

```text
1. Project setup
2. Authentication
3. Database
4. Upload
5. Transcription
6. Diarization
7. Extraction
8. Evidence verification
9. Date resolution
10. Compliance
11. Human review
12. Main dashboard/report
13. Search
14. Sentiment
15. Testing
16. Deployment
17. Polish
```

Do not build the UI around fake/mock AI results and then redesign the backend around it. Establish the data contracts early.

## 23. Final MVP Demonstration

The ideal demo should show one complete call:

```text
Upload recording
      ↓
Processing
      ↓
Speaker-diarized transcript
      ↓
Summary
      ↓
Decisions
      ↓
Action items + owners + dates
      ↓
Blocker
      ↓
Compliance observation
      ↓
Evidence lines
      ↓
Human review item
      ↓
Reviewer decision
```

Use the debt-collection example pattern from the assignment as the primary demonstration because it naturally proves:
- action extraction,
- owner extraction,
- relative-date resolution,
- blocker detection,
- evidence grounding,
- compliance escalation,
- human review.
