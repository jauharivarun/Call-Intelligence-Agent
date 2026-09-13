# Call Intelligence AI Agent — Product Requirements Document (PRD)

## 1. Product Overview

**Product name:** Call Intelligence AI Agent

**One-line idea:**  
A post-call AI workflow that converts meeting/call recordings into structured, trustworthy notes where important claims are grounded in exact transcript lines and uncertain or risky items are escalated for human review.

The product is not simply a summarizer. Its main value is **reliable, evidence-backed call intelligence**.

## 2. Problem Statement

Teams conduct sales, support, debt-collection, and internal calls every day. After a call, someone still has to determine what happened, what was decided, who agreed to do what, when it is due, what is blocking progress, and whether anything risky or non-compliant occurred.

A normal LLM summary is not sufficient because a model can invent action items, owners, dates, or compliance claims. The system therefore must treat the original transcript as the source of truth and require evidence for extracted facts.

## 3. Target Users

### Primary user
A team member, manager, QA reviewer, operations user, or analyst who needs reliable post-call intelligence.

### Secondary user
A human reviewer who handles ambiguous, risky, sensitive, or permission-dependent items.

## 4. Primary Use Cases

1. Debt-collection call analysis.
2. Customer-support call analysis.
3. Sales-call analysis.
4. Internal meeting/standup analysis.

The first implementation should use **debt-collection calls as the strongest demo scenario**, because the assignment provides explicit examples and compliance categories for this domain.

## 5. Core User Journey

1. User uploads a call recording.
2. User supplies/confirm call metadata such as call date and domain.
3. System transcribes the audio and identifies speakers.
4. System creates a numbered transcript.
5. AI extracts summary, decisions, action items, owners, dates, blockers, and compliance observations.
6. Every extracted item is mapped to supporting transcript line(s).
7. The system verifies whether the evidence actually supports the extracted claim.
8. Relative dates are normalized using the call date.
9. Compliance/risk rules are evaluated.
10. Low-confidence, ambiguous, sensitive, risky, or authority-dependent items enter a human-review queue.
11. User views the final structured report and can inspect evidence.
12. Optional bonus: users can search across stored transcripts and inspect sentiment/profanity/angry-customer signals.

## 6. Core Features

### F1 — Audio Upload
- Upload supported audio recordings.
- Show upload/processing status.
- Reject unsupported or invalid files.
- Store the original recording reference.

### F2 — Speaker-Diarized Transcription
- Convert audio to text.
- Identify speakers.
- Produce stable transcript segments/lines.
- Preserve timestamps where available.
- Assign deterministic line numbers after transcription.

### F3 — Call Context
Store:
- Call date.
- Domain/type.
- Optional title/tag.
- Speaker metadata if available.

Call date is required for reliable resolution of relative dates such as "Friday" or "next month."

### F4 — Structured Intelligence Extraction
Generate:
- Short tag.
- Plain-language summary.
- Decisions.
- Action items.
- Owners.
- Start/due dates when stated or inferable from explicit relative dates.
- Blockers.
- Compliance observations.
- Confidence.
- Human-review items.

### F5 — Evidence Grounding
Every extracted decision, action item, blocker, compliance observation, and review item must include exact source transcript line(s).

The application must display the original transcript text as evidence rather than an LLM-generated quotation.

### F6 — Evidence Verification
The system must verify claims against transcript evidence.

Verification should:
- Find candidate transcript lines.
- Compare the extracted claim with candidate evidence semantically.
- Reject unsupported claims.
- Lower confidence when evidence is partial or ambiguous.
- Route unsupported/ambiguous claims to human review.

### F7 — Relative Date Resolution
Examples:
- "Friday" → date based on call date.
- "15th of next month" → normalized calendar date based on call date.

The system must preserve the original phrase as well as the normalized date.

### F8 — Compliance Analysis
At minimum support domain-aware checks for:
- Potential compliance issues.
- Customer recording/consent ambiguity.
- Settlement/approval situations.
- Cease-and-desist language.
- Legal mentions.
- Wrong-number mentions.

Compliance observations are classified:
- Green = no significant issue / positive behavior.
- Yellow = requires attention or verification.
- Red = potentially serious issue requiring human attention.

