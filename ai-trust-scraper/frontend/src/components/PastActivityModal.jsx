import React, { useState, useEffect } from 'react'
import { X, Clock, Trash2 } from 'lucide-react'

export default function PastActivityModal({ isOpen, onClose }) {
  const [history, setHistory] = useState([])

  useEffect(() => {
    if (isOpen) {
      setHistory(JSON.parse(localStorage.getItem('ai_trust_activity') || '[]'))
    }
  }, [isOpen])

  const handleClear = () => {
    localStorage.removeItem('ai_trust_activity')
    setHistory([])
  }

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose} style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1000,
      display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(4px)'
    }}>
      <div className="card" onClick={e => e.stopPropagation()} style={{
        maxWidth: 550, width: '90%', maxHeight: '85vh', display: 'flex', flexDirection: 'column',
        background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 12, overflow: 'hidden'
      }}>
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Clock size={16} /> Past Activity
          </span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>
        
        <div className="card-body" style={{ overflowY: 'auto', flex: 1, padding: 16 }}>
          {history.length === 0 ? (
             <div className="empty-state" style={{ padding: '40px 20px' }}>
               <div className="empty-state-icon">📝</div>
               <div className="empty-state-msg">No past activity found. Start a scrape!</div>
             </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {history.map(item => (
                <div key={item.id} style={{
                  padding: 14, borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-elevated)',
                  display: 'flex', flexDirection: 'column', gap: 6
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong style={{ color: 'var(--text-primary)', fontSize: 14 }}>"{item.query}"</strong>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {new Date(item.date).toLocaleString()}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {item.sources.map(s => (
                      <span key={s} className="badge badge-purple" style={{ fontSize: 10, padding: '2px 8px' }}>{s}</span>
                    ))}
                    <span className="badge badge-blue" style={{ fontSize: 10, padding: '2px 8px' }}>Max: {item.max}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {history.length > 0 && (
          <div style={{ padding: 16, borderTop: '1px solid var(--border)', background: 'var(--bg-elevated)' }}>
             <button className="btn btn-danger" style={{ width: '100%', justifyContent: 'center' }} onClick={handleClear}>
               <Trash2 size={15} /> Clear History
             </button>
          </div>
        )}
      </div>
    </div>
  )
}
