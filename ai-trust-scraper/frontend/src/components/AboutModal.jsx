import React from 'react'
import { X } from 'lucide-react'

export default function AboutModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose} style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1000,
      display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(4px)'
    }}>
      <div className="card" onClick={e => e.stopPropagation()} style={{
        maxWidth: 500, width: '90%', maxHeight: '90vh', overflowY: 'auto',
        background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 12
      }}>
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="card-title">ℹ️ About This Project</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>
        <div className="card-body" style={{ lineHeight: 1.6, color: 'var(--text-secondary)' }}>
          <p>
            <strong>AI Trust Scraper</strong> is a full-stack platform designed to scrape, aggregate, and evaluate the trustworthiness of AI-related content from diverse sources such as PubMed, YouTube, and technical blogs.
          </p>
          <h4 style={{ color: 'var(--text-primary)', marginTop: 16, marginBottom: 8 }}>Features</h4>
          <ul style={{ paddingLeft: 20 }}>
            <li><strong>Automated Scraping:</strong> Pulls articles, transcripts, and metadata.</li>
            <li><strong>Trust Scoring Algorithm:</strong> Evaluates content out of 100 based on Author Credibility, Citation Score, Domain Authority, Recency, and Medical Disclaimers.</li>
            <li><strong>Real-time Dashboard:</strong> Search, filter, and visualize data trends instantly.</li>
          </ul>
          <h4 style={{ color: 'var(--text-primary)', marginTop: 16, marginBottom: 8 }}>Tech Stack</h4>
          <p>Built with <strong>React/Vite</strong> on the frontend and <strong>FastAPI/Python</strong> on the backend.</p>
        </div>
      </div>
    </div>
  )
}
