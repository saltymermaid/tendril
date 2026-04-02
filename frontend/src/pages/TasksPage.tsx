import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'

interface TaskData {
  id: number
  user_id: number
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
  created_at: string
  updated_at: string
}

interface TaskFormData {
  title: string
  description: string
  due_date: string
  container_id: string
  planting_id: string
}

interface ContainerOption {
  id: number
  name: string
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

function isOverdue(dateStr: string | null): boolean {
  if (!dateStr) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(dateStr + 'T00:00:00')
  return due < today
}

function isToday(dateStr: string | null): boolean {
  if (!dateStr) return false
  const today = new Date().toISOString().split('T')[0]
  return dateStr === today
}

function getWeekRange(): { start: string; end: string; label: string } {
  const now = new Date()
  const dayOfWeek = now.getDay()
  const start = new Date(now)
  start.setDate(now.getDate() - dayOfWeek)
  const end = new Date(start)
  end.setDate(start.getDate() + 6)

  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0],
    label: `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} – ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`,
  }
}

function groupByDate(tasks: TaskData[]): Map<string, TaskData[]> {
  const groups = new Map<string, TaskData[]>()

  // First: overdue tasks (past due, not completed/dismissed)
  const overdue = tasks.filter(
    (t) => t.due_date && isOverdue(t.due_date) && t.status === 'pending'
  )
  if (overdue.length > 0) {
    groups.set('Overdue', overdue)
  }

  // Then: no-date tasks
  const noDate = tasks.filter((t) => !t.due_date && t.status === 'pending')
  
  // Group remaining by date
  const dated = tasks.filter(
    (t) => t.due_date && !isOverdue(t.due_date) && t.status === 'pending'
  )
  for (const task of dated) {
    const key = task.due_date!
    if (!groups.has(key)) {
      groups.set(key, [])
    }
    groups.get(key)!.push(task)
  }

  if (noDate.length > 0) {
    groups.set('No Due Date', noDate)
  }

  // Completed/dismissed at the end
  const done = tasks.filter((t) => t.status !== 'pending')
  if (done.length > 0) {
    groups.set('Completed / Dismissed', done)
  }

  return groups
}

