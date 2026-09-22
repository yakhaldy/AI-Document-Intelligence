import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { ApiError, askChat } from '../api'

export default function Chat() {
  const { token } = useAuth()
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    const q = question.trim()
    if (!q) return
    setQuestion('')
    setMessages((prev) => [...prev, { role: 'user', text: q }])
    setLoading(true)
    try {
      const res = await askChat(token, q)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: res.answer, toolsUsed: res.tools_used },
      ])
    } catch (err) {
      const text = err instanceof ApiError ? err.message : "Échec de la requête"
      setMessages((prev) => [...prev, { role: 'error', text }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 640, display: 'flex', flexDirection: 'column', height: 'calc(100vh - 8rem)' }}>
      <h1>Assistant documents</h1>
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.7rem', padding: '0.5rem 0' }}>
        {messages.length === 0 && (
          <p style={{ color: 'var(--color-text-muted)' }}>
            Posez une question libre ("date d'échéance de la facture X ?") ou chiffrée
            ("total des factures impayées ?").
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className="card"
            style={{
              alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '80%',
              borderColor: m.role === 'error' ? 'var(--color-danger)' : undefined,
            }}
          >
            <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{m.text}</p>
            {m.toolsUsed?.length > 0 && (
              <p style={{ margin: '0.5rem 0 0', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                outils : {m.toolsUsed.join(', ')}
              </p>
            )}
          </div>
        ))}
        {loading && <p style={{ color: 'var(--color-text-muted)' }}>L'agent réfléchit…</p>}
      </div>
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', paddingTop: '0.5rem' }}>
        <input
          className="input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Votre question…"
          disabled={loading}
        />
        <button type="submit" className="btn" disabled={loading || !question.trim()}>
          Envoyer
        </button>
      </form>
    </div>
  )
}
