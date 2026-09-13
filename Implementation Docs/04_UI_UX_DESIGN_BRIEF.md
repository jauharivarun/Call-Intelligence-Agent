# Call Intelligence AI Agent — UI/UX Design Brief

## 1. Design Direction

The product should feel like a **professional operations/QA intelligence dashboard**, not a generic AI chatbot.

Desired characteristics:
- Clean.
- Trustworthy.
- Evidence-focused.
- Information-dense without feeling cluttered.
- Professional.
- Easy to scan.
- Strong visual distinction between accepted intelligence and human-review items.

Avoid:
- Excessive gradients.
- Overly playful AI visuals.
- Chatbot-style primary layout.
- Decorative elements that compete with evidence.
- Hiding confidence/risk information.

## 2. Visual Hierarchy

The most important information should appear in this order:

1. Call status and high-level summary.
2. Human-review/risk alerts.
3. Action items and decisions.
4. Blockers.
5. Compliance observations.
6. Supporting evidence.
7. Full transcript.

The transcript should remain accessible but should not dominate the initial report.

## 3. Color System

Use a restrained neutral base with semantic status colors:

- Neutral: application background and standard content.
- Green: compliant/positive.
- Yellow/amber: caution/review.
- Red: high-risk/urgent review.
- Blue/primary accent: navigation, actions, evidence links.

Do not use color alone to convey meaning. Pair color with labels/icons/text.

## 4. Typography

Use a modern sans-serif UI font.

Suggested hierarchy:
- Page title: large/bold.
- Section title: medium/bold.
- Card title: semibold.
- Body: readable regular.
- Metadata: smaller muted text.
- Transcript: highly legible, with clear speaker differentiation.

Avoid very small body text.

## 5. Layout

Desktop:
- Left navigation sidebar.
- Main content area.
- Optional right-side evidence/transcript panel.

Suggested analysis layout:

```text
┌────────────┬──────────────────────────────────────┐
│ Navigation │ Call Header                         │
│            ├──────────────────────────────────────┤
│ Dashboard  │ Summary                              │
│ Calls      │                                      │
│ Reviews    ├──────────────────────────────────────┤
│ Search     │ Action Items / Decisions             │
│            │                                      │
│            ├──────────────────────────────────────┤
│            │ Compliance / Blockers / Review       │
│            │                                      │
└────────────┴──────────────────────────────────────┘
```

When evidence is opened, use a side panel or expandable panel.

## 6. Cards

Cards should be:
- Flat or lightly elevated.
- Rounded moderately.
- Consistent padding.
- Strong headings.
- Minimal decoration.

Every intelligence card should have a consistent evidence affordance:

```text
Evidence · Lines 7–8 →
```

## 7. Action Item Component

Example:

```text
FOLLOW UP WITH SUPERVISOR

Owner        Marcus
Due          03 Jul 2026
Confidence   High

Evidence · Line 8 →
```

If inferred:
```text
Due · 15 Aug 2026
From "15th of next month"
```

If review required:
```text
⚠ Human review required
```

## 8. Review Item Component

Review items should be visually prominent.

Example:

```text
⚠ HUMAN REVIEW REQUIRED

Settlement split may require supervisor approval.

Why flagged:
Potential deviation from standard terms.

Evidence · Line 8 →

[Open Evidence] [Review]
```

Do not hide review items inside a generic "warnings" section.

## 9. Compliance Display

Use a compact severity indicator:

```text
GREEN   No significant issue
YELLOW  Review recommended
RED     Human attention required
```

Each observation should show:
- Severity.
- Category.
- Explanation.
- Evidence.
- Confidence.

## 10. Transcript Design

Transcript should look like a readable professional transcript, not a chat application.

Example:

```text
7  CONSUMER   00:02:10
   That's still too much right now. Could I do $700 now
   and $700 next month?

8  AGENT      00:02:18   [EVIDENCE]
   Let me note that — $700 today and $700 on the 15th
   of next month...
```

Evidence lines:
- Highlight the whole line/segment.
- Provide a clear "Evidence" indicator.
- Keep original text unchanged.

## 11. Upload UI

Use a large drag-and-drop zone:

```text
┌────────────────────────────────────┐
│                                    │
│       Drop recording here          │
│       or Browse files              │
│                                    │
│       WAV · MP3 · M4A ...          │
│                                    │
└────────────────────────────────────┘
```

Below it:
- Call date.
- Domain.
- Optional title.
- Analyze button.

## 12. Processing UI

Show a vertical pipeline rather than a generic spinner.

```text
✓ Audio uploaded
✓ Transcription
✓ Speaker identification
● Intelligence extraction
○ Evidence verification
○ Compliance checks
○ Final report
```

This reassures the user that the system is actually performing multiple stages.

## 13. Dashboard

Top area:
- Total calls.
- Calls needing review.
- Processing calls.
- High-risk calls.

Main area:
- Recent calls table.
- Status.
- Risk.
- Review count.
- Date.

Avoid excessive analytics in the MVP.

## 14. Responsive Behavior

Desktop is the primary target because the product is operational/QA oriented.

Tablet:
- Collapse navigation.
- Stack cards where necessary.

Mobile:
- Single-column layout.
- Evidence opens as full-width panel/modal.
- Transcript remains readable.
- Tables become cards where necessary.

## 15. Accessibility

- Keyboard-accessible actions.
- Visible focus states.
- Semantic HTML.
- Sufficient contrast.
- Do not rely only on color.
- Clear error text.
- Status changes should be understandable without animation.

## 16. Interaction Principles

### Evidence first
Every important AI claim should have an obvious path to evidence.

### Progressive disclosure
Show concise information first; expose details on click.

### Human review is a feature
Do not visually frame review items as system failures. They represent intentional caution.

### Confidence must be understandable
Avoid showing a raw number without context. Prefer:
- High
- Medium
- Low
with optional numeric score in details.

### Original text is authoritative
Evidence panels must display transcript text exactly as stored.

## 17. UI States To Design

Every major component should support:
- Loading.
- Empty.
- Success.
- Error.
- Disabled.
- Review-required.
- Low-confidence.

## 18. Visual Tone

The final UI should communicate:

> "This system helps me make decisions, but it also shows me when I should verify something."

That trust relationship is more important than making the interface look like a futuristic AI product.
