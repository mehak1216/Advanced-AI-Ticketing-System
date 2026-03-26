'use client'

import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'

const API_BASE_CANDIDATES = [
  process.env.NEXT_PUBLIC_API_BASE,
  'http://127.0.0.1:8011/api',
  'http://localhost:8011/api',
].filter(Boolean) as string[]

const apiGet = async <T,>(path: string) => {
  let lastError: unknown = null
  for (const base of API_BASE_CANDIDATES) {
    try {
      const res = await axios.get<T>(`${base}${path}`, { timeout: 10000 })
      return { data: res.data, base }
    } catch (err) {
      lastError = err
      continue
    }
  }
  throw lastError
}

const apiPost = async <T,>(path: string, body: any) => {
  let lastError: unknown = null
  for (const base of API_BASE_CANDIDATES) {
    try {
      const res = await axios.post<T>(`${base}${path}`, body, { timeout: 10000 })
      return { data: res.data, base }
    } catch (err) {
      lastError = err
      continue
    }
  }
  throw lastError
}

const apiPut = async <T,>(path: string, body: any, params?: Record<string, any>) => {
  let lastError: unknown = null
  for (const base of API_BASE_CANDIDATES) {
    try {
      const res = await axios.put<T>(`${base}${path}`, body, { params, timeout: 10000 })
      return { data: res.data, base }
    } catch (err) {
      lastError = err
      continue
    }
  }
  throw lastError
}

const STATUSES = ['New', 'Assigned', 'In Progress', 'Pending Info', 'Resolved', 'Closed', 'Escalated']
const SEVERITIES = ['Critical', 'High', 'Medium', 'Low']
const DEPARTMENTS = ['Engineering', 'Finance', 'HR', 'IT', 'Product', 'Marketing', 'Legal']

interface Ticket {
  id: number
  title: string
  description: string
  category: string
  ai_summary: string
  severity: string
  sentiment: string
  resolution_path: string
  suggested_department?: string
  suggested_employee_id?: number
  confidence: number
  estimated_resolution_time: number
  status: string
  assignee_id?: number
  auto_resolved: boolean
  auto_response?: string
  feedback?: string
  created_at: string
  assigned_at?: string
  picked_up_at?: string
  resolved_at?: string
}

interface Employee {
  id: number
  name: string
  department: string
  role: string
  skills: string
  availability: string
  current_load: number
  avg_resolution_time: number
}

interface AnalyticsSummary {
  total_tickets: number
  open_tickets: number
  resolved_tickets: number
  auto_resolved: number
  escalated: number
  department_load: Record<string, number>
  avg_resolution_time_by_dept: Record<string, number>
  top_categories: [string, number][]
  auto_resolution_success_rate: number
}

interface TicketEvent {
  id: number
  ticket_id: number
  event_type: string
  message: string
  actor?: string
  created_at: string
}

type Role = 'Admin' | 'Agent' | 'Requester'

interface Toast {
  id: string
  title: string
  message: string
  tone: 'info' | 'success' | 'warning'
}

