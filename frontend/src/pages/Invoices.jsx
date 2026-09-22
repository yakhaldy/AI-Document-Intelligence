import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { ApiError, listInvoices } from '../api'

const PAGE_SIZE = 20

export default function Invoices() {
  const { token } = useAuth()
  const [page, setPage] = useState(1)
  const [paymentStatus, setPaymentStatus] = useState('')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function fetchInvoices() {
      setLoading(true)
      setError(null)
      try {
        const res = await listInvoices(token, { page, pageSize: PAGE_SIZE, paymentStatus: paymentStatus || undefined })
        if (!cancelled) setData(res)
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : 'Chargement impossible')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchInvoices()
    return () => {
      cancelled = true
    }
  }, [token, page, paymentStatus])

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

  return (
    <div>
      <h1>Factures</h1>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <select
          className="input"
          style={{ width: 'auto' }}
          value={paymentStatus}
          onChange={(e) => {
            setPaymentStatus(e.target.value)
            setPage(1)
          }}
        >
          <option value="">Tous les statuts</option>
          <option value="paid">Payées</option>
          <option value="unpaid">Impayées</option>
        </select>
      </div>

      {error && <p style={{ color: 'var(--color-danger)' }}>{error}</p>}
      {loading && <p style={{ color: 'var(--color-text-muted)' }}>Chargement…</p>}

      {!loading && data && (
        <>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--color-border)' }}>
                  {['N°', 'Fournisseur', 'Date', 'Échéance', 'Total TTC', 'Statut'].map((h) => (
                    <th key={h} style={{ padding: '0.7rem 1rem', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map((inv) => (
                  <tr key={inv.invoice_id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td style={{ padding: '0.7rem 1rem' }}>{inv.invoice_number ?? '—'}</td>
                    <td style={{ padding: '0.7rem 1rem' }}>{inv.supplier_name ?? '—'}</td>
                    <td style={{ padding: '0.7rem 1rem' }}>{inv.invoice_date ?? '—'}</td>
                    <td style={{ padding: '0.7rem 1rem' }}>{inv.due_date ?? '—'}</td>
                    <td style={{ padding: '0.7rem 1rem' }}>
                      {inv.total_ttc ?? '—'} {inv.currency ?? ''}
                    </td>
                    <td style={{ padding: '0.7rem 1rem' }}>
                      <span className={`badge ${inv.payment_status === 'paid' ? 'badge-paid' : 'badge-unpaid'}`}>
                        {inv.payment_status ?? '—'}
                      </span>
                    </td>
                  </tr>
                ))}
                {data.items.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ padding: '1rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                      Aucune facture
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginTop: '1rem' }}>
            <button className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Précédent
            </button>
            <span style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
              Page {page} / {totalPages} — {data.total} facture{data.total > 1 ? 's' : ''}
            </span>
            <button className="btn btn-secondary" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              Suivant
            </button>
          </div>
        </>
      )}
    </div>
  )
}
