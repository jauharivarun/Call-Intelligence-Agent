import { Navigate, Outlet, Route, Routes, NavLink } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import UploadPage from './pages/UploadPage'
import CallDetailPage from './pages/CallDetailPage'
import ReviewsPage from './pages/ReviewsPage'
import SearchPage from './pages/SearchPage'

function ProtectedLayout() {
  const { user, loading, logout } = useAuth()
  if (loading) return <div className="main">Loading…</div>
  if (!user) return <Navigate to="/login" replace />

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            CI
          </div>
          <div className="brand-text">
            Call Intelligence
            <span>Evidence-backed analysis</span>
          </div>
        </div>
        <nav className="nav">
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/upload">Upload</NavLink>
          <NavLink to="/reviews">Reviews</NavLink>
          <NavLink to="/search">Search</NavLink>
        </nav>
        <div className="sidebar-footer">
          <div>{user.username}</div>
          <div className="role-label">
            Role: {user.role || (user.is_staff ? 'admin' : 'viewer')}
          </div>
          <button className="btn secondary" onClick={() => logout()}>
            Log out
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/calls/:id" element={<CallDetailPage />} />
          <Route path="/reviews" element={<ReviewsPage />} />
          <Route path="/search" element={<SearchPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
