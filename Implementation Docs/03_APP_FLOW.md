# Call Intelligence AI Agent — App Flow Document

## 1. Product Flow

```text
Login
  ↓
Dashboard
  ↓
Upload Call
  ↓
Call Metadata
  ↓
Processing
  ↓
Call Analysis
  ├── Summary
  ├── Decisions
  ├── Action Items
  ├── Blockers
  ├── Compliance
  ├── Sentiment
  └── Human Review
  ↓
Transcript + Evidence
```

## 2. Screen Inventory

### Screen 1 — Login
Purpose: authenticate the user.

Elements:
- Email/username.
- Password.
- Login button.
- Error message.

Success:
- Redirect to Dashboard.

Error:
- Invalid credentials message.

### Screen 2 — Dashboard
Purpose: show previously analyzed calls and current processing jobs.

Elements:
- Header/navigation.
- "Upload Call" button.
- Recent calls table/cards.
- Status.
- Call date.
- Domain.
- Risk level.
- Review count.
- Search/filter controls.

Empty state:
> No calls analyzed yet. Upload your first call to begin.

Processing state:
> Analysis in progress.

### Screen 3 — Upload Call
Elements:
- Drag-and-drop upload.
- File picker.
- File name.
- File size/type.
- Call date.
- Call type/domain selector.
- Optional call title.
- Analyze button.

Validation:
- Unsupported format.
- File too large.
- Missing call date.
- Missing domain.

Success:
- Create call.
- Redirect to Processing screen.

### Screen 4 — Processing
Show pipeline stages:

```text
✓ Uploaded
✓ Transcribing
✓ Identifying speakers
● Extracting intelligence
○ Verifying evidence
○ Running compliance checks
○ Finalizing report
```

Do not expose technical stack details unnecessarily.

Failure:
- Explain stage failure.
- Offer Retry.

### Screen 5 — Call Analysis
Main report screen.

Sections:
1. Header/metadata.
2. Summary.
3. Risk/sentiment overview.
4. Decisions.
5. Action items.
6. Blockers.
7. Compliance.
8. Human review.
9. Transcript/evidence panel.

## 3. Analysis Screen Interactions

### Evidence click
When user clicks "Evidence: Lines 7–8":
- Open transcript panel.
- Scroll to lines 7–8.
- Highlight those lines.
- Show speaker and timestamp if available.

### Action item
Display:
- Task.
- Owner.
- Start date.
- Due date.
- Confidence.
- Evidence.

If owner is unclear:
> Owner unclear — Human review required.

If date is inferred:
> Due: 15 Aug 2026
> Original phrase: "15th of next month"

### Decision
Display:
- Decision text.
- Confidence.
- Evidence lines.
- Review badge if uncertain.

### Blocker
Display:
- Blocker.
- Impact.
- Evidence.
- Review status.

## 4. Compliance Flow

Compliance section displays observations grouped by severity:

```text
GREEN
No significant issue detected.

YELLOW
Potential issue — review recommended.

RED
Potential serious issue — human review required.
```

Clicking an observation opens:
- Explanation.
- Category.
- Evidence.
- Confidence.
- Review state.

For debt collection, show specific categories such as:
- Cease and desist.
- Legal mention.
- Bankruptcy.
- Wrong number.
- Recording consent ambiguity.
- Settlement/approval concern.

## 5. Human Review Flow

### Review Queue
Accessible from dashboard/navigation.

Each row:
- Call.
- Category.
- Issue.
- Severity.
- Confidence.
- Created time.
- Status.

### Review Detail
Show:
- Issue.
- Why it was flagged.
- Original extracted claim.
- Exact transcript evidence.
- Relevant surrounding lines.
- Suggested system interpretation.
- Reviewer note field.

Actions:
- Approve.
- Reject.
- Escalate.
- Save note.

### Review principles
The reviewer should never have to search the entire transcript manually to understand why an item was flagged.

## 6. Transcript View

Display:

```text
Line | Speaker | Timestamp | Text
----------------------------------
7    | Consumer| 00:02:10 | ...
8    | Agent   | 00:02:18 | ...
```

Evidence lines should be visually highlighted.

The user can:
- Scroll.
- Search within transcript.
- Jump to evidence.
- Copy text.

## 7. Search Flow (Bonus)

Dashboard/search page:

```text
Search transcripts
[ supervisor approval                 ] [Search]

Results:
Call #123 — 3 matches
Call #087 — 1 match
```

Click result:
- Open call.
- Jump to matching transcript line.

Use normal database text search for MVP.

## 8. Sentiment Flow (Bonus)

On analysis page:

```text
Overall Sentiment: Negative
Customer Sentiment: Negative
Agent Sentiment: Neutral
Profanity: Detected
Angry Customer: Yes
```

Each signal should optionally show evidence lines.

Do not make sentiment the basis for compliance decisions by itself.

## 9. Navigation

Primary navigation:
- Dashboard
- Upload Call
- Review Queue
- Transcript Search

Secondary:
- Call details.
- User/account menu.
- Logout.

## 10. Empty States

### Dashboard
No calls:
> Upload a call recording to generate your first intelligence report.

### Review queue
No pending reviews:
> No items require human review.

### Search
No results:
> No transcript matches found.

### Transcript
Transcript unavailable:
> Transcript could not be generated. Check processing status.

## 11. Error States

### Upload
> This file format is not supported.

### Processing
> We could not process this recording. You can retry the analysis.

### AI extraction
> Intelligence extraction failed. The transcript is still available.

### Evidence verification
> Some extracted items could not be verified and were moved to human review.

### Permission
> You do not have permission to view this call.

## 12. Success States

After analysis:
> Call analyzed successfully. 8 intelligence items found; 2 require human review.

After review:
> Review decision saved.

After retry:
> Processing restarted.

## 13. Recommended UX Principle

The user should be able to answer three questions immediately:

1. **What happened?**
2. **What needs to happen next?**
3. **Why should I trust this output?**

The third question is answered through visible evidence links and review flags.

## 14. Important Product Constraint

Do not create a chat-first interface as the main experience. The assignment is centered on a structured call report and evidence review.

A future conversational interface can be added later, but the MVP should make the structured output the primary UI.
