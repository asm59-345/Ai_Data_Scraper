// src/components/Navbar.jsx
import React from 'react'
import { Activity, Info, Sun, Moon, Clock } from 'lucide-react'

export default function Navbar({ status, onRefresh, onOpenAbout, theme, onToggleTheme, onOpenActivity }) {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <div className="navbar-logo">🔬</div>
        <div>
          <div className="navbar-title">AI Trust Scraper</div>
        </div>
      </div>

      <div className="navbar-actions">
        {status?.running ? (
          <span className="status-pill">
            <span className="pulse-dot running" />
            Scraping…
          </span>
        ) : (
          <span className="status-pill">
            <span className="pulse-dot" />
            Ready
          </span>
        )}
        <button className="btn btn-ghost" onClick={onOpenActivity} title="Past Activity" style={{ marginRight: 4, padding: '9px 12px' }}>
          <Clock size={15} />
        </button>
        <button className="btn btn-ghost" onClick={onToggleTheme} title="Toggle theme" style={{ marginRight: 4, padding: '9px 12px' }}>
          {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
        </button>
        <button className="btn btn-ghost" onClick={onOpenAbout} title="About this project" style={{ marginRight: 8 }}>
          <Info size={15} />
          About
        </button>
        <button className="btn btn-ghost" onClick={onRefresh} title="Refresh data">
          <Activity size={15} />
          Refresh
        </button>
      </div>
    </nav>
  )
}
