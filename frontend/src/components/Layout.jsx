import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const links = [
  { to: '/factures', label: 'Factures' },
  { to: '/documents', label: 'Documents' },
  { to: '/upload', label: 'Envoyer' },
  { to: '/chat', label: 'Assistant' },
]

export default function Layout() {
  const { logout, isAdmin } = useAuth()
  const navLinks = isAdmin ? [...links, { to: '/admin', label: 'Admin' }] : links

  return (
    <div style={{ minHeight: '100%', display: 'flex', flexDirection: 'column' }}>
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '1rem 1.5rem',
          borderBottom: '1px solid var(--color-border)',
        }}
      >
        <strong>AI Document Intelligence</strong>
        <nav style={{ display: 'flex', gap: '1.2rem', alignItems: 'center' }}>
          {navLinks.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              style={({ isActive }) => ({
                color: isActive ? 'var(--color-primary)' : 'var(--color-text)',
                fontWeight: isActive ? 600 : 400,
                textDecoration: 'none',
              })}
            >
              {l.label}
            </NavLink>
          ))}
          <button type="button" className="btn btn-secondary" onClick={logout}>
            Déconnexion
          </button>
        </nav>
      </header>
      <main style={{ flex: 1, padding: '1.5rem' }}>
        <Outlet />
      </main>
    </div>
  )
}
