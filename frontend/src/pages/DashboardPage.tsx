import { useAuth } from '@/contexts/AuthContext'

export function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="dashboard-content">
      <div className="page-header">
        <h2>Welcome, {user?.name}!</h2>
        <p className="text-muted">Your garden at a glance</p>
      </div>

      <div className="status-card">
        <p>You're logged in as <strong>{user?.email}</strong></p>
        <p className="text-muted">Full dashboard coming in Step 17.</p>
      </div>
    </div>
  )
}