export default function Home() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [employees, setEmployees] = useState<Employee[]>([])
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')

  const [statusFilter, setStatusFilter] = useState('All')
  const [severityFilter, setSeverityFilter] = useState('All')
  const [departmentFilter, setDepartmentFilter] = useState('All')
  const [autoFilter, setAutoFilter] = useState('All')
  const [sortBy, setSortBy] = useState('created_at')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const [timelineMap, setTimelineMap] = useState<Record<number, TicketEvent[]>>({})
  const [wsStatus, setWsStatus] = useState<'connected' | 'connecting' | 'disconnected'>('connecting')
  const [role, setRole] = useState<Role>('Admin')
  const [toasts, setToasts] = useState<Toast[]>([])

  const employeeNameById = useMemo(() => {
    return employees.reduce<Record<number, string>>((acc, emp) => {
      acc[emp.id] = emp.name
      return acc
    }, {})
  }, [employees])

  const fetchTickets = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, string> = { sort_by: sortBy, sort_dir: 'desc' }
      if (statusFilter !== 'All') params.status = statusFilter
      if (severityFilter !== 'All') params.severity = severityFilter
      if (departmentFilter !== 'All') params.department = departmentFilter
      if (dateFrom) params.date_from = new Date(dateFrom).toISOString()
      if (dateTo) params.date_to = new Date(dateTo).toISOString()

      const res = await apiGet<Ticket[]>(`/tickets?${new URLSearchParams(params).toString()}`)
      let data: Ticket[] = res.data
      if (autoFilter === 'Auto-Resolved') data = data.filter((t) => t.auto_resolved)
      if (autoFilter === 'Manual') data = data.filter((t) => !t.auto_resolved)
      setTickets(data)
    } catch (err: any) {
      setError(err?.message ?? 'Failed to fetch tickets')
    } finally {
      setLoading(false)
    }
  }

  const pushToast = (toast: Omit<Toast, 'id'>) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
    setToasts((prev) => [...prev, { id, ...toast }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 3500)
  }

  const fetchEmployees = async () => {
    try {
      const res = await apiGet<Employee[]>('/employees')
      setEmployees(res.data)
    } catch (err: any) {
      setError(err?.message ?? 'Failed to fetch employees')
    }
  }

  const fetchAnalytics = async () => {
    try {
      const res = await apiGet<AnalyticsSummary>('/analytics/summary')
      setAnalytics(res.data)
    } catch (err: any) {
      setError(err?.message ?? 'Failed to fetch analytics')
    }
  }

  useEffect(() => {
    fetchEmployees()
    fetchAnalytics()
  }, [])

  useEffect(() => {
    const ws = new WebSocket('ws://127.0.0.1:8011/api/ws/tickets')
    setWsStatus('connecting')
    ws.onopen = () => setWsStatus('connected')
    ws.onclose = () => setWsStatus('disconnected')
    ws.onerror = () => setWsStatus('disconnected')
    ws.onmessage = () => {
      fetchTickets()
      fetchAnalytics()
      fetchEmployees()
      pushToast({
        title: 'Live update',
        message: 'New ticket activity detected.',
        tone: 'info',
      })
    }
    return () => ws.close()
  }, [])

  useEffect(() => {
    fetchTickets()
  }, [statusFilter, severityFilter, departmentFilter, autoFilter, sortBy, dateFrom, dateTo])

  const createTicket = async () => {
    if (!title.trim() || !description.trim()) return
    await apiPost('/tickets', { title, description })
    setTitle('')
    setDescription('')
    fetchTickets()
    fetchAnalytics()
    pushToast({
      title: 'Ticket created',
      message: 'AI analysis completed and routing applied.',
      tone: 'success',
    })
  }

  const updateTicket = async (ticketId: number, payload: Record<string, any>) => {
    await apiPut(`/tickets/${ticketId}`, payload)
    fetchTickets()
    fetchAnalytics()
    pushToast({
      title: 'Ticket updated',
      message: 'Status/assignment saved successfully.',
      tone: 'info',
    })
  }

  const submitFeedback = async (ticketId: number, feedback: 'Yes' | 'No') => {
    await apiPut(`/tickets/${ticketId}/feedback`, null, { feedback })
    fetchTickets()
    fetchAnalytics()
    pushToast({
      title: 'Feedback received',
      message: `Marked as ${feedback === 'Yes' ? 'Helpful' : 'Not Helpful'}.`,
      tone: feedback === 'Yes' ? 'success' : 'warning',
    })
  }

  const addNote = async (ticketId: number, message: string) => {
    await apiPost(`/tickets/${ticketId}/notes`, { message, actor: 'assignee' })
    loadTimeline(ticketId)
    pushToast({
      title: 'Note added',
      message: 'Internal note saved to timeline.',
      tone: 'info',
    })
  }

  const requestInfo = async (ticketId: number, message: string) => {
    await apiPost(`/tickets/${ticketId}/request-info`, { message, actor: 'assignee' })
    fetchTickets()
    loadTimeline(ticketId)
    pushToast({
      title: 'Info requested',
      message: 'Ticket moved to Pending Info.',
      tone: 'warning',
    })
  }

  const loadTimeline = async (ticketId: number) => {
    const res = await apiGet<TicketEvent[]>(`/tickets/${ticketId}/timeline`)
    setTimelineMap((prev) => ({ ...prev, [ticketId]: res.data }))
  }

  return (
    <div className="min-h-screen">
      <div className="fixed right-6 top-6 z-50 space-y-3">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`rounded-2xl border px-4 py-3 text-sm shadow-lg ${
              toast.tone === 'success'
                ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                : toast.tone === 'warning'
                ? 'border-amber-200 bg-amber-50 text-amber-800'
                : 'border-slate-200 bg-white text-slate-800'
            }`}
          >
            <p className="font-semibold">{toast.title}</p>
            <p className="text-xs">{toast.message}</p>
          </div>
        ))}
      </div>
      <div className="mx-auto max-w-6xl px-6 py-10">
        <section className="fade-up">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl">
              <span className="inline-flex items-center rounded-full bg-white/70 px-4 py-2 text-sm font-medium uppercase tracking-[0.2em] text-slate-600 soft-ring">
                Advanced AI Ticketing System
              </span>
              <h1 className="mt-5 text-4xl font-semibold leading-tight text-slate-900 md:text-5xl">
                Resolve smarter, route faster, and keep every team in sync.
              </h1>
              <p className="mt-4 text-lg text-slate-700">
                AI reads every ticket first, proposes the resolution path, and keeps the lifecycle transparent with timeline events, escalation logic, and analytics.
              </p>
              <div className="mt-6 flex flex-wrap items-center gap-3">
                <span className="text-xs uppercase tracking-[0.2em] text-slate-500">Role</span>
                <div className="inline-flex rounded-full bg-white/80 p-1 soft-ring">
                  {(['Admin', 'Agent', 'Requester'] as Role[]).map((r) => (
                    <button
                      key={r}
                      onClick={() => setRole(r)}
                      className={`rounded-full px-4 py-1 text-xs font-semibold transition ${
                        role === r ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="glass rounded-3xl p-6 fade-up delay-1">
              <p className="text-sm uppercase tracking-[0.2em] text-slate-500">System Health</p>
              <p className="mt-2 text-xs text-slate-500">Live updates: {wsStatus}</p>
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-2xl font-semibold">{analytics?.total_tickets ?? 0}</p>
                  <p className="text-sm text-slate-500">Total Tickets</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold">{analytics?.open_tickets ?? 0}</p>
                  <p className="text-sm text-slate-500">Open Queue</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold">{analytics?.auto_resolved ?? 0}</p>
                  <p className="text-sm text-slate-500">Auto-Resolved</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold">{analytics?.auto_resolution_success_rate?.toFixed(1) ?? '0.0'}%</p>
                  <p className="text-sm text-slate-500">Helpful Rate</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-10 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="glass rounded-3xl p-6 fade-up delay-1">
            <h2 className="text-2xl font-semibold">Create a Ticket</h2>
            <p className="text-sm text-slate-600">Submit a new request and see AI decisions instantly.</p>
            <div className="mt-6 space-y-4">
              <input
                type="text"
                placeholder="Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white/80 px-4 py-3 text-sm outline-none focus:border-slate-400"
              />
              <textarea
                placeholder="Describe the issue, include impact and urgency."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="min-h-[140px] w-full rounded-xl border border-slate-200 bg-white/80 px-4 py-3 text-sm outline-none focus:border-slate-400"
              />
              {role !== 'Requester' && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-700">
                  Requester role is required to submit tickets. Switch role above to proceed.
                </div>
              )}
              <button
                onClick={createTicket}
                disabled={role !== 'Requester'}
                className="w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                Submit Ticket
              </button>
            </div>
          </div>

          <div className="grid gap-4">
            <div className="glass rounded-3xl p-6 fade-up delay-2">
              <h3 className="text-lg font-semibold">Department Load</h3>
              <div className="mt-4 space-y-3 text-sm">
                {analytics?.department_load &&
                  Object.entries(analytics.department_load).map(([dept, count]) => (
                    <div key={dept} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span>{dept}</span>
                        <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">
                          {count}
                        </span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-slate-200">
                        <div
                          className="h-2 rounded-full bg-indigo-500"
                          style={{ width: `${Math.min(100, (count / Math.max(1, analytics.total_tickets)) * 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                {!analytics?.department_load && <p className="text-slate-500">No department data yet.</p>}
              </div>
            </div>
            <div className="glass rounded-3xl p-6 fade-up delay-3">
              <h3 className="text-lg font-semibold">Top Categories This Week</h3>
              <div className="mt-4 space-y-3 text-sm">
                {analytics?.top_categories?.length ? (
                  analytics.top_categories.map(([cat, count]) => (
                    <div key={cat} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span>{cat}</span>
                        <span className="rounded-full bg-orange-500 px-3 py-1 text-xs font-semibold text-white">
                          {count}
                        </span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-orange-100">
                        <div
                          className="h-2 rounded-full bg-orange-500"
                          style={{ width: `${Math.min(100, (count / Math.max(1, analytics.total_tickets)) * 100)}%` }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-500">No category trends yet.</p>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="mt-12">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-semibold">Tickets Command Center</h2>
              <p className="text-sm text-slate-600">Filter, route, and manage the entire lifecycle.</p>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={autoFilter}
                onChange={(e) => setAutoFilter(e.target.value)}
                className="rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm"
              >
                {['All', 'Auto-Resolved', 'Manual'].map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm"
              >
                {['created_at', 'severity', 'status'].map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-6 grid gap-4 rounded-3xl border border-slate-200 bg-white/60 p-6">
            <div className="grid gap-3 md:grid-cols-5">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm"
              >
                {['All', ...STATUSES].map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm"
              >
                {['All', ...SEVERITIES].map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
              <select
                value={departmentFilter}
                onChange={(e) => setDepartmentFilter(e.target.value)}
                className="rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm"
              >
                {['All', ...DEPARTMENTS].map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm"
              />
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm"
              />
            </div>

            {role === 'Requester' && (
              <p className="text-xs text-slate-500">
                Requester view: you can submit and track tickets, but cannot change status or assign agents.
              </p>
            )}

            {error && <p className="text-sm text-red-600">{error}</p>}
            {loading && <p className="text-sm text-slate-500">Loading tickets...</p>}

            <div className="grid gap-4">
              {tickets.map((ticket) => (
                <article key={ticket.id} className="glass rounded-3xl p-6">
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <h3 className="text-xl font-semibold">{ticket.title}</h3>
                      <p className="text-sm text-slate-600">{ticket.description}</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-wide">
                      <span className="rounded-full bg-slate-900 px-3 py-1 text-white">{ticket.status}</span>
                      <span className="rounded-full bg-emerald-100 px-3 py-1 text-emerald-700">{ticket.severity}</span>
                      <span className="rounded-full bg-indigo-100 px-3 py-1 text-indigo-700">{ticket.category}</span>
                    </div>
                  </div>

                  <div className="mt-4 grid gap-4 md:grid-cols-3">
                    <div className="text-sm">
                      <p className="text-slate-500">AI Summary</p>
                      <p className="font-medium">{ticket.ai_summary}</p>
                    </div>
                    <div className="text-sm">
                      <p className="text-slate-500">Routing</p>
                      <p className="font-medium">
                        {ticket.resolution_path} - {ticket.suggested_department ?? '-'}
                      </p>
                    </div>
                    <div className="text-sm">
                      <p className="text-slate-500">Assignee</p>
                      <p className="font-medium">
                        {ticket.assignee_id ? employeeNameById[ticket.assignee_id] : 'Unassigned'}
                      </p>
                    </div>
                  </div>

                  {ticket.auto_resolved && (
                    <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm">
                      <p className="font-semibold text-emerald-700">Auto-Resolved Response</p>
                      <p>{ticket.auto_response}</p>
                      {ticket.feedback ? (
                        <p className="mt-2 text-emerald-700">Feedback: {ticket.feedback}</p>
                      ) : (
                        <div className="mt-2 flex gap-2">
                          <button
                            onClick={() => submitFeedback(ticket.id, 'Yes')}
                            className="rounded-full bg-emerald-600 px-3 py-1 text-xs font-semibold text-white"
                          >
                            Helpful
                          </button>
                          <button
                            onClick={() => submitFeedback(ticket.id, 'No')}
                            className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white"
                          >
                            Not Helpful
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {role !== 'Requester' && (
                  <div className="mt-5 grid gap-3 md:grid-cols-3">
                    <select
                      defaultValue={ticket.status}
                      onChange={(e) => updateTicket(ticket.id, { status: e.target.value })}
                      className="rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm"
                    >
                      {STATUSES.map((status) => (
                        <option key={status} value={status}>{status}</option>
                      ))}
                    </select>

                    <select
                      defaultValue={ticket.assignee_id ?? ''}
                      onChange={(e) =>
                        updateTicket(ticket.id, { assignee_id: e.target.value ? Number(e.target.value) : null })
                      }
                      className="rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm"
                    >
                      <option value="">Unassigned</option>
                      {employees.map((emp) => (
                        <option key={emp.id} value={emp.id}>
                          {emp.name} - {emp.department}
                        </option>
                      ))}
                    </select>

                    <button
                      onClick={() => loadTimeline(ticket.id)}
                      className="rounded-xl border border-slate-900 px-3 py-2 text-sm font-semibold text-slate-900"
                    >
                      Refresh Timeline
                    </button>
                  </div>
                  )}

                  {role !== 'Requester' && (
                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <div>
                      <textarea
                        placeholder="Internal note"
                        className="w-full rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm"
                        onBlur={(e) => {
                          if (e.target.value.trim()) {
                            addNote(ticket.id, e.target.value.trim())
                            e.target.value = ''
                          }
                        }}
                      />
                      <p className="mt-1 text-xs text-slate-500">Add a note and click away to save.</p>
                    </div>
                    <div>
                      <textarea
                        placeholder="Request more info from the user"
                        className="w-full rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm"
                        onBlur={(e) => {
                          if (e.target.value.trim()) {
                            requestInfo(ticket.id, e.target.value.trim())
                            e.target.value = ''
                          }
                        }}
                      />
                      <p className="mt-1 text-xs text-slate-500">Request info sets status to Pending Info.</p>
                    </div>
                  </div>
                  )}

                  {timelineMap[ticket.id] && (
                    <div className="mt-5 rounded-2xl bg-white/70 px-4 py-3 text-sm">
                      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Timeline</p>
                      <div className="mt-2 space-y-2">
                        {timelineMap[ticket.id].map((event) => (
                          <div key={event.id} className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-semibold">{event.event_type}</span>
                            <span className="text-slate-500">{event.message}</span>
                            <span className="text-xs text-slate-400">
                              {new Date(event.created_at).toLocaleString()}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </article>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
