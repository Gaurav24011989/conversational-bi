import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function AppLayout() {
  const { user, logout } = useAuth()

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/projects" className="brand" data-testid="brand-link">
          Conversational BI
        </Link>
        <nav className="app-nav">
          <NavLink to="/projects" data-testid="nav-projects">
            Projects
          </NavLink>
        </nav>
        <div className="header-actions">
          <span className="user-email" data-testid="user-email">
            {user?.email}
          </span>
          <button type="button" onClick={logout} data-testid="logout-button">
            Log out
          </button>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
