import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { WeatherWidget } from '@/components/WeatherWidget'

interface TaskData {
  id: number
  title: string
  description: string | null
  due_date: string | null
  source: string
  status: string
  container_id: number | null
  planting_id: number | null
  variety_id: number | null
  container_name: string | null
  variety_name: string | null
}

interface ContainerOverview {
  id: number
  name: string
  type: string
  total_slots: number
  planted_slots: number
  plantings: { id: number; variety_name: string; status: string }[]
}

function isOverdue(dateStr: string | null): boolean {
  if (!dateStr) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(dateStr + 'T00:00:00')
  return due < today
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

export function DashboardPage() {
  const { user } = useAuth()
  const [tasks, setTasks] = useState<TaskData[]>([])
  const [containers, setContainers] = useState<ContainerOverview[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const [tasksRes, containersRes] = await Promise.all([
        fetch('/api/tasks?status=pending'),
        fetch('/api/containers/overview'),
      ])
      if (tasksRes.ok) {
        const tasksData = await tasksRes.json()
        setTasks(tasksData)
      }
      if (containersRes.ok) {
        const containersData = await containersRes.json()
        setContainers(containersData)
      }
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  async function handleCompleteTask(taskId: number) {
    try {
      const res = await fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'completed' }),
      })
      if (res.ok) {
        setTasks((prev) => prev.filter((t) => t.id !== taskId))
      }
    } catch (err) {
      console.error('Failed to complete task:', err)
    }
  }

  // Compute stats
  const totalContainers = containers.length
  const totalPlantings = containers.reduce(
    (sum, c) => sum + c.plantings.filter((p) => p.status === 'active').length,
    0
  )
  const totalSlots = containers.reduce((sum, c) => sum + c.total_slots, 0)
  const plantedSlots = containers.reduce((sum, c) => sum + c.planted_slots, 0)
  const overdueTasks = tasks.filter((t) => isOverdue(t.due_date))
  const upcomingTasks = tasks.filter((t) => !isOverdue(t.due_date)).slice(0, 5)

  const greeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 17) return 'Good afternoon'
    return 'Good evening'
  }

  if (loading) {
    return (
      <div className="page-container">
        <p className="loading-text">Loading dashboard…</p>
      </div>
    )
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div className="dashboard-greeting">
        <h2>{greeting()}, {user?.name || 'Gardener'}! 🌱</h2>
        <p className="text-secondary">
          {new Date().toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'long',
            day: 'numeric',
            year: 'numeric',
          })}
        </p>
      </div>

      {/* Quick Stats */}
      <div className="dashboard-stats">
        <div className="stat-card">
          <div className="stat-value">{totalContainers}</div>
          <div className="stat-label">Containers</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{totalPlantings}</div>
          <div className="stat-label">Active Plantings</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {plantedSlots}/{totalSlots}
          </div>
          <div className="stat-label">Slots Used</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{tasks.length}</div>
          <div className="stat-label">Pending Tasks</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="dashboard-actions">
        <Link to="/containers" className="quick-action-btn">
          📦 Containers
        </Link>
        <Link to="/catalog/varieties/new" className="quick-action-btn">
          🌱 Add Variety
        </Link>
        <Link to="/overview" className="quick-action-btn">
          🗺️ Garden Overview
        </Link>
        <Link to="/timeline" className="quick-action-btn">
          📊 Timeline
        </Link>
        <Link to="/tasks" className="quick-action-btn">
          ✅ All Tasks
        </Link>
        <Link to="/catalog" className="quick-action-btn">
          📚 Catalog
        </Link>
      </div>

      {/* Main Content Grid */}
      <div className="dashboard-grid">
        {/* Left Column: Tasks */}
        <div className="dashboard-column">
          {/* Overdue Tasks */}
          {overdueTasks.length > 0 && (
            <div className="dashboard-card dashboard-card-alert">
              <h3 className="dashboard-card-title text-error">
                ⚠️ Overdue Tasks ({overdueTasks.length})
              </h3>
              <div className="dashboard-task-list">
                {overdueTasks.map((task) => (
                  <div key={task.id} className="dashboard-task-item task-overdue">
                    <div className="dashboard-task-info">
                      <span className="dashboard-task-source">
                        {task.source === 'auto' ? '🤖' : '✏️'}
                      </span>
                      <div>
                        <div className="dashboard-task-title">{task.title}</div>
                        <div className="dashboard-task-meta">
                          {task.due_date && <span>📅 {formatDate(task.due_date)}</span>}
                          {task.container_name && (
                            <Link to={`/containers/${task.container_id}`}>
                              📦 {task.container_name}
                            </Link>
                          )}
                        </div>
                      </div>
                    </div>
                    <button
                      className="btn btn-sm btn-success"
                      onClick={() => handleCompleteTask(task.id)}
                      title="Complete"
                    >
                      ✓
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upcoming Tasks */}
          <div className="dashboard-card">
            <div className="dashboard-card-header">
              <h3 className="dashboard-card-title">📋 Upcoming Tasks</h3>
              <Link to="/tasks" className="dashboard-card-link">
                View all →
              </Link>
            </div>
            {upcomingTasks.length === 0 ? (
              <div className="dashboard-empty">
                <p>No pending tasks.</p>
                <Link to="/tasks" className="btn btn-outline btn-sm">
                  + Create Task
                </Link>
              </div>
            ) : (
              <div className="dashboard-task-list">
                {upcomingTasks.map((task) => (
                  <div key={task.id} className="dashboard-task-item">
                    <div className="dashboard-task-info">
                      <span className="dashboard-task-source">
                        {task.source === 'auto' ? '🤖' : '✏️'}
                      </span>
                      <div>
                        <div className="dashboard-task-title">{task.title}</div>
                        <div className="dashboard-task-meta">
                          {task.due_date && <span>📅 {formatDate(task.due_date)}</span>}
                          {task.container_name && (
                            <span>📦 {task.container_name}</span>
                          )}
                          {task.variety_name && (
                            <span>🌱 {task.variety_name}</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <button
                      className="btn btn-sm btn-success"
                      onClick={() => handleCompleteTask(task.id)}
                      title="Complete"
                    >
                      ✓
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Container Summary */}
          <div className="dashboard-card">
            <div className="dashboard-card-header">
              <h3 className="dashboard-card-title">📦 Garden Containers</h3>
              <Link to="/containers" className="dashboard-card-link">
                View all →
              </Link>
            </div>
            {containers.length === 0 ? (
              <div className="dashboard-empty">
                <p>No containers yet.</p>
                <Link to="/containers/new" className="btn btn-outline btn-sm">
                  + Add Container
                </Link>
              </div>
            ) : (
              <div className="dashboard-container-list">
                {containers.map((c) => (
                  <Link
                    key={c.id}
                    to={`/containers/${c.id}`}
                    className="dashboard-container-item"
                  >
                    <div className="dashboard-container-info">
                      <span className="dashboard-container-icon">
                        {c.type === 'tower' ? '🗼' : '🌿'}
                      </span>
                      <div>
                        <div className="dashboard-container-name">{c.name}</div>
                        <div className="dashboard-container-meta">
                          {c.planted_slots}/{c.total_slots} slots ·{' '}
                          {c.plantings.filter((p) => p.status === 'active').length} active
                        </div>
                      </div>
                    </div>
                    <div className="dashboard-container-bar">
                      <div
                        className="dashboard-container-bar-fill"
                        style={{
                          width: `${c.total_slots > 0 ? (c.planted_slots / c.total_slots) * 100 : 0}%`,
                        }}
                      />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Weather */}
        <div className="dashboard-column dashboard-column-side">
          <WeatherWidget />
        </div>
      </div>
    </div>
  )
}
