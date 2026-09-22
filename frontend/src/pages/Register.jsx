import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, register } from '../api'

export default function Register() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await register(username, password)
      setDone(true)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Inscription impossible')
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div style={{ maxWidth: 360, margin: '4rem auto', padding: '0 1rem' }}>
        <div className="card">
          <p style={{ margin: 0 }}>
            Compte créé. Il doit être approuvé par un administrateur avant que vous puissiez vous connecter.
          </p>
        </div>
        <p style={{ marginTop: '1rem' }}>
          <Link to="/login">Retour à la connexion</Link>
        </p>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 360, margin: '4rem auto', padding: '0 1rem' }}>
      <h1 style={{ marginBottom: '1.5rem' }}>Créer un compte</h1>
      <form onSubmit={handleSubmit} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
        <div>
          <label htmlFor="username" style={{ display: 'block', marginBottom: '0.3rem', fontSize: '0.9rem' }}>
            Nom d'utilisateur
          </label>
          <input
            id="username"
            className="input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            minLength={3}
            required
          />
        </div>
        <div>
          <label htmlFor="password" style={{ display: 'block', marginBottom: '0.3rem', fontSize: '0.9rem' }}>
            Mot de passe
          </label>
          <input
            id="password"
            type="password"
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            minLength={8}
            required
          />
        </div>
        {error && (
          <p role="alert" style={{ color: 'var(--color-danger)', margin: 0, fontSize: '0.9rem' }}>
            {error}
          </p>
        )}
        <button type="submit" className="btn" disabled={loading}>
          {loading ? 'Création…' : 'Créer le compte'}
        </button>
      </form>
      <p style={{ marginTop: '1rem' }}>
        <Link to="/login">J'ai déjà un compte</Link>
      </p>
    </div>
  )
}