export function TasksPage() {
  const [tasks, setTasks] = useState<TaskData[]>([])
  const [containers, setContainers] = useState<ContainerOption[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed' | 'dismissed'>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [form, setForm] = useState<TaskFormData>({
    title: '',
    description: '',
    due_date: '',
    container_id: '',
    planting_id: '',
  })

  const week = getWeekRange()

  const fetchTasks = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      if (filter !== 'all') {
        params.set('status', filter)
      }
      const res = await fetch(`/api/tasks?${params}`)
      if (res.ok) {
        const data = await res.json()
        setTasks(data)
      }
    } catch (err) {
      console.error('Failed to fetch tasks:', err)
    } finally {
      setLoading(false)
    }
  }, [filter])

  const fetchContainers = useCallback(async () => {
    try {
      const res = await fetch('/api/containers')
      if (res.ok) {
        const data = await res.json()
        setContainers(data)
      }
    } catch (err) {
      console.error('Failed to fetch containers:', err)
    }
  }, [])

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  useEffect(() => {
    fetchContainers()
  }, [fetchContainers])

  async function handleGenerate() {
    setGenerating(true)
    try {
      const res = await fetch('/api/tasks/generate')
      if (res.ok) {
        const data = await res.json()
        if (data.generated > 0) {
          fetchTasks()
        }
      }
    } catch (err) {
      console.error('Failed to generate tasks:', err)
    } finally {
      setGenerating(false)
    }
  }

  async function handleStatusChange(taskId: number, newStatus: string) {
    try {
      const res = await fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      })
      if (res.ok) {
        setTasks((prev) =>
          prev.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
        )
      }
    } catch (err) {
      console.error('Failed to update task:', err)
    }
  }

  async function handleDelete(taskId: number) {
    if (!confirm('Delete this task?')) return
    try {
      const res = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' })
      if (res.ok) {
        setTasks((prev) => prev.filter((t) => t.id !== taskId))
      }
    } catch (err) {
      console.error('Failed to delete task:', err)
    }
  }

  async function handleCreateTask(e: React.FormEvent) {
    e.preventDefault()
    if (!form.title.trim()) return

    try {
      const body: Record<string, unknown> = { title: form.title.trim() }
      if (form.description.trim()) body.description = form.description.trim()
      if (form.due_date) body.due_date = form.due_date
      if (form.container_id) body.container_id = parseInt(form.container_id)
      if (form.planting_id) body.planting_id = parseInt(form.planting_id)

      const res = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (res.ok) {
        const newTask = await res.json()
        setTasks((prev) => [newTask, ...prev])
        setShowCreateModal(false)
        setForm({ title: '', description: '', due_date: '', container_id: '', planting_id: '' })
      }
    } catch (err) {
      console.error('Failed to create task:', err)
    }
  }

  const pendingCount = tasks.filter((t) => t.status === 'pending').length
  const overdueCount = tasks.filter(
    (t) => t.status === 'pending' && t.due_date && isOverdue(t.due_date)
  ).length

  const grouped = groupByDate(tasks)

  if (loading) {
    return (
      <div className="page-container">
        <p className="loading-text">Loading tasks…</p>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2>Tasks</h2>
          <p className="page-subtitle">
            {pendingCount} pending{overdueCount > 0 && <span className="text-error"> · {overdueCount} overdue</span>}
            {' · '}This week: {week.label}
          </p>
        </div>
        <div className="page-actions">
          <button
            className="btn btn-outline"
            onClick={handleGenerate}
            disabled={generating}
          >
            {generating ? '⏳ Generating…' : '🔄 Auto-Generate'}
          </button>
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            + New Task
          </button>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="task-filters">
        {(['all', 'pending', 'completed', 'dismissed'] as const).map((f) => (
          <button
            key={f}
            className={`task-filter-btn ${filter === f ? 'active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Task groups */}
      {tasks.length === 0 ? (
        <div className="empty-state">
          <p>No tasks yet.</p>
          <p className="text-secondary">
            Click "Auto-Generate" to create tasks from your plantings, or add a manual task.
          </p>
        </div>
      ) : (
        <div className="task-groups">
          {Array.from(grouped.entries()).map(([groupLabel, groupTasks]) => (
            <div key={groupLabel} className="task-group">
              <h3 className={`task-group-label ${groupLabel === 'Overdue' ? 'text-error' : ''}`}>
                {groupLabel.match(/^\d{4}-\d{2}-\d{2}$/)
                  ? (isToday(groupLabel) ? `Today — ${formatDate(groupLabel)}` : formatDate(groupLabel))
                  : groupLabel}
                <span className="task-group-count">{groupTasks.length}</span>
              </h3>
              <div className="task-list">
                {groupTasks.map((task) => (
                  <div
                    key={task.id}
                    className={`task-card ${task.status !== 'pending' ? 'task-done' : ''} ${
                      task.due_date && isOverdue(task.due_date) && task.status === 'pending'
                        ? 'task-overdue'
                        : ''
                    } ${task.due_date && isToday(task.due_date) ? 'task-today' : ''}`}
                  >
                    <div className="task-card-main">
                      <div className="task-card-header">
                        <span className={`task-source-badge task-source-${task.source}`}>
                          {task.source === 'auto' ? '🤖' : '✏️'}
                        </span>
                        <h4 className="task-title">{task.title}</h4>
                      </div>
                      {task.description && (
                        <p className="task-description">{task.description}</p>
                      )}
                      <div className="task-meta">
                        {task.due_date && (
                          <span className="task-due">
                            📅 {formatDate(task.due_date)}
                          </span>
                        )}
                        {task.container_name && (
                          <Link
                            to={`/containers/${task.container_id}`}
                            className="task-link"
                          >
                            📦 {task.container_name}
                          </Link>
                        )}
                        {task.variety_name && (
                          <span className="task-variety">🌱 {task.variety_name}</span>
                        )}
                        {task.planting_id && (
                          <Link
                            to={`/plantings/${task.planting_id}`}
                            className="task-link"
                          >
                            🌿 Planting #{task.planting_id}
                          </Link>
                        )}
                      </div>
                    </div>
                    <div className="task-card-actions">
                      {task.status === 'pending' ? (
                        <>
                          <button
                            className="btn btn-sm btn-success"
                            onClick={() => handleStatusChange(task.id, 'completed')}
                            title="Complete"
                          >
                            ✓
                          </button>
                          <button
                            className="btn btn-sm btn-outline"
                            onClick={() => handleStatusChange(task.id, 'dismissed')}
                            title="Dismiss"
                          >
                            ✕
                          </button>
                        </>
                      ) : (
                        <button
                          className="btn btn-sm btn-outline"
                          onClick={() => handleStatusChange(task.id, 'pending')}
                          title="Reopen"
                        >
                          ↩
                        </button>
                      )}
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDelete(task.id)}
                        title="Delete"
                      >
                        🗑
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Task Modal */}
      {showCreateModal && (
        <div className="modal-backdrop" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>New Task</h3>
              <button className="modal-close" onClick={() => setShowCreateModal(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleCreateTask}>
              <div className="form-group">
                <label className="form-label">Title *</label>
                <input
                  type="text"
                  className="form-input"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="e.g., Water tomatoes"
                  required
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  className="form-input"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Optional details…"
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Due Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={form.due_date}
                  onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Container</label>
                <select
                  className="form-input"
                  value={form.container_id}
                  onChange={(e) => setForm({ ...form, container_id: e.target.value })}
                >
                  <option value="">— None —</option>
                  {containers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