### F9 — Human Review Queue
Review items should contain:
- Reason for review.
- Risk/category.
- Extracted claim if applicable.
- Exact evidence lines.
- Confidence.
- Status.
- Reviewer decision/notes.

### F10 — Transcript Search (Bonus)
Search across stored transcripts using normal text search first. The assignment does not require vector search.

### F11 — Sentiment / Conversation Signals (Bonus)
Capture:
- Positive/negative sentiment.
- Profanity.
- Angry-customer signal.
- Overall call sentiment.

These are secondary to evidence-grounded intelligence.

## 7. User Stories

### Upload
- As a user, I want to upload a recording so that the system can analyze the call.
- As a user, I want to see processing status so I know whether analysis is complete.

### Intelligence
- As a user, I want a short summary so I can understand the call quickly.
- As a user, I want decisions separated from general discussion.
- As a user, I want action items with owners and due dates.
- As a user, I want blockers clearly identified.

### Trust
- As a user, I want every important claim linked to exact transcript lines.
- As a user, I want unsupported claims to be flagged instead of presented as facts.
- As a reviewer, I want to see why an item was escalated.

### Compliance
- As a QA user, I want risky statements highlighted.
- As a reviewer, I want the original evidence before deciding whether an issue is real.

### Search
- As a user, I want to search historical transcripts for terms or phrases.

## 8. Trust and Product Rules

1. **Transcript is the source of truth.**
2. **No important claim without evidence.**
3. Evidence must reference original transcript lines.
4. Do not invent owners.
5. Do not invent dates.
6. Relative dates may be normalized only when the reference date is known.
7. Unclear ownership → human review.
8. Vague deadlines → human review.
9. Potential compliance problem → human review.
10. Decisions requiring authority/judgment → human review.
11. Sensitive information should be handled conservatively.
12. Low confidence should result in review rather than confident guessing.

## 9. MVP Scope

### Must ship
- Audio upload.
- Transcription.
- Speaker diarization or speaker-labelled transcript.
- Numbered transcript.
- Call date/domain metadata.
- Summary.
- Decisions.
- Action items.
- Owners.
- Dates.
- Blockers.
- Compliance observations.
- Evidence grounding.
- Evidence verification.
- Confidence.
- Human-review queue.
- Report UI.
- Persistent storage.

### Version 1 exclusions
- Live meeting assistant.
- Real-time interruption/coaching.
- External knowledge RAG as a core dependency.
- Vector database for transcript storage/grounding.
- Autonomous external actions such as sending emails or changing CRM records.
- Fully automated compliance/legal decisions.
- Enterprise SSO.
- Complex billing/subscriptions.
- Multi-tenant enterprise administration unless specifically required.

## 10. Success Metrics

For the assignment/demo, prioritize measurable quality over scale:

- **Evidence coverage:** percentage of extracted factual items with valid transcript evidence.
- **Unsupported-claim rate:** percentage of final accepted items that cannot be supported by transcript evidence.
- **Review precision:** percentage of human-review items that are genuinely ambiguous/risky.
- **Date accuracy:** correctness of normalized relative dates.
- **Extraction completeness:** important decisions/actions/blockers captured from the transcript.
- **Processing success rate:** recordings successfully processed end-to-end.
- **Traceability:** reviewer can reach exact evidence lines from every important report item.

## 11. Assumptions

- The initial application is post-call, not real-time.
- The call date is available or entered by the user.
- A single call can be processed independently.
- The first demo domain is debt collection.
- The system can use an LLM, but the LLM is not the final source of truth.
- Transcript search can use conventional database text search.
- Compliance rules are initially configuration/rule driven rather than dependent on a policy-document RAG system.

## 12. Definition of Done

A call is considered successfully analyzed only when:
1. A transcript exists.
2. The transcript has speaker labels and stable line numbers.
3. Structured intelligence has been generated.
4. Important extracted items have evidence.
5. Evidence has been verified.
6. Relative dates have been resolved when possible.
7. Compliance checks have run.
8. Review-required items have been separated from accepted outputs.
9. The final report is persisted and viewable.
