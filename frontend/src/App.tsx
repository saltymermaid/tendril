import { useEffect, useState } from 'react'

interface HealthResponse {
  status: string
  app: string
  version: string
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data: HealthResponse) => setHealth(data))
      .catch((err: Error) => setError(err.message))
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <div className="tendril-icon">🌱</div>
        <h1>Tendril</h1>
        <p className="subtitle">Garden Planning & Tracking</p>
      </header>

      <main className="app-main">
        <div className="status-card">
          <h2>System Status</h2>
          {error && (
            <div className="status-error">
              <span className="status-dot error" />
              Backend unreachable: {error}
            </div>
          )}
          {health && (
            <div className="status-ok">
              <span className="status-dot ok" />
              {health.app} v{health.version} — {health.status}
            </div>
          )}
          {!health && !error && (
            <div className="status-loading">
              <span className="status-dot loading" />
              Connecting to backend...
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
