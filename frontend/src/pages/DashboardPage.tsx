import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Call } from '../api'
import { useAuth } from '../auth'

function statusBadge(status: string) {
  if (status === 'COMPLETED') return 'green'
  if (status === 'FAILED') return 'red'
  if (status === 'UPLOADED') return 'neutral'
  return 'yellow'
}

export default function DashboardPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin' || user?.is_staff
  const [calls, setCalls] = useState<Call[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  useEffect(() => {
    api
      .listCalls()
      .then(setCalls)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  async function handleDelete(call: Call) {
    if (!isAdmin) return
    const label = call.title || call.id
    if (!window.confirm(`Delete analysis for “${label}”? This cannot be undone.`)) {
      return
    }
    setDeletingId(call.id)
    setError('')
    try {
      await api.deleteCall(call.id)
      setCalls((prev) => prev.filter((c) => c.id !== call.id))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>
            Uploaded calls and processing status.
            {!isAdmin && ' You can upload and view; only admins can delete.'}
          </p>
        </div>
        <Link className="btn" to="/upload">
          Upload call
        </Link>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="panel">
        {loading ? (
          <p className="muted">Loading calls…</p>
        ) : calls.length === 0 ? (
          <p className="muted">No calls yet. Upload a recording to get started.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Domain</th>
                <th>Call date</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {calls.map((call) => (
                <tr key={call.id}>
                  <td>{call.title || 'Untitled'}</td>
                  <td>{call.domain}</td>
                  <td>{call.call_date}</td>
                  <td>
                    <span className={`badge ${statusBadge(call.status)}`}>{call.status}</span>
                  </td>
                  <td>
                    <div className="row-actions">
                      <Link to={`/calls/${call.id}`}>Open</Link>
                      {isAdmin && (
                        <button
                          type="button"
                          className="btn danger compact"
                          disabled={deletingId === call.id}
                          onClick={() => handleDelete(call)}
                        >
                          {deletingId === call.id ? 'Deleting…' : 'Delete'}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
