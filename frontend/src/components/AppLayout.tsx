import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

export function AppLayout() {
  const { user, logout } = useAuth()

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="header-left">
          <span className="tendril-icon-sm">🌱</span>
          <h1>Tendril</h1>
        </div>
        <nav className="header-nav">
          <NavLink to="/" className="nav-link" end>Dashboard</NavLink>
          <NavLink to="/overview" className="nav-link">Overview</NavLink>
          <NavLink to="/catalog" className="nav-link">Catalog</NavLink>
          <NavLink to="/containers" className="nav-link">Containers</NavLink>
          <NavLink to="/settings" className="nav-link">Settings</NavLink>
        </nav>
        <div className="header-right">
          <span className="user-name">{user?.name}</span>
          <button onClick={logout} className="btn btn-outline btn-sm">
            Logout
          </button>
        </div>
      </header>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
