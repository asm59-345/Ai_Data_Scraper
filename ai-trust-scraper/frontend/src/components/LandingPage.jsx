import React from 'react'
import { ArrowRight, ShieldCheck, Database, BarChart3 } from 'lucide-react'

export default function LandingPage({ onLaunch, theme }) {
  const bgImage = "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=2000&auto=format&fit=crop"
  
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-deep)', color: 'var(--text-primary)' }}>
      {/* Hero Section */}
      <div style={{
        position: 'relative', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden'
      }}>
        {/* Background Image with Overlay */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          backgroundImage: `url(${bgImage})`, backgroundSize: 'cover', backgroundPosition: 'center',
          opacity: theme === 'dark' ? 0.3 : 0.15, zIndex: 0
        }} />
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          background: `linear-gradient(to bottom, transparent, var(--bg-deep))`, zIndex: 1
        }} />

        {/* Content */}
        <div style={{ position: 'relative', zIndex: 2, textAlign: 'center', maxWidth: 800, padding: '0 24px' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '8px 16px', background: 'var(--bg-glass)', borderRadius: 999, border: '1px solid var(--border)', marginBottom: 24, fontSize: 13, fontWeight: 600, color: 'var(--accent-light)' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--emerald)', boxShadow: '0 0 10px var(--emerald)' }}></span>
            Platform Live & Operational
          </div>
          <h1 style={{ fontSize: 'clamp(40px, 6vw, 64px)', fontWeight: 800, letterSpacing: '-1.5px', marginBottom: 24, lineHeight: 1.1 }}>
            The Future of <br/>
            <span style={{ background: 'linear-gradient(90deg, var(--accent-light), var(--teal))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              AI Trust Verification
            </span>
          </h1>
          <p style={{ fontSize: 'clamp(16px, 2vw, 20px)', color: 'var(--text-secondary)', marginBottom: 40, lineHeight: 1.6, maxWidth: 600, margin: '0 auto 40px' }}>
            Automate the scraping, aggregation, and credibility scoring of AI-related content from PubMed, YouTube, and global technical blogs in real-time.
          </p>
          <button 
            onClick={onLaunch}
            style={{
              padding: '16px 36px', fontSize: 16, fontWeight: 600, borderRadius: 999,
              background: 'linear-gradient(135deg, var(--accent) 0%, #2563eb 100%)', color: 'white',
              border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 10,
              boxShadow: '0 10px 30px var(--accent-glow)', transition: 'all 0.2s',
            }}
            onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
            onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
          >
            Launch Dashboard <ArrowRight size={18} />
          </button>
        </div>
      </div>

      {/* Features Section */}
      <div style={{ padding: '80px 24px', position: 'relative', zIndex: 2, background: 'var(--bg-deep)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 32 }}>
          <div className="card" style={{ padding: 32, display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(59,130,246,0.1)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Database size={24} />
            </div>
            <h3 style={{ fontSize: 20, color: 'var(--text-primary)' }}>Multi-Source Ingestion</h3>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>Seamlessly scrape full text from technical blogs, peer-reviewed medical abstracts from PubMed, and video transcripts from YouTube.</p>
          </div>
          <div className="card" style={{ padding: 32, display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(20,184,166,0.1)', color: 'var(--teal)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldCheck size={24} />
            </div>
            <h3 style={{ fontSize: 20, color: 'var(--text-primary)' }}>Trust Scoring Engine</h3>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>Advanced multi-factor algorithm scores content out of 100 based on author credibility, citations, domain authority, and medical disclaimers.</p>
          </div>
          <div className="card" style={{ padding: 32, display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(139,92,246,0.1)', color: 'var(--purple)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BarChart3 size={24} />
            </div>
            <h3 style={{ fontSize: 20, color: 'var(--text-primary)' }}>Real-Time Analytics</h3>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>Visualize trends, filter by complex topic tags, and query data dynamically in a responsive command-center dashboard.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
