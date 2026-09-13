import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

export default function UploadPage() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [domain, setDomain] = useState('debt_collection')
  const [callDate, setCallDate] = useState(new Date().toISOString().slice(0, 10))
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!file) {
      setError('Choose an audio file.')
      return
    }
    setBusy(true)
    setError('')
    const form = new FormData()
    form.append('title', title)
    form.append('domain', domain)
    form.append('call_date', callDate)
    form.append('recording', file)
    try {
      const call = await api.uploadCall(form)
      navigate(`/calls/${call.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Upload call</h1>
          <p>Provide call date and domain so relative dates resolve correctly.</p>
        </div>
      </div>
      <form className="panel form-narrow" onSubmit={onSubmit}>
        {error && <div className="error">{error}</div>}
        <div className="field">
          <label htmlFor="title">Title (optional)</label>
          <input id="title" value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="domain">Domain</label>
          <select id="domain" value={domain} onChange={(e) => setDomain(e.target.value)}>
            <option value="debt_collection">Debt collection</option>
            <option value="customer_support">Customer support</option>
            <option value="sales">Sales</option>
            <option value="internal">Internal</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="call_date">Call date</label>
          <input
            id="call_date"
            type="date"
            value={callDate}
            onChange={(e) => setCallDate(e.target.value)}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="recording">Recording</label>
          <input
            id="recording"
            type="file"
            accept="audio/*,.mp3,.wav,.m4a,.ogg,.flac,.webm"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            required
          />
        </div>
        <button className="btn" disabled={busy}>
          {busy ? 'Uploading…' : 'Upload & analyze'}
        </button>
      </form>
    </div>
  )
}
