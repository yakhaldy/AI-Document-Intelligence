import { useState } from 'react'
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
  const [navOpen, setNavOpen] = useState(false)
  const navLinks = isAdmin ? [...links, { to: '/admin', label: 'Admin' }] : links

  return (
    <div style={{ minHeight: '100%', display: 'flex', flexDirection: 'column' }}>
      <header className="app-header">
        <strong>AI Document Intelligence</strong>
        <button
          type="button"
          className="nav-toggle"
          aria-label="Ouvrir le menu"
          aria-expanded={navOpen}
          onClick={() => setNavOpen((v) => !v)}
        >
          ☰
        </button>
        <nav className={navOpen ? 'app-nav app-nav-open' : 'app-nav'}>
          {navLinks.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              onClick={() => setNavOpen(false)}
              style={({ isActive }) => ({
                color: isActive ? 'var(--color-link)' : 'var(--color-text)',
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
      <footer style={{ padding: '1rem 1.5rem', textAlign: 'center' }}>
        <NavLink to="/legal" style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
          Informations légales
        </NavLink>
      </footer>
    </div>
  )
}
