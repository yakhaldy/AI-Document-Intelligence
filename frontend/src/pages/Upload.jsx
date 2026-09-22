import { useRef, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { ApiError, uploadDocument } from '../api'
import { docTypeLabel } from '../docTypes'

export default function Upload() {
  const { token } = useAuth()
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await uploadDocument(token, file)
      setResult(res)
      setFile(null)
      if (inputRef.current) inputRef.current.value = ''
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Échec de l'envoi")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 560 }}>
      <h1>Envoyer un document</h1>
      <p style={{ color: 'var(--color-text-muted)' }}>
        Formats acceptés : PDF, JPG, PNG. Le pipeline complet (OCR → classification →
        extraction → indexation) s'exécute automatiquement.
      </p>

      <form onSubmit={handleSubmit} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem', marginTop: '1rem' }}>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="input"
        />
        <button type="submit" className="btn" disabled={!file || loading} style={{ alignSelf: 'flex-start' }}>
          {loading ? 'Traitement en cours…' : 'Envoyer'}
        </button>
      </form>

      {error && (
        <p role="alert" style={{ color: 'var(--color-danger)', marginTop: '1rem' }}>
          {error}
        </p>
      )}

      {result && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <p style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            Document #{result.document_id} traité
            <span className="badge badge-paid">{docTypeLabel(result.doc_type)}</span>
            {result.used_regex_fallback && (
              <span className="badge badge-unpaid">repli regex (LLM indisponible)</span>
            )}
          </p>
          {result.invoice ? (
            <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.3rem 1rem', marginTop: '0.8rem', fontSize: '0.9rem' }}>
              <dt style={{ color: 'var(--color-text-muted)' }}>N° facture</dt>
              <dd style={{ margin: 0 }}>{result.invoice.invoice_number ?? '—'}</dd>
              <dt style={{ color: 'var(--color-text-muted)' }}>Fournisseur</dt>
              <dd style={{ margin: 0 }}>{result.invoice.supplier_name ?? '—'}</dd>
              <dt style={{ color: 'var(--color-text-muted)' }}>Total TTC</dt>
              <dd style={{ margin: 0 }}>
                {result.invoice.total_ttc ?? '—'} {result.invoice.currency ?? ''}
              </dd>
              <dt style={{ color: 'var(--color-text-muted)' }}>Statut</dt>
              <dd style={{ margin: 0 }}>
                <span className={`badge ${result.invoice.payment_status === 'paid' ? 'badge-paid' : 'badge-unpaid'}`}>
                  {result.invoice.payment_status ?? '—'}
                </span>
              </dd>
            </dl>
          ) : (
            <p style={{ color: 'var(--color-text-muted)', marginBottom: 0 }}>
              Document indexé (pas une facture, ou déjà ingéré précédemment).
            </p>
          )}
        </div>
      )}
    </div>
  )
}
