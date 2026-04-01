import { useAuth } from '@/contexts/AuthContext'

export function DashboardPage() {
  const { user, logout } = useAuth()

  return (
    <div className="dashboard-page">
      <header className="app-header">
        <div className="header-left">
          <span className="tendril-icon">🌱</span>
          <h1>Tendril</h1>
        </div>
        <div className="header-right">
          <span className="user-name">{user?.name}</span>
          <button onClick={logout} className="btn btn-outline btn-sm">
            Logout
          </button>
        </div>
      </header>

      <main className="app-main">
        <div className="status-card">
          <h2>Welcome, {user?.name}!</h2>
          <p>You're logged in as <strong>{user?.email}</strong></p>
          <p className="text-muted">Dashboard coming in Step 17.</p>
        </div>
      </main>
    </div>
  )
}
