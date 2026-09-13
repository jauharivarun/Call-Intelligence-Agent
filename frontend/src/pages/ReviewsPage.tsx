import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type ReviewItem } from '../api'

const RESOLVED = new Set(['APPROVED', 'REJECTED', 'ESCALATED'])

function statusBadgeClass(status: string) {
  if (status === 'APPROVED') return 'green'
  if (status === 'REJECTED') return 'red'
  if (status === 'ESCALATED') return 'yellow'
  return 'neutral'
}

function severityClass(severity: string) {
  if (severity === 'RED') return 'red'
  if (severity === 'YELLOW') return 'yellow'
  if (severity === 'GREEN') return 'green'
  return 'neutral'
}

function formatWhen(iso: string | null | undefined) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function decisionBannerClass(status: string) {
  if (status === 'APPROVED') return 'approved'
  if (status === 'REJECTED') return 'rejected'
  return 'escalated'
}

export default function ReviewsPage() {
  const [items, setItems] = useState<ReviewItem[]>([])
  const [selected, setSelected] = useState<ReviewItem | null>(null)
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('OPEN')
  const [busy, setBusy] = useState(false)
  const [editingResolved, setEditingResolved] = useState(false)

  async function load(activeFilter = filter) {
    const data = await api.listReviews(activeFilter || undefined)
    setItems(data)
    return data
  }

  useEffect(() => {
    setSelected(null)
    setNote('')
    setError('')
    setEditingResolved(false)
    load(filter).catch((e) => setError(e.message))
  }, [filter])

  function selectItem(item: ReviewItem) {
    setSelected(item)
    setNote(item.reviewer_note || '')
    setError('')
    setEditingResolved(false)
  }

  async function decide(decision: string) {
    if (!selected) return
    const alreadyResolved = selected.is_resolved || RESOLVED.has(selected.status)
    if (alreadyResolved && !editingResolved && decision !== 'OPEN') return

    setBusy(true)
    setError('')
    try {
      const updated = await api.decideReview(selected.id, decision, note)
      setEditingResolved(false)

      if (decision === 'OPEN') {
        setFilter('OPEN')
        const openItems = await load('OPEN')
        const match = openItems.find((r) => r.id === updated.id) || updated
        setSelected(match)
        setNote(match.reviewer_note || '')
        return
      }

      // Keep resolved edits in the resolved view; first decisions also land here.
      setFilter('RESOLVED')
      const resolved = await load('RESOLVED')
      const match = resolved.find((r) => r.id === updated.id) || updated
      setSelected(match)
      setNote(match.reviewer_note || '')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Decision failed')
    } finally {
      setBusy(false)
    }
  }

  const isOpenView = filter === 'OPEN'
  const selectedResolved =
    !!selected && (selected.is_resolved || RESOLVED.has(selected.status))
  const canAct = !!selected && (!selectedResolved || editingResolved)

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>{isOpenView ? 'Review queue' : 'Resolved logs'}</h1>
          <p>
            {isOpenView
              ? 'Decide open items. After approve / reject / escalate they move to Resolved logs.'
              : 'History of reviewed items. Use Edit decision to correct accidental resolutions.'}
          </p>
        </div>
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="OPEN">Open queue</option>
          <option value="RESOLVED">Resolved logs</option>
          <option value="APPROVED">Approved only</option>
          <option value="REJECTED">Rejected only</option>
          <option value="ESCALATED">Escalated only</option>
          <option value="">All</option>
        </select>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="grid-2">
        <div className="panel">
          {items.length === 0 && (
            <p className="muted">
              {isOpenView ? 'No open review items.' : 'No resolved items in this view.'}
            </p>
          )}
          {items.map((item) => {
            const resolved = item.is_resolved || RESOLVED.has(item.status)
            const isSelected = selected?.id === item.id
            return (
              <button
                key={item.id}
                type="button"
                className={`item-card ${isSelected ? 'selected' : ''}`}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  cursor: 'pointer',
                }}
                onClick={() => selectItem(item)}
              >
                <div className="meta-row">
                  <span className={`badge ${severityClass(item.severity)}`}>{item.severity}</span>
                  <span className={`badge ${statusBadgeClass(item.status)}`}>
                    {resolved ? `Reviewed · ${item.status}` : item.status}
                  </span>
                  <strong>{item.category}</strong>
                </div>
                <div>{item.reason}</div>
                <div className="muted" style={{ marginTop: '0.35rem' }}>
                  {item.call_title || item.call}
                  {resolved && item.reviewed_at
                    ? ` · ${formatWhen(item.reviewed_at)}`
                    : ''}
                </div>
              </button>
            )
          })}
        </div>
        <div className="panel decision-pane">
          {!selected ? (
            <p className="muted">Select a review item.</p>
          ) : (
            <div className="stack">
              <div className="meta-row">
                <span className={`badge ${statusBadgeClass(selected.status)}`}>
                  {selectedResolved ? `Reviewed · ${selected.status}` : selected.status}
                </span>
                <span className={`badge ${severityClass(selected.severity)}`}>
                  {selected.severity}
                </span>
              </div>
              <h2 style={{ margin: 0 }}>{selected.category}</h2>
              <p>{selected.reason}</p>
              <Link className="link-accent" to={`/calls/${selected.call}`}>
                Open call →
              </Link>

              {selectedResolved && (
                <div className={`decision-banner ${decisionBannerClass(selected.status)}`}>
                  <strong>Decision recorded</strong>
                  <div className="meta-row" style={{ marginTop: '0.5rem' }}>
                    <span>Outcome: {selected.status}</span>
                    <span>By: {selected.reviewer_username || '—'}</span>
                    <span>At: {formatWhen(selected.reviewed_at)}</span>
                  </div>
                  {selected.reviewer_note ? (
                    <p style={{ marginBottom: 0 }}>Note: {selected.reviewer_note}</p>
                  ) : (
                    <p className="muted" style={{ marginBottom: 0 }}>
                      No reviewer note.
                    </p>
                  )}
                </div>
              )}

              <div>
                <strong>Evidence</strong>
                {selected.evidence.length === 0 && (
                  <p className="muted">No evidence lines linked.</p>
                )}
                {selected.evidence.map((e) => (
                  <div key={e.id} className="item-card">
                    Line {e.line_number} · {e.speaker_label}: {e.text}
                  </div>
                ))}
              </div>

              {selectedResolved && !editingResolved ? (
                <div className="action-row">
                  <button
                    type="button"
                    className="btn secondary"
                    disabled={busy}
                    onClick={() => {
                      setNote(selected.reviewer_note || '')
                      setEditingResolved(true)
                    }}
                  >
                    Edit decision
                  </button>
                  <button
                    type="button"
                    className="btn secondary"
                    disabled={busy}
                    onClick={() => decide('OPEN')}
                  >
                    Reopen
                  </button>
                </div>
              ) : (
                <>
                  {editingResolved && (
                    <p className="muted" style={{ margin: 0 }}>
                      Update the outcome or note, or reopen to send this back to the open queue.
                    </p>
                  )}
                  <div className="field">
                    <label htmlFor="note">Reviewer note</label>
                    <textarea
                      id="note"
                      rows={3}
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      disabled={busy || !canAct}
                    />
                  </div>
                  <div className="action-row">
                    <button
                      className="btn"
                      disabled={busy || !canAct}
                      onClick={() => decide('APPROVED')}
                    >
                      {editingResolved ? 'Save as approved' : 'Approve'}
                    </button>
                    <button
                      className="btn danger"
                      disabled={busy || !canAct}
                      onClick={() => decide('REJECTED')}
                    >
                      {editingResolved ? 'Save as rejected' : 'Reject'}
                    </button>
                    <button
                      className="btn secondary"
                      disabled={busy || !canAct}
                      onClick={() => decide('ESCALATED')}
                    >
                      {editingResolved ? 'Save as escalated' : 'Escalate'}
                    </button>
                    {editingResolved && (
                      <>
                        <button
                          type="button"
                          className="btn secondary"
                          disabled={busy}
                          onClick={() => decide('OPEN')}
                        >
                          Reopen
                        </button>
                        <button
                          type="button"
                          className="btn secondary"
                          disabled={busy}
                          onClick={() => {
                            setEditingResolved(false)
                            setNote(selected.reviewer_note || '')
                            setError('')
                          }}
                        >
                          Cancel
                        </button>
                      </>
                    )}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
