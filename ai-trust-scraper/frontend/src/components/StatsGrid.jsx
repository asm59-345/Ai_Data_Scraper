// src/components/StatsGrid.jsx
import React from 'react'

const ICONS = {
  total:   { icon: '📄', bg: 'rgba(59,130,246,0.12)',  color: '#60a5fa' },
  avg:     { icon: '⭐', bg: 'rgba(245,158,11,0.12)',  color: '#fcd34d' },
  max:     { icon: '🏆', bg: 'rgba(16,185,129,0.12)',  color: '#34d399' },
  sources: { icon: '🌐', bg: 'rgba(139,92,246,0.12)', color: '#a78bfa' },
}

// scores come from API as 0–1 floats; display as 0–100
function fmt(val) {
  if (val == null || val === '—') return '—'
  const n = parseFloat(val)
  if (isNaN(n)) return val
  if (n <= 1.0) return (n * 100).toFixed(1)
  return n.toFixed(1)
}

function StatCard({ icon, bg, color, value, label }) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ background: bg, color }}>{icon}</div>
      <div className="stat-value">{value ?? '—'}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

export default function StatsGrid({ stats }) {
  const sourcesCount = stats?.by_source ? Object.keys(stats.by_source).length : 0

  return (
    <div className="stats-grid">
      <StatCard {...ICONS.total}   value={stats?.total_items ?? 0}            label="Total Articles"  />
      <StatCard {...ICONS.avg}     value={fmt(stats?.avg_trust_score)}        label="Avg Trust Score" />
      <StatCard {...ICONS.max}     value={fmt(stats?.max_trust_score)}        label="Top Score"       />
      <StatCard {...ICONS.sources} value={sourcesCount}                       label="Sources Active"  />
    </div>
  )
}
