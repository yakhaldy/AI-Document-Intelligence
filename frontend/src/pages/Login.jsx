import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ApiError } from '../api'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(username, password)
      navigate('/factures')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Connexion impossible au serveur')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 360, margin: '4rem auto', padding: '0 1rem' }}>
      <h1 style={{ marginBottom: '0.5rem' }}>AI Document Intelligence</h1>
      <p style={{ marginTop: 0, marginBottom: '1.5rem' }}>
        <Link to="/about">À propos du projet</Link>
      </p>
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
            autoComplete="current-password"
            required
          />
        </div>
        {error && (
          <p role="alert" style={{ color: 'var(--color-danger)', margin: 0, fontSize: '0.9rem' }}>
            {error}
          </p>
        )}
        <button type="submit" className="btn" disabled={loading}>
          {loading ? 'Connexion…' : 'Se connecter'}
        </button>
      </form>
      <p style={{ marginTop: '1rem' }}>
        <Link to="/register">Créer un compte</Link>
      </p>
    </div>
  )
}
