import { useEffect, useState } from 'react'
import { api } from '../api'

type Props = {
  callId: string
  enabled: boolean
}

export default function RecordingPlayer({ callId, enabled }: Props) {
  const [src, setSrc] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!enabled || !callId) {
      setSrc(null)
      return
    }

    let objectUrl: string | null = null
    let cancelled = false

    setLoading(true)
    setError('')
    api
      .getRecordingBlobUrl(callId)
      .then((url) => {
        if (cancelled) {
          URL.revokeObjectURL(url)
          return
        }
        objectUrl = url
        setSrc(url)
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Unable to load recording')
          setSrc(null)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [callId, enabled])

  return (
    <div className="panel recording-player">
      <strong>Recording</strong>
      {loading && <p className="muted" style={{ margin: '0.75rem 0 0' }}>Loading audio…</p>}
      {error && (
        <p className="muted" style={{ margin: '0.75rem 0 0', color: 'var(--red)' }}>
          {error}
        </p>
      )}
      {!loading && !error && src && (
        <audio className="audio-player" controls preload="metadata" src={src}>
          Your browser does not support audio playback.
        </audio>
      )}
      {!loading && !error && !src && (
        <p className="muted" style={{ margin: '0.75rem 0 0' }}>
          Recording unavailable.
        </p>
      )}
    </div>
  )
}
