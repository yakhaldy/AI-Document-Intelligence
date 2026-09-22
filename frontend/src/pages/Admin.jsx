import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { ApiError, approveUser, listUsers, rejectUser } from '../api'

export default function Admin() {
  const { token } = useAuth()
  const [users, setUsers] = useState(null)
  const [error, setError] = useState(null)
  const [busyId, setBusyId] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const res = await listUsers(token)
      setUsers(res)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Chargement impossible')
    }
  }, [token])

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const res = await listUsers(token)
        if (!cancelled) setUsers(res)
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : 'Chargement impossible')
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [token])

  async function handleDecision(userId, action) {
    setBusyId(userId)
    setError(null)
    try {
      if (action === 'approve') await approveUser(token, userId)
      else await rejectUser(token, userId)
      await refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Action impossible')
    } finally {
      setBusyId(null)
    }
  }

  const pending = users?.filter((u) => u.status === 'pending') ?? []
  const others = users?.filter((u) => u.status !== 'pending') ?? []

  return (
    <div style={{ maxWidth: 720 }}>
      <h1>Comptes utilisateurs</h1>
      {error && <p style={{ color: 'var(--color-danger)' }}>{error}</p>}

      <h2 style={{ fontSize: '1.1rem' }}>En attente d'approbation ({pending.length})</h2>
      {users === null && <p style={{ color: 'var(--color-text-muted)' }}>Chargement…</p>}
      {users !== null && pending.length === 0 && (
        <p style={{ color: 'var(--color-text-muted)' }}>Aucun compte en attente.</p>
      )}
      {pending.map((u) => (
        <div key={u.id} className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
          <span>{u.username}</span>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn" disabled={busyId === u.id} onClick={() => handleDecision(u.id, 'approve')}>
              Approuver
            </button>
            <button className="btn btn-secondary" disabled={busyId === u.id} onClick={() => handleDecision(u.id, 'reject')}>
              Rejeter
            </button>
          </div>
        </div>
      ))}

      {others.length > 0 && (
        <>
          <h2 style={{ fontSize: '1.1rem', marginTop: '1.5rem' }}>Autres comptes</h2>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--color-border)' }}>
                  <th style={{ padding: '0.6rem 1rem', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Utilisateur</th>
                  <th style={{ padding: '0.6rem 1rem', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Rôle</th>
                  <th style={{ padding: '0.6rem 1rem', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Statut</th>
                </tr>
              </thead>
              <tbody>
                {others.map((u) => (
                  <tr key={u.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td style={{ padding: '0.6rem 1rem' }}>{u.username}</td>
                    <td style={{ padding: '0.6rem 1rem' }}>{u.role}</td>
                    <td style={{ padding: '0.6rem 1rem' }}>
                      <span className={`badge ${u.status === 'approved' ? 'badge-paid' : 'badge-unpaid'}`}>{u.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
