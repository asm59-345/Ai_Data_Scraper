// src/components/ScrapePanel.jsx
import React, { useState } from 'react'
import { triggerScrape } from '../api/index.js'
import { Play, Loader2, Trash2 } from 'lucide-react'
import { clearResults } from '../api/index.js'

const SOURCE_OPTIONS = [
  { id: 'blog',    label: 'Blog',    desc: 'OpenAI, HuggingFace, DeepMind' },
  { id: 'pubmed',  label: 'PubMed',  desc: 'Peer-reviewed research abstracts' },
  { id: 'youtube', label: 'YouTube', desc: 'AI video transcripts' },
]

export default function ScrapePanel({ onScrapeStart, onClear, disabled }) {
  const [selected, setSelected] = useState(['blog', 'pubmed', 'youtube'])
  const [pubmedMax, setPubmedMax] = useState(10)
  const [scrapeQuery, setScrapeQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [clearing, setClearing] = useState(false)

  const toggle = (id) =>
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    )

  const handleScrape = async () => {
    if (!selected.length) return
    setLoading(true)
    try {
      await triggerScrape({ sources: selected, pubmed_max: pubmedMax, query: scrapeQuery || undefined })
      
      // Auto-save past activity to localStorage
      const history = JSON.parse(localStorage.getItem('ai_trust_activity') || '[]')
      history.unshift({
        id: Date.now(),
        date: new Date().toISOString(),
        query: scrapeQuery || 'Default (No query)',
        sources: selected,
        max: pubmedMax
      })
      localStorage.setItem('ai_trust_activity', JSON.stringify(history.slice(0, 50))) // keep last 50

      onScrapeStart?.('Scraping pipeline started!')
    } catch (err) {
      onScrapeStart?.(null, err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleClear = async () => {
    setClearing(true)
    try {
      await clearResults()
      onClear?.()
    } catch (err) {
      console.error(err)
    } finally {
      setClearing(false)
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">🚀 New Scrape</span>
      </div>
      <div className="card-body scrape-panel">
        <div className="source-checkboxes">
          {SOURCE_OPTIONS.map((src) => (
            <label key={src.id} className="checkbox-row">
              <input
                type="checkbox"
                checked={selected.includes(src.id)}
                onChange={() => toggle(src.id)}
              />
              <div>
                <div className="checkbox-label">{src.label}</div>
                <div className="checkbox-desc">{src.desc}</div>
              </div>
            </label>
          ))}
        </div>

        <div>
          <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>
            Search Topic
          </label>
          <input
            type="text"
            className="filter-input"
            style={{ width: '100%', marginBottom: 12 }}
            placeholder="e.g. machine learning, cancer..."
            value={scrapeQuery}
            onChange={(e) => setScrapeQuery(e.target.value)}
          />
        </div>

        <div>
          <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>
            Max results
          </label>
          <input
            type="number"
            className="filter-input"
            style={{ width: '100%' }}
            value={pubmedMax}
            min={1}
            max={100}
            onChange={(e) => setPubmedMax(Number(e.target.value))}
          />
        </div>

        <button
          className="btn btn-primary"
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={handleScrape}
          disabled={loading || disabled || !selected.length}
          id="btn-start-scrape"
        >
          {loading
            ? <><Loader2 size={15} className="spin" />Starting…</>
            : <><Play size={15} />Run Pipeline</>}
        </button>

        <div className="divider" />

        <button
          className="btn btn-danger"
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={handleClear}
          disabled={clearing}
          id="btn-clear-results"
        >
          {clearing
            ? <><Loader2 size={15} className="spin" />Clearing…</>
            : <><Trash2 size={15} />Clear Results</>}
        </button>
      </div>
    </div>
  )
}
