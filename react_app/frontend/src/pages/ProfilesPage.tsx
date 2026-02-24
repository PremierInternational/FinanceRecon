import { useState, useEffect } from 'react'
import Header from '../components/Header'
import { fetchProfiles, deleteProfileApi } from '../api'
import type { ProfilesMap } from '../types'

export default function ProfilesPage() {
  const [profiles, setProfiles] = useState<ProfilesMap>({})
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    setLoading(true)
    fetchProfiles()
      .then((p) => {
        setProfiles(p)
        setLoading(false)
      })
      .catch((e) => {
        setError(String(e))
        setLoading(false)
      })
  }

  useEffect(() => {
    load()
  }, [])

  const handleDelete = async (name: string) => {
    try {
      await deleteProfileApi(name)
      load()
    } catch (e) {
      setError(String(e))
    }
  }

  const toggleExpand = (name: string) => {
    setExpanded((prev) => ({ ...prev, [name]: !prev[name] }))
  }

  const names = Object.keys(profiles)

  return (
    <div>
      <Header title="Configuration Profiles" />
      <div className="page-body">
        <p style={{ color: 'var(--cool-gray)', marginBottom: '1.25rem', fontSize: '0.9rem' }}>
          Saved profiles can be loaded from the <strong>Reconciliation</strong> page via the
          Load Profile dropdown.
        </p>

        {loading && <div className="msg-info">Loading profiles…</div>}
        {error && <div className="msg-error">{error}</div>}

        {!loading && names.length === 0 && (
          <div className="msg-info">
            No configuration profiles saved yet. Go to the Reconciliation page, configure a
            comparison, and click Save.
          </div>
        )}

        {!loading && names.length > 0 && (
          <>
            <p style={{ color: 'var(--white)', fontWeight: 600, marginBottom: '0.75rem' }}>
              {names.length} profile{names.length !== 1 ? 's' : ''} saved
            </p>
            <hr className="divider" />
            {names.map((name) => {
              const cfg = profiles[name]
              const isOpen = expanded[name] ?? false
              const tolDisplay =
                cfg.tolerance_type === 'None' || !cfg.tolerance_type
                  ? 'None'
                  : `${cfg.tolerance_type} ${cfg.tolerance_value ?? ''}`

              return (
                <div className="profile-card" key={name}>
                  <div className="profile-card-header" onClick={() => toggleExpand(name)}>
                    <span>{name}</span>
                    <div className="profile-card-header-actions">
                      <button
                        className="btn-danger"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(name)
                        }}
                      >
                        Delete
                      </button>
                      <span className={`chevron ${isOpen ? 'open' : ''}`}>▼</span>
                    </div>
                  </div>
                  {isOpen && (
                    <div className="profile-card-body">
                      <div>
                        <strong>Match keys (first file):</strong>{' '}
                        {cfg.match_keys_first?.join(', ') || '—'}
                      </div>
                      <div>
                        <strong>Match keys (second file):</strong>{' '}
                        {cfg.match_keys_second?.join(', ') || '—'}
                      </div>
                      <div>
                        <strong>Compare column (first file):</strong>{' '}
                        {cfg.compare_col_first || '—'}
                      </div>
                      <div>
                        <strong>Compare column (second file):</strong>{' '}
                        {cfg.compare_col_second || '—'}
                      </div>
                      <div>
                        <strong>Tolerance:</strong> {tolDisplay}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </>
        )}
      </div>
    </div>
  )
}
