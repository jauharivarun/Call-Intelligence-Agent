const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export type User = {
  id: number
  username: string
  email: string
  is_staff: boolean
  role: 'admin' | 'viewer'
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Token ${token}` } : {}
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {})
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  const auth = authHeaders()
  Object.entries(auth).forEach(([k, v]) => headers.set(k, v as string))

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const data = await res.json()
      detail = data.detail || JSON.stringify(data)
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  health: () => request<{ status: string }>('/api/health/'),
  login: (username: string, password: string) =>
    request<{ token: string; user: User }>('/api/auth/token/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  me: () => request<User>('/api/auth/me/'),
  logout: () => request('/api/auth/logout/', { method: 'POST' }),
  listCalls: () => request<Call[]>('/api/calls/'),
  getCall: (id: string) => request<CallDetail>(`/api/calls/${id}/`),
  uploadCall: (form: FormData) =>
    request<CallDetail>('/api/calls/', { method: 'POST', body: form }),
  getTranscript: (id: string) => request<TranscriptSegment[]>(`/api/calls/${id}/transcript/`),
  getAnalysis: (id: string) => request<Analysis>(`/api/calls/${id}/analysis/`),
  reanalyze: (id: string) =>
    request<CallDetail>(`/api/calls/${id}/reanalyze/`, { method: 'POST' }),
  deleteCall: (id: string) =>
    request<void>(`/api/calls/${id}/`, { method: 'DELETE' }),
  getRecordingBlobUrl: async (id: string) => {
    const headers = new Headers(authHeaders())
    const res = await fetch(`${API_BASE}/api/calls/${id}/recording/`, { headers })
    if (!res.ok) {
      let detail = res.statusText
      try {
        const data = await res.json()
        detail = data.detail || JSON.stringify(data)
      } catch {
        /* ignore */
      }
      throw new Error(detail)
    }
    const blob = await res.blob()
    return URL.createObjectURL(blob)
  },
  listReviews: (status?: string) =>
    request<ReviewItem[]>(`/api/reviews/${status ? `?status=${status}` : ''}`),
  getReview: (id: string) => request<ReviewItem>(`/api/reviews/${id}/`),
  decideReview: (id: string, decision: string, note: string) =>
    request<ReviewItem>(`/api/reviews/${id}/decision/`, {
      method: 'POST',
      body: JSON.stringify({ decision, note }),
    }),
  search: (q: string) =>
    request<SearchResponse>(`/api/search/transcripts/?q=${encodeURIComponent(q)}`),
}

export type Call = {
  id: string
  title: string
  domain: string
  call_date: string
  status: string
  error_message: string
  recording_duration_seconds: number | null
  created_at: string
  updated_at: string
}

export type CallDetail = Call & {
  recording_path: string
  jobs: Array<{
    id: string
    stage: string
    status: string
    started_at: string | null
    completed_at: string | null
    error_message: string
  }>
}

export type TranscriptSegment = {
  id: string
  line_number: number
  speaker_label: string
  start_time_seconds: string | null
  end_time_seconds: string | null
  text: string
}

export type Analysis = {
  id: string
  tag: string
  summary: string
  overall_confidence: string | null
  analysis_version: string
  decisions: Array<{
    id: string
    text: string
    confidence: string | null
    verification_status: string
    evidence: TranscriptSegment[]
  }>
  action_items: Array<{
    id: string
    task: string
    owner_name: string
    owner_type: string
    due_date: string | null
    original_due_phrase: string
    confidence: string | null
    verification_status: string
    review_required: boolean
    evidence: TranscriptSegment[]
  }>
  blockers: Array<{
    id: string
    text: string
    impact: string
    confidence: string | null
    verification_status: string
    review_required: boolean
    evidence: TranscriptSegment[]
  }>
  compliance_observations: Array<{
    id: string
    category: string
    severity: string
    observation: string
    rationale: string
    confidence: string | null
    review_required: boolean
    evidence: TranscriptSegment[]
  }>
  review_items: ReviewItem[]
  sentiment: {
    overall_sentiment: string
    customer_sentiment: string
    agent_sentiment: string
    profanity_detected: boolean
    angry_customer_detected: boolean
    confidence: string | null
  } | null
}

export type ReviewItem = {
  id: string
  call: string
  call_title?: string
  category: string
  reason: string
  severity: string
  confidence: string | null
  status: string
  is_resolved?: boolean
  reviewer?: number | null
  reviewer_username?: string | null
  reviewer_note: string
  reviewed_at?: string | null
  evidence: TranscriptSegment[]
  created_at: string
}

export type SearchResponse = {
  query: string
  count: number
  results: Array<{
    call_id: string
    call_title: string
    segment_id: string
    line_number: number
    speaker_label: string
    text: string
  }>
}
