import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

export function AppLayout() {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  const closeMenu = () => setMenuOpen(false)

  const handleLogout = () => {
    closeMenu()
    logout()
  }

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="header-left">
          <span className="tendril-icon-sm">🌱</span>
          <h1>Tendril</h1>
        </div>

        {/* Desktop nav — hidden on mobile */}
        <nav className="header-nav header-nav-desktop">
          <NavLink to="/" className="nav-link" end>Dashboard</NavLink>
          <NavLink to="/overview" className="nav-link">Overview</NavLink>
          <NavLink to="/timeline" className="nav-link">Timeline</NavLink>
          <NavLink to="/catalog" className="nav-link">Catalog</NavLink>
          <NavLink to="/containers" className="nav-link">Containers</NavLink>
          <NavLink to="/tasks" className="nav-link">Tasks</NavLink>
          <NavLink to="/settings" className="nav-link">Settings</NavLink>
        </nav>

        <div className="header-right">
          {/* User name only visible on desktop */}
          <span className="user-name header-user-name">{user?.name}</span>
          <button onClick={handleLogout} className="btn btn-outline btn-sm header-logout-btn">
            Logout
          </button>
          {/* Hamburger — hidden on desktop */}
          <button
            className="hamburger-btn"
            onClick={() => setMenuOpen(o => !o)}
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={menuOpen}
          >
            {menuOpen ? '✕' : '☰'}
          </button>
        </div>
      </header>

      {/* Mobile/tablet slide-down menu */}
      {menuOpen && (
        <div className="mobile-menu-overlay" onClick={closeMenu}>
          <nav className="mobile-menu" onClick={e => e.stopPropagation()}>
            <div className="mobile-menu-user">{user?.name}</div>
            <NavLink to="/" className="mobile-nav-link" end onClick={closeMenu}>Dashboard</NavLink>
            <NavLink to="/overview" className="mobile-nav-link" onClick={closeMenu}>Overview</NavLink>
            <NavLink to="/timeline" className="mobile-nav-link" onClick={closeMenu}>Timeline</NavLink>
            <NavLink to="/catalog" className="mobile-nav-link" onClick={closeMenu}>Catalog</NavLink>
            <NavLink to="/containers" className="mobile-nav-link" onClick={closeMenu}>Containers</NavLink>
            <NavLink to="/tasks" className="mobile-nav-link" onClick={closeMenu}>Tasks</NavLink>
            <NavLink to="/settings" className="mobile-nav-link" onClick={closeMenu}>Settings</NavLink>
            <button onClick={handleLogout} className="mobile-menu-logout">Logout</button>
          </nav>
        </div>
      )}

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
