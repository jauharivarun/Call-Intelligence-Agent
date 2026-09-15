import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type Analysis, type CallDetail, type TranscriptSegment } from '../api'
import { useAuth } from '../auth'
import RecordingPlayer from '../components/RecordingPlayer'

function severityClass(severity: string) {
  if (severity === 'RED') return 'red'
  if (severity === 'YELLOW') return 'yellow'
  if (severity === 'GREEN') return 'green'
  return 'neutral'
}

function speakerRole(label: string) {
  const lower = label.toLowerCase()
  if (lower.includes('agent') || lower.includes('rep') || lower.includes('collector')) return 'agent'
  if (lower.includes('customer') || lower.includes('caller') || lower.includes('consumer')) {
    return 'customer'
  }
  return ''
}

function buildRiskStrip(analysis: Analysis) {
  const openReviews = analysis.review_items.filter(
    (item) => !item.is_resolved && !['APPROVED', 'REJECTED', 'ESCALATED'].includes(item.status),
  )
  const redCompliance = analysis.compliance_observations.filter((c) => c.severity === 'RED').length
  const yellowCompliance = analysis.compliance_observations.filter((c) => c.severity === 'YELLOW').length
  const blockers = analysis.blockers.length
  const reviewActions = analysis.action_items.filter((a) => a.review_required).length
  const angry = analysis.sentiment?.angry_customer_detected

  const openCount = openReviews.length
  const reviewTone = openCount > 0 ? (openReviews.some((r) => r.severity === 'RED') ? 'tone-risk' : 'tone-caution') : 'tone-ok'
  const complianceTone = redCompliance > 0 ? 'tone-risk' : yellowCompliance > 0 ? 'tone-caution' : 'tone-ok'
  const blockerTone = blockers > 0 ? 'tone-caution' : 'tone-ok'
  const signalTone = angry || reviewActions > 0 ? (angry ? 'tone-risk' : 'tone-caution') : 'tone-ok'

  return [
    {
      label: 'Human review',
      value: openCount === 0 ? 'Clear' : `${openCount} open`,
      tone: reviewTone,
    },
    {
      label: 'Compliance',
      value:
        redCompliance > 0
          ? `${redCompliance} red`
          : yellowCompliance > 0
            ? `${yellowCompliance} caution`
            : 'No flags',
      tone: complianceTone,
    },
    {
      label: 'Blockers',
      value: blockers === 0 ? 'None' : `${blockers} flagged`,
      tone: blockerTone,
    },
    {
      label: 'Signals',
      value: angry
        ? 'Angry customer'
        : reviewActions > 0
          ? `${reviewActions} need review`
          : analysis.sentiment?.overall_sentiment || 'Stable',
      tone: signalTone,
    },
  ] as const
}

