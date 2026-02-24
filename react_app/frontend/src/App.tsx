import { Routes, Route, NavLink } from 'react-router-dom'
import ReconcilePage from './pages/ReconcilePage'
import ProfilesPage from './pages/ProfilesPage'

export default function App() {
  return (
    <div className="app-layout">
      <nav className="sidebar">
        <NavLink
          to="/"
          end
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
        >
          Reconciliation
        </NavLink>
        <NavLink
          to="/profiles"
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
        >
          Configuration Profiles
        </NavLink>
      </nav>
      <div className="main-content">
        <Routes>
          <Route path="/" element={<ReconcilePage />} />
          <Route path="/profiles" element={<ProfilesPage />} />
        </Routes>
      </div>
    </div>
  )
}
