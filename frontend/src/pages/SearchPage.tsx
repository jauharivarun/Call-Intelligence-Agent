import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api, type SearchResponse } from '../api'

export default function SearchPage() {
  const [q, setQ] = useState('')
  const [result, setResult] = useState<SearchResponse | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      setResult(await api.search(q))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Transcript search</h1>
          <p>Search across your stored transcript lines.</p>
        </div>
      </div>
      <form className="panel search-bar" onSubmit={onSubmit}>
        <input
          className="search-input"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="supervisor, attorney, stop calling…"
        />
        <button className="btn" disabled={busy || !q.trim()}>
          {busy ? 'Searching…' : 'Search'}
        </button>
      </form>
      {error && <div className="error">{error}</div>}
      {result && (
        <div className="panel">
          <p className="muted">
            {result.count} result{result.count === 1 ? '' : 's'} for “{result.query}”
          </p>
          {result.results.map((row) => (
            <div className="item-card" key={row.segment_id}>
              <div className="meta-row">
                <Link to={`/calls/${row.call_id}`}>{row.call_title || row.call_id}</Link>
                <span>
                  Line {row.line_number} · {row.speaker_label}
                </span>
              </div>
              <div>{row.text}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
