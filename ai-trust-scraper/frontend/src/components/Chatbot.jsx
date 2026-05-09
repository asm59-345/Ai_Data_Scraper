import React, { useState, useRef, useEffect } from 'react'
import { MessageSquare, X, Send, Bot, User } from 'lucide-react'

export default function Chatbot({ results }) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    { id: 1, text: "Hi! I'm your AI Dashboard Assistant. Ask me anything about the scraped content, trust scores, or sources!", sender: 'ai' }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const handleSend = (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMsg = { id: Date.now(), text: input, sender: 'user' }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsTyping(true)

    // Simulate AI processing and querying the local results data
    setTimeout(() => {
      const query = userMsg.text.toLowerCase()
      let aiResponse = "I'm not sure about that. Try asking about our top articles, sources like PubMed or YouTube, or average trust scores."

      if (query.includes('top') || query.includes('highest')) {
        const top = [...results].sort((a, b) => b.trust_score - a.trust_score)[0]
        if (top) {
          aiResponse = `The highest trusted article is "${top.title}" from ${top.source_type} with a score of ${Math.round(top.trust_score * 100)}/100.`
        }
      } else if (query.includes('pubmed') || query.includes('medical')) {
        const pm = results.filter(r => r.source_type === 'pubmed')
        aiResponse = `We have scraped ${pm.length} articles from PubMed.`
      } else if (query.includes('youtube') || query.includes('video')) {
        const yt = results.filter(r => r.source_type === 'youtube')
        aiResponse = `We have scraped ${yt.length} YouTube videos.`
      } else if (query.includes('hello') || query.includes('hi')) {
        aiResponse = "Hello there! How can I help you analyze the dashboard data today?"
      } else if (query.includes('how many')) {
        aiResponse = `Currently, we have a total of ${results.length} scraped items in the database.`
      } else {
        // Generic simulated AI response
        aiResponse = `Based on my AI analysis of the data, your query "${input}" highlights interesting trends in our database of ${results.length} articles. Try using the filter bar to narrow down the results!`
      }

      setMessages(prev => [...prev, { id: Date.now() + 1, text: aiResponse, sender: 'ai' }])
      setIsTyping(false)
    }, 1500)
  }

  return (
    <>
      {/* Floating Action Button */}
      <button 
        onClick={() => setIsOpen(true)}
        style={{
          position: 'fixed', bottom: 30, right: 30, zIndex: 999,
          width: 60, height: 60, borderRadius: '50%', background: 'var(--accent)',
          color: 'white', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          display: isOpen ? 'none' : 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', transition: 'transform 0.2s'
        }}
        onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.05)'}
        onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
      >
        <MessageSquare size={28} />
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div style={{
          position: 'fixed', bottom: 30, right: 30, zIndex: 1000,
          width: 350, height: 500, background: 'var(--bg-card)',
          border: '1px solid var(--border)', borderRadius: 16,
          boxShadow: '0 8px 24px rgba(0,0,0,0.4)', display: 'flex', flexDirection: 'column',
          overflow: 'hidden'
        }}>
          {/* Header */}
          <div style={{
            background: 'var(--accent)', color: 'white', padding: '16px',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Bot size={20} />
              <strong style={{ fontSize: 16 }}>AI Assistant</strong>
            </div>
            <button onClick={() => setIsOpen(false)} style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer' }}>
              <X size={20} />
            </button>
          </div>

          {/* Messages Area */}
          <div style={{ flex: 1, padding: 16, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 12, background: 'var(--bg-main)' }}>
            {messages.map(msg => (
              <div key={msg.id} style={{
                display: 'flex', gap: 8, alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '85%', flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row'
              }}>
                <div style={{ 
                  width: 28, height: 28, borderRadius: '50%', background: msg.sender === 'user' ? 'var(--accent-light)' : 'var(--border)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', color: msg.sender === 'user' ? 'white' : 'var(--text-primary)', flexShrink: 0
                }}>
                  {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
                </div>
                <div style={{
                  background: msg.sender === 'user' ? 'var(--accent)' : 'var(--bg-card)',
                  color: msg.sender === 'user' ? 'white' : 'var(--text-primary)',
                  padding: '10px 14px', borderRadius: 16, fontSize: 13, lineHeight: 1.5,
                  border: msg.sender === 'ai' ? '1px solid var(--border)' : 'none',
                  borderTopLeftRadius: msg.sender === 'ai' ? 4 : 16,
                  borderTopRightRadius: msg.sender === 'user' ? 4 : 16,
                }}>
                  {msg.text}
                </div>
              </div>
            ))}
            {isTyping && (
              <div style={{ display: 'flex', gap: 8, alignSelf: 'flex-start', maxWidth: '85%' }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-primary)', flexShrink: 0 }}>
                  <Bot size={16} />
                </div>
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', padding: '10px 14px', borderRadius: 16, fontSize: 13, borderTopLeftRadius: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span className="dot-typing"></span><span className="dot-typing"></span><span className="dot-typing"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <form onSubmit={handleSend} style={{
            padding: 12, borderTop: '1px solid var(--border)', background: 'var(--bg-card)',
            display: 'flex', gap: 8
          }}>
            <input 
              type="text" 
              value={input} 
              onChange={e => setInput(e.target.value)}
              placeholder="Ask the AI..."
              style={{
                flex: 1, background: 'var(--bg-main)', border: '1px solid var(--border)',
                borderRadius: 20, padding: '8px 16px', color: 'var(--text-primary)', fontSize: 14, outline: 'none'
              }}
            />
            <button type="submit" disabled={!input.trim()} style={{
              background: 'var(--accent)', color: 'white', border: 'none', width: 36, height: 36,
              borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: input.trim() ? 'pointer' : 'default', opacity: input.trim() ? 1 : 0.5
            }}>
              <Send size={16} style={{ marginLeft: 2 }} />
            </button>
          </form>
        </div>
      )}

      {/* Global CSS for typing animation */}
      <style>{`
        .dot-typing {
          width: 4px; height: 4px; background: var(--text-muted); borderRadius: 50%;
          animation: bounce 1.4s infinite ease-in-out both;
        }
        .dot-typing:nth-child(1) { animation-delay: -0.32s; }
        .dot-typing:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
      `}</style>
    </>
  )
}
