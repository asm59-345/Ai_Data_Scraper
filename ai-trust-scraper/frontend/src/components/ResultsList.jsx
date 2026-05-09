// src/components/ResultsList.jsx
import React, { useState } from 'react'
import { ExternalLink, ChevronDown, ChevronUp } from 'lucide-react'

const SOURCE_BADGE = {
  pubmed:      'badge-teal',
  openai:      'badge-blue',
  huggingface: 'badge-amber',
  deepmind:    'badge-purple',
  youtube:     'badge-rose',
  blog:        'badge-blue',
}

// Trust score is now 0–1 float; convert to 0–100 for display
function toDisplay(score) {
  if (typeof score === 'string') score = parseFloat(score) || 0
  return score <= 1 ? Math.round(score * 100) : Math.round(score)
}

function scoreColor(display) {
  if (display >= 75) return { bg: 'rgba(16,185,129,0.15)', color: '#34d399', border: 'rgba(16,185,129,0.4)' }
  if (display >= 50) return { bg: 'rgba(245,158,11,0.15)', color: '#fcd34d', border: 'rgba(245,158,11,0.4)' }
  return              { bg: 'rgba(244,63,94,0.15)',  color: '#fb7185', border: 'rgba(244,63,94,0.4)'  }
}

function ResultItem({ item }) {
  const [expanded, setExpanded] = useState(false)

  const source      = item.source_type || item.source || 'blog'
  const title       = item.title || item.video_id || item.pmid || 'Untitled'
  const tags        = item.topic_tags || item.tags || []
  const badgeClass  = SOURCE_BADGE[source] || 'badge-blue'
  const displayScore = toDisplay(item.trust_score)
  const sc          = scoreColor(displayScore)

  const previewText = (item.content || item.abstract || item.transcript || '').slice(0, 260)
    || (item.content_chunks || []).slice(0, 2).join(' ').slice(0, 260)

  // Normalise score_breakdown keys (old keys used different names)
  const breakdown = item.score_breakdown || {}

  return (
    <div className="result-item" onClick={() => setExpanded(v => !v)}>
      <div style={{ minWidth: 0 }}>
        <div className="result-title truncate">{title}</div>
        <div className="result-meta">
          <span className={`badge ${badgeClass}`}>{source}</span>
          {item.language && (
            <span className="badge badge-purple">{item.language.toUpperCase()}</span>
          )}
          {tags.slice(0, 4).map(t => (
            <span key={t} className="tag-chip" style={{ fontSize: 10, padding: '2px 7px' }}>{t}</span>
          ))}
        </div>
        {item.author && (
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
            ✍️ {String(item.author).slice(0, 80)}
          </div>
        )}
        {item.published_date && (
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            📅 {item.published_date}
          </div>
        )}

        {expanded && (
          <div style={{ marginTop: 12 }}>
            {previewText && (
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                {previewText}{previewText.length === 260 ? '…' : ''}
              </p>
            )}

            {Object.keys(breakdown).length > 0 && (
              <div style={{
                marginTop: 12,
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill,minmax(150px,1fr))',
                gap: 8,
              }}>
                {Object.entries(breakdown)
                  .filter(([k]) => k !== 'abuse_penalty_applied')
                  .map(([k, v]) => (
                    <div key={k} style={{ background: 'var(--bg-elevated)', borderRadius: 8, padding: '8px 10px', fontSize: 11 }}>
                      <div style={{ color: 'var(--text-muted)', marginBottom: 3, textTransform: 'capitalize' }}>
                        {k.replace(/_/g, ' ')}
                      </div>
                      <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                        {typeof v === 'number' ? (v <= 1 ? (v * 100).toFixed(0) + '%' : v) : v}
                      </div>
                    </div>
                  ))}
              </div>
            )}

            {item.source_url && (
              <a
                href={item.source_url}
                target="_blank"
                rel="noreferrer"
                onClick={e => e.stopPropagation()}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 5,
                  marginTop: 10, fontSize: 12, color: 'var(--accent-light)',
                  textDecoration: 'none',
                }}
              >
                <ExternalLink size={12} /> Open source
              </a>
            )}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8 }}>
        <div
          className="score-ring"
          style={{ background: sc.bg, color: sc.color, border: `2px solid ${sc.border}` }}
          title={`Trust score: ${displayScore}/100`}
        >
          {displayScore}
        </div>
        <span style={{ color: 'var(--text-muted)', marginTop: 'auto' }}>
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </span>
      </div>
    </div>
  )
}

export default function ResultsList({ items, loading }) {
  if (loading) {
    return (
      <div className="results-list">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="skeleton" style={{ height: 90, borderRadius: 12 }} />
        ))}
      </div>
    )
  }

  if (!items?.length) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📭</div>
        <div className="empty-state-msg">Type in the search bar or use filters to see results.</div>
      </div>
    )
  }

  return (
    <div className="results-list">
      {items.map((item, idx) => (
        <ResultItem
          key={item.pmid || item.source_url || item.video_id || idx}
          item={item}
        />
      ))}
    </div>
  )
}
