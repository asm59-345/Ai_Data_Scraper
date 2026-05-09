// src/App.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react'
import Navbar from './components/Navbar.jsx'
import StatsGrid from './components/StatsGrid.jsx'
import ScrapePanel from './components/ScrapePanel.jsx'
import ResultsList from './components/ResultsList.jsx'
import ChartsPanel from './components/ChartsPanel.jsx'
import AboutModal from './components/AboutModal.jsx'
import PastActivityModal from './components/PastActivityModal.jsx'
import Chatbot from './components/Chatbot.jsx'
import LandingPage from './components/LandingPage.jsx'
import { ToastContainer } from './components/Toast.jsx'
import {
  getStats,
  getResults,
  getTags,
  getScrapeStatus,
} from './api/index.js'

let toastId = 0

export default function App() {
  const [stats, setStats] = useState(null)
  const [results, setResults] = useState([])
  const [tags, setTags] = useState([])
  const [status, setStatus] = useState({ running: false })
  const [loading, setLoading] = useState(true)
  const [toasts, setToasts] = useState([])
  const [activeTag, setActiveTag] = useState('')
  const [minScore, setMinScore] = useState(0)
  const [sourceFilter, setSourceFilter] = useState('')
  const [isAboutOpen, setIsAboutOpen] = useState(false)
  const [isActivityOpen, setIsActivityOpen] = useState(false)
  const [theme, setTheme] = useState('dark')
  const [showDashboard, setShowDashboard] = useState(false)

  const pollRef = useRef(null)

  // ── Apply theme ──────────────────────────────────────────────────────────
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  // ── Toast helpers ────────────────────────────────────────────────────────
  const addToast = useCallback((message, type = 'info') => {
    const id = ++toastId
    setToasts((prev) => [...prev, { id, message, type }])
  }, [])

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  // ── Data fetch ───────────────────────────────────────────────────────────
  const fetchAll = useCallback(async () => {
    setLoading(true)
    try {
      const [statsData, resultsData, tagsData, statusData] = await Promise.all([
        getStats().catch(() => null),
        getResults({ limit: 100, min_score: minScore / 100, tag: activeTag || undefined }).catch(() => ({ items: [] })),
        getTags().catch(() => ({ tags: [] })),
        getScrapeStatus().catch(() => ({ running: false })),
      ])
      setStats(statsData)
      setResults(resultsData?.items || [])
      setTags(tagsData?.tags || [])
      setStatus(statusData)
    } finally {
      setLoading(false)
    }
  }, [minScore, activeTag])

  useEffect(() => { fetchAll() }, [fetchAll])

  // ── Poll pipeline status while running ──────────────────────────────────
  useEffect(() => {
    if (status?.running) {
      pollRef.current = setInterval(async () => {
        try {
          const s = await getScrapeStatus()
          setStatus(s)
          if (!s.running) {
            clearInterval(pollRef.current)
            addToast('Scrape complete! Refreshing results…', 'success')
            fetchAll()
          }
        } catch (_) { }
      }, 3000)
    }
    return () => clearInterval(pollRef.current)
  }, [status?.running, fetchAll, addToast])

  const [searchQuery, setSearchQuery] = useState('')

  // ── Derived filtered list ────────────────────────────────────────────────
  const isSearchActive = searchQuery.trim().length > 0 || activeTag || sourceFilter || minScore > 0

  const filtered = results.filter((item) => {
    if (!isSearchActive) return false // Hide by default

    if (sourceFilter && sourceFilter !== 'all' && item.source_type !== sourceFilter) return false

    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      const title = (item.title || '').toLowerCase()
      const author = (item.author || '').toLowerCase()
      const tags = (item.topic_tags || item.tags || []).join(' ').toLowerCase()
      if (!title.includes(q) && !author.includes(q) && !tags.includes(q)) {
        return false
      }
    }
    return true
  })

  const sources = [...new Set(results.map((r) => r.source_type))].filter(Boolean)

  // ── Handlers ─────────────────────────────────────────────────────────────
  const handleScrapeStart = (msg, err) => {
    if (err) { addToast(err, 'error'); return }
    addToast(msg, 'success')
    setStatus((s) => ({ ...s, running: true }))
  }

  const handleClear = () => {
    setResults([])
    setStats(null)
    addToast('Results cleared.', 'info')
  }

  if (!showDashboard) {
    return <LandingPage onLaunch={() => setShowDashboard(true)} theme={theme} />
  }

  return (
    <div className="app-layout">
      <Navbar
        status={status}
        onRefresh={fetchAll}
        onOpenAbout={() => setIsAboutOpen(true)}
        onOpenActivity={() => setIsActivityOpen(true)}
        theme={theme}
        onToggleTheme={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
      />

      <main className="main-content">
        <div style={{ marginBottom: 24 }}>
          <h1 className="section-title">Intelligence Dashboard</h1>
          <p className="section-sub">
            Scrape, score, and explore AI content from blogs, PubMed and YouTube — all in one place.
          </p>
        </div>

        <StatsGrid stats={stats} />

        <div className="dashboard-grid">
          {/* ── Left: Results + Charts ─────────────────────────── */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Filter bar */}
            <div className="card">
              <div className="card-body" style={{ padding: '14px 18px' }}>
                <div className="filter-bar">
                  <input
                    id="filter-search-query"
                    type="text"
                    className="filter-input"
                    placeholder="Search titles, authors, tags..."
                    style={{ width: 220, marginRight: 8 }}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  <input
                    id="filter-min-score"
                    type="number"
                    className="filter-input"
                    placeholder="Min score (0-100)"
                    style={{ width: 140 }}
                    value={minScore || ''}
                    min={0}
                    max={100}
                    onChange={(e) => setMinScore(Number(e.target.value) || 0)}
                  />
                  <select
                    id="filter-source"
                    className="filter-select"
                    value={sourceFilter}
                    onChange={(e) => setSourceFilter(e.target.value)}
                  >
                    <option value="">--- Select Source ---</option>
                    <option value="all">✅ All Sources</option>
                    {sources.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>

                  <div className="tag-cloud" style={{ flex: 1 }}>
                    {tags.slice(0, 10).map((tag) => (
                      <span
                        key={tag}
                        className={`tag-chip ${activeTag === tag ? 'active' : ''}`}
                        onClick={() => setActiveTag((t) => t === tag ? '' : tag)}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>

                  <span style={{ fontSize: 12, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {filtered.length} item{filtered.length !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>
            </div>

            {/* Results */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">🔍 Results</span>
                {status?.running && (
                  <span className="badge badge-amber">⏳ Scraping…</span>
                )}
              </div>
              <div className="card-body">
                <ResultsList items={filtered} loading={loading} />
              </div>
            </div>

            {/* Charts */}
            <ChartsPanel stats={stats} />
          </div>

          {/* ── Right: Scrape panel ────────────────────────────── */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <ScrapePanel
              onScrapeStart={handleScrapeStart}
              onClear={handleClear}
              disabled={status?.running}
            />

            {/* Last run info */}
            {status?.last_run && (
              <div className="card">
                <div className="card-header">
                  <span className="card-title">⏰ Last Run</span>
                </div>
                <div className="card-body">
                  <p className="mono" style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    {new Date(status.last_run).toLocaleString()}
                  </p>
                  {status.last_execution_time_ms && (
                    <p style={{ marginTop: 8, fontSize: 12, color: 'var(--primary)', fontWeight: 500 }}>
                      ⚡ Executed in {status.last_execution_time_ms} ms
                    </p>
                  )}
                  {stats?.execution_time_ms > 0 && !status.last_execution_time_ms && (
                    <p style={{ marginTop: 8, fontSize: 12, color: 'var(--primary)', fontWeight: 500 }}>
                      ⚡ Executed in {stats.execution_time_ms} ms
                    </p>
                  )}
                  {status.error && (
                    <p style={{ marginTop: 8, fontSize: 12, color: '#fb7185' }}>
                      ⚠️ {status.error}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      <AboutModal isOpen={isAboutOpen} onClose={() => setIsAboutOpen(false)} />
      <PastActivityModal isOpen={isActivityOpen} onClose={() => setIsActivityOpen(false)} />
      <Chatbot results={results} />
    </div>
  )
}