export default function CallDetailPage() {
  const { id = '' } = useParams()
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin' || user?.is_staff
  const [call, setCall] = useState<CallDetail | null>(null)
  const [transcript, setTranscript] = useState<TranscriptSegment[]>([])
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [activeLines, setActiveLines] = useState<number[]>([])
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    const c = await api.getCall(id)
    setCall(c)
    if (['COMPLETED', 'FAILED', 'ANALYZING', 'VERIFYING', 'COMPLIANCE_CHECK', 'DIARIZING', 'TRANSCRIBING', 'PROCESSING'].includes(c.status)) {
      try {
        setTranscript(await api.getTranscript(id))
      } catch {
        setTranscript([])
      }
    }
    if (c.status === 'COMPLETED') {
      try {
        setAnalysis(await api.getAnalysis(id))
      } catch {
        setAnalysis(null)
      }
    }
  }, [id])

  useEffect(() => {
    refresh().catch((e) => setError(e.message))
  }, [refresh])

  useEffect(() => {
    if (!call || call.status === 'COMPLETED' || call.status === 'FAILED') return
    const t = setInterval(() => {
      refresh().catch(() => undefined)
    }, 2000)
    return () => clearInterval(t)
  }, [call, refresh])

  function showEvidence(segments: TranscriptSegment[]) {
    setActiveLines(segments.map((s) => s.line_number))
    const first = segments[0]
    if (first) {
      document.getElementById(`line-${first.line_number}`)?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      })
    }
  }

  async function reanalyze() {
    setError('')
    try {
      await api.reanalyze(id)
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Reanalyze failed')
    }
  }

  const riskStrip = useMemo(() => (analysis ? buildRiskStrip(analysis) : null), [analysis])

  if (!call) {
    return (
      <div className="stack">
        {error ? <div className="error">{error}</div> : <p className="muted">Loading call…</p>}
      </div>
    )
  }

  const showPlayer = call.status === 'COMPLETED' && Boolean(call.recording_path)

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>{call.title || 'Call analysis'}</h1>
          <p>
            {call.domain} · {call.call_date} ·{' '}
            <span className={`badge ${call.status === 'COMPLETED' ? 'green' : call.status === 'FAILED' ? 'red' : 'yellow'}`}>
              {call.status}
            </span>
          </p>
        </div>
        <div className="action-row">
          <Link className="btn secondary" to="/">
            Back
          </Link>
          {isAdmin && (
            <button className="btn secondary" onClick={reanalyze}>
              Reanalyze
            </button>
          )}
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {call.error_message && <div className="error">{call.error_message}</div>}

      {riskStrip && (
        <div className="risk-strip" aria-label="Call risk overview">
          {riskStrip.map((chip) => (
            <div key={chip.label} className={`risk-chip ${chip.tone}`}>
              <span className="label">{chip.label}</span>
              <div className="value">{chip.value}</div>
            </div>
          ))}
        </div>
      )}

      <div className="pipeline-player-row">
        <div className="panel">
          <strong>Pipeline</strong>
          {call.jobs?.length > 0 ? (
            <div className="pipeline" style={{ marginTop: '0.75rem' }}>
              {call.jobs.map((job) => (
                <span
                  key={job.id}
                  className={
                    job.status === 'SUCCEEDED'
                      ? 'done'
                      : job.status === 'FAILED'
                        ? 'failed'
                        : job.status === 'RUNNING'
                          ? 'running'
                          : ''
                  }
                >
                  {job.stage}: {job.status}
                </span>
              ))}
            </div>
          ) : (
            <p className="muted" style={{ margin: '0.75rem 0 0' }}>
              No pipeline jobs yet.
            </p>
          )}
        </div>
        {showPlayer ? (
          <RecordingPlayer callId={call.id} enabled />
        ) : (
          <div className="panel recording-player">
            <strong>Recording</strong>
            <p className="muted" style={{ margin: '0.75rem 0 0' }}>
              {call.status === 'COMPLETED'
                ? 'Recording file unavailable.'
                : 'Player unlocks after analysis completes.'}
            </p>
          </div>
        )}
      </div>

      {call.status !== 'COMPLETED' && call.status !== 'FAILED' && (
        <div className="panel">
          <p className="muted" style={{ margin: 0 }}>
            Processing in progress. This page refreshes automatically.
          </p>
        </div>
      )}

      {analysis && (
        <div className="grid-2">
          <div className="stack">
            <div className="panel">
              <h2 style={{ marginTop: 0 }}>{analysis.tag}</h2>
              <p>{analysis.summary}</p>
              {analysis.sentiment && (
                <div className="meta-row">
                  <span>Overall: {analysis.sentiment.overall_sentiment}</span>
                  <span>Customer: {analysis.sentiment.customer_sentiment}</span>
                  {analysis.sentiment.angry_customer_detected && (
                    <span className="badge red">Angry customer</span>
                  )}
                  {analysis.sentiment.profanity_detected && (
                    <span className="badge yellow">Profanity</span>
                  )}
                </div>
              )}
            </div>

            <div className="panel">
              <h2 style={{ marginTop: 0 }}>Action items</h2>
              {analysis.action_items.length === 0 && <p className="muted">None</p>}
              {analysis.action_items.map((item) => (
                <div className="item-card" key={item.id}>
                  <h3>{item.task}</h3>
                  <div className="meta-row">
                    <span>Owner: {item.owner_name || '—'}</span>
                    <span>
                      Due: {item.due_date || '—'}
                      {item.original_due_phrase ? ` (“${item.original_due_phrase}”)` : ''}
                    </span>
                    <span className={`badge ${item.verification_status === 'SUPPORTED' ? 'green' : 'yellow'}`}>
                      {item.verification_status}
                    </span>
                    {item.review_required && <span className="badge yellow">Review</span>}
                  </div>
                  <button className="evidence-link" onClick={() => showEvidence(item.evidence)}>
                    Evidence · Lines {item.evidence.map((e) => e.line_number).join(', ') || '—'} →
                  </button>
                </div>
              ))}
            </div>

            <div className="panel">
              <h2 style={{ marginTop: 0 }}>Decisions</h2>
              {analysis.decisions.map((item) => (
                <div className="item-card" key={item.id}>
                  <h3>{item.text}</h3>
                  <button className="evidence-link" onClick={() => showEvidence(item.evidence)}>
                    Evidence · Lines {item.evidence.map((e) => e.line_number).join(', ') || '—'} →
                  </button>
                </div>
              ))}
            </div>

            <div className="panel">
              <h2 style={{ marginTop: 0 }}>Blockers</h2>
              {analysis.blockers.length === 0 && <p className="muted">None</p>}
              {analysis.blockers.map((item) => (
                <div className="item-card" key={item.id}>
                  <h3>{item.text}</h3>
                  {item.impact && <p className="muted">{item.impact}</p>}
                  <button className="evidence-link" onClick={() => showEvidence(item.evidence)}>
                    Evidence · Lines {item.evidence.map((e) => e.line_number).join(', ') || '—'} →
                  </button>
                </div>
              ))}
            </div>

            <div className="panel">
              <h2 style={{ marginTop: 0 }}>Compliance</h2>
              {analysis.compliance_observations.length === 0 && (
                <p className="muted">No compliance observations.</p>
              )}
              {analysis.compliance_observations.map((item) => (
                <div className="item-card" key={item.id}>
                  <div className="meta-row">
                    <span className={`badge ${severityClass(item.severity)}`}>{item.severity}</span>
                    <strong>{item.category}</strong>
                  </div>
                  <p>{item.observation}</p>
                  <button className="evidence-link" onClick={() => showEvidence(item.evidence)}>
                    Evidence · Lines {item.evidence.map((e) => e.line_number).join(', ') || '—'} →
                  </button>
                </div>
              ))}
            </div>

            <div className="panel">
              <h2 style={{ marginTop: 0 }}>Review items for this call</h2>
              {analysis.review_items.length === 0 && <p className="muted">No review items.</p>}
              {analysis.review_items.map((item) => {
                const resolved =
                  item.is_resolved ||
                  ['APPROVED', 'REJECTED', 'ESCALATED'].includes(item.status)
                return (
                  <div className="item-card" key={item.id}>
                    <div className="meta-row">
                      <span className={`badge ${severityClass(item.severity)}`}>{item.severity}</span>
                      <span
                        className={`badge ${
                          item.status === 'APPROVED'
                            ? 'green'
                            : item.status === 'REJECTED'
                              ? 'red'
                              : item.status === 'ESCALATED'
                                ? 'yellow'
                                : 'neutral'
                        }`}
                      >
                        {resolved ? `Reviewed · ${item.status}` : item.status}
                      </span>
                      <strong>{item.category}</strong>
                    </div>
                    <p>{item.reason}</p>
                    {resolved && (
                      <p className="muted">
                        Decision by {item.reviewer_username || '—'}
                        {item.reviewed_at ? ` at ${new Date(item.reviewed_at).toLocaleString()}` : ''}
                        {item.reviewer_note ? ` · Note: ${item.reviewer_note}` : ''}
                      </p>
                    )}
                    <Link className="link-accent" to="/reviews">
                      Open reviews →
                    </Link>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="panel">
            <h2 style={{ marginTop: 0 }}>Transcript</h2>
            <div className="transcript">
              {transcript.map((line) => {
                const role = speakerRole(line.speaker_label)
                return (
                  <div
                    key={line.id}
                    id={`line-${line.line_number}`}
                    className={`transcript-line ${activeLines.includes(line.line_number) ? 'active' : ''}`}
                  >
                    <strong className="line-no">{line.line_number}</strong>
                    <span className={`speaker ${role}`} data-role={role || undefined}>
                      {line.speaker_label}
                    </span>
                    <span>{line.text}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {!analysis && transcript.length > 0 && (
        <div className="panel">
          <h2 style={{ marginTop: 0 }}>Transcript (in progress)</h2>
          <div className="transcript">
            {transcript.map((line) => {
              const role = speakerRole(line.speaker_label)
              return (
                <div key={line.id} className="transcript-line">
                  <strong className="line-no">{line.line_number}</strong>
                  <span className={`speaker ${role}`} data-role={role || undefined}>
                    {line.speaker_label}
                  </span>
                  <span>{line.text}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
