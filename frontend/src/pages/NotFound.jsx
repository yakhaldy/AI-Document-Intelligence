import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div style={{ maxWidth: 480, margin: '4rem auto', padding: '0 1rem', textAlign: 'center' }}>
      <h1 style={{ fontSize: '3rem', margin: 0 }}>404</h1>
      <p style={{ color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
        Cette page n'existe pas.
      </p>
      <Link to="/" className="btn" style={{ marginTop: '1.5rem', display: 'inline-flex' }}>
        Retour à l'accueil
      </Link>
    </div>
  )
}
