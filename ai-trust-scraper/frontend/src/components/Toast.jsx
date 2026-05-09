// src/components/Toast.jsx
import React, { useEffect } from 'react'
import { CheckCircle, XCircle, Info } from 'lucide-react'

const ICONS = {
  success: <CheckCircle size={16} />,
  error:   <XCircle   size={16} />,
  info:    <Info      size={16} />,
}

export function Toast({ id, type = 'info', message, onDismiss }) {
  useEffect(() => {
    const t = setTimeout(() => onDismiss(id), 4000)
    return () => clearTimeout(t)
  }, [id, onDismiss])

  return (
    <div className={`toast toast-${type}`}>
      {ICONS[type]}
      <span>{message}</span>
    </div>
  )
}

export function ToastContainer({ toasts, onDismiss }) {
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <Toast key={t.id} {...t} onDismiss={onDismiss} />
      ))}
    </div>
  )
}
