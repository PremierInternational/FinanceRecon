import { useState, useEffect, useRef } from 'react'
import Select from 'react-select'
import Header from '../components/Header'
import {
  getColumns,
  runCompare,
  getDownloadUrl,
  fetchProfiles,
  saveProfileApi,
} from '../api'
import type { CompareResult, ProfilesMap } from '../types'

// react-select styles to match brand theme
const selectStyles = {
  control: (base: Record<string, unknown>) => ({
    ...base,
    backgroundColor: '#ffffff',
    borderColor: '#cccccc',
    color: '#000000',
    minHeight: '38px',
    boxShadow: 'none',
  }),
  option: (
    base: Record<string, unknown>,
    state: { isSelected: boolean; isFocused: boolean },
  ) => ({
    ...base,
    backgroundColor: state.isSelected
      ? '#0d2c71'
      : state.isFocused
        ? '#e8e8f0'
        : '#ffffff',
    color: '#000000',
  }),
  menu: (base: Record<string, unknown>) => ({
    ...base,
    backgroundColor: '#ffffff',
    zIndex: 9999,
  }),
  menuPortal: (base: Record<string, unknown>) => ({ ...base, zIndex: 9999 }),
  multiValue: (base: Record<string, unknown>) => ({
    ...base,
    backgroundColor: '#d8d7ee',
  }),
  multiValueLabel: (base: Record<string, unknown>) => ({
    ...base,
    color: '#000000',
  }),
  multiValueRemove: (base: Record<string, unknown>) => ({
    ...base,
    color: '#000000',
    ':hover': { backgroundColor: '#0d2c71', color: '#ffffff' },
  }),
  singleValue: (base: Record<string, unknown>) => ({
    ...base,
    color: '#000000',
  }),
  placeholder: (base: Record<string, unknown>) => ({
    ...base,
    color: '#666666',
  }),
}

type FileStatus = 'idle' | 'loading' | 'success' | 'error'

function toOptions(cols: string[]) {
  return cols.map((c) => ({ value: c, label: c }))
}

function toMultiValue(selected: string[]) {
  return selected.map((c) => ({ value: c, label: c }))
}

function toSingleValue(selected: string) {
  return selected ? { value: selected, label: selected } : null
}

function formatCell(val: unknown): string {
  if (val === null || val === undefined) return ''
  if (typeof val === 'boolean') return val ? 'True' : 'False'
  if (typeof val === 'number') {
    return isFinite(val) ? val.toLocaleString('en-US', { maximumFractionDigits: 4 }) : ''
  }
  return String(val)
}

export default function ReconcilePage() {
  const [firstFile, setFirstFile] = useState<File | null>(null)
  const [secondFile, setSecondFile] = useState<File | null>(null)
  const [firstCols, setFirstCols] = useState<string[]>([])
  const [secondCols, setSecondCols] = useState<string[]>([])
  const [firstStatus, setFirstStatus] = useState<FileStatus>('idle')
  const [secondStatus, setSecondStatus] = useState<FileStatus>('idle')
  const [firstName, setFirstName] = useState('')
  const [secondName, setSecondName] = useState('')

  const [matchKeysFirst, setMatchKeysFirst] = useState<string[]>([])
  const [matchKeysSecond, setMatchKeysSecond] = useState<string[]>([])
  const [compareColFirst, setCompareColFirst] = useState<string>('')
  const [compareColSecond, setCompareColSecond] = useState<string>('')
  const [toleranceType, setToleranceType] = useState<string>('None')
  const [toleranceValue, setToleranceValue] = useState<number>(0)

  const [profiles, setProfiles] = useState<ProfilesMap>({})
  const [selectedProfile, setSelectedProfile] = useState<string>('')
  const [profileName, setProfileName] = useState<string>('')
  const [saveMsg, setSaveMsg] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)

  const [result, setResult] = useState<CompareResult | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [runError, setRunError] = useState<string | null>(null)

  const [showDiffsOnly, setShowDiffsOnly] = useState(false)
  const [showMatchesOnly, setShowMatchesOnly] = useState(false)

  const firstInputRef = useRef<HTMLInputElement>(null)
  const secondInputRef = useRef<HTMLInputElement>(null)

  const bothLoaded = firstCols.length > 0 && secondCols.length > 0

  // Fetch profiles once both files are loaded
  useEffect(() => {
    if (bothLoaded) {
      fetchProfiles().then(setProfiles).catch(() => {})
    }
  }, [bothLoaded])

  const handleFirstFile = async (file: File) => {
    setFirstFile(file)
    setFirstName(file.name)
    setFirstStatus('loading')
    setFirstCols([])
    try {
      const cols = await getColumns(file)
      setFirstCols(cols)
      setFirstStatus('success')
      if (cols.length > 0) setCompareColFirst(cols[0])
    } catch {
      setFirstStatus('error')
    }
  }

  const handleSecondFile = async (file: File) => {
    setSecondFile(file)
    setSecondName(file.name)
    setSecondStatus('loading')
    setSecondCols([])
    try {
      const cols = await getColumns(file)
      setSecondCols(cols)
      setSecondStatus('success')
      if (cols.length > 0) setCompareColSecond(cols[0])
    } catch {
      setSecondStatus('error')
    }
  }

  const handleLoadProfile = () => {
    if (!selectedProfile || !profiles[selectedProfile]) return
    const cfg = profiles[selectedProfile]
    setMatchKeysFirst(cfg.match_keys_first.filter((k) => firstCols.includes(k)))
    setMatchKeysSecond(cfg.match_keys_second.filter((k) => secondCols.includes(k)))
    if (cfg.compare_col_first && firstCols.includes(cfg.compare_col_first)) {
      setCompareColFirst(cfg.compare_col_first)
    }
    if (cfg.compare_col_second && secondCols.includes(cfg.compare_col_second)) {
      setCompareColSecond(cfg.compare_col_second)
    }
    setToleranceType(cfg.tolerance_type || 'None')
    setToleranceValue(cfg.tolerance_value ?? 0)
  }

  const handleRun = async () => {
    if (!firstFile || !secondFile) return
    setIsRunning(true)
    setRunError(null)
    setResult(null)
    try {
      const res = await runCompare(firstFile, secondFile, {
        match_keys_first: matchKeysFirst,
        match_keys_second: matchKeysSecond,
        compare_col_first: compareColFirst,
        compare_col_second: compareColSecond,
        tolerance_type: toleranceType,
        tolerance_value: toleranceType !== 'None' ? toleranceValue : null,
      })
      setResult(res)
      setShowDiffsOnly(false)
      setShowMatchesOnly(false)
    } catch (e) {
      setRunError(String(e))
    } finally {
      setIsRunning(false)
    }
  }

  const handleSaveProfile = async () => {
    setSaveMsg(null)
    setSaveError(null)
    if (!profileName.trim()) {
      setSaveError('Enter a profile name before saving.')
      return
    }
    try {
      await saveProfileApi(profileName.trim(), {
        match_keys_first: matchKeysFirst,
        match_keys_second: matchKeysSecond,
        compare_col_first: compareColFirst,
        compare_col_second: compareColSecond,
        tolerance_type: toleranceType,
        tolerance_value: toleranceType !== 'None' ? toleranceValue : null,
      })
      setSaveMsg(`Profile '${profileName.trim()}' saved!`)
      setProfileName('')
      const updated = await fetchProfiles()
      setProfiles(updated)
    } catch (e) {
      setSaveError(String(e))
    }
  }

  // Compute filtered rows
  const filteredRows = result
    ? result.rows.filter((row) => {
        if (showDiffsOnly && !showMatchesOnly) return row['Difference'] === true
        if (showMatchesOnly && !showDiffsOnly) return row['Difference'] === false
        return true
      })
    : []

  // Stat card colors
  const pct = result?.stats.match_percentage ?? 0
  const pctColor = pct >= 95 ? '#00ab63' : pct >= 75 ? '#ffa500' : '#ff4444'
  const unmatched = result ? result.stats.total_records - result.stats.matched_records : 0

  const canRun =
    bothLoaded &&
    matchKeysFirst.length > 0 &&
    matchKeysSecond.length > 0 &&
    compareColFirst &&
    compareColSecond &&
    !isRunning

  return (
    <div>
      <Header title="Reconciliation" />
      <div className="page-body">
        <div className="two-col">
          {/* ── Left: Upload Files ── */}
          <div>
            <h3>Upload Files</h3>

            {/* First file */}
            <div
              className="file-upload-area"
              onClick={() => firstInputRef.current?.click()}
            >
              <input
                ref={firstInputRef}
                type="file"
                accept=".xlsx,.xls"
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (f) handleFirstFile(f)
                }}
              />
              <label>
                {firstStatus === 'idle'
                  ? 'Select first file'
                  : firstStatus === 'loading'
                    ? 'Reading columns…'
                    : firstName}
              </label>
              <span className="upload-hint">.xlsx or .xls</span>
            </div>
            {firstStatus === 'success' && (
              <div className="msg-success">✓ Loaded: {firstName}</div>
            )}
            {firstStatus === 'error' && (
              <div className="msg-error">Error reading first file columns.</div>
            )}

            {/* Second file */}
            <div
              className="file-upload-area"
              onClick={() => secondInputRef.current?.click()}
            >
              <input
                ref={secondInputRef}
                type="file"
                accept=".xlsx,.xls"
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (f) handleSecondFile(f)
                }}
              />
              <label>
                {secondStatus === 'idle'
                  ? 'Select second file'
                  : secondStatus === 'loading'
                    ? 'Reading columns…'
                    : secondName}
              </label>
              <span className="upload-hint">.xlsx or .xls</span>
            </div>
            {secondStatus === 'success' && (
              <div className="msg-success">✓ Loaded: {secondName}</div>
            )}
            {secondStatus === 'error' && (
              <div className="msg-error">Error reading second file columns.</div>
            )}
          </div>

          {/* ── Right: Configure ── */}
          <div>
            <h3>Configure</h3>
            {!bothLoaded ? (
              <div className="msg-info">Upload both files to configure the comparison</div>
            ) : (
              <>
                {/* Load Profile */}
                {Object.keys(profiles).length > 0 && (
                  <div className="field">
                    <span className="field-label">Load Profile</span>
                    <div className="input-btn-row">
                      <select
                        value={selectedProfile}
                        onChange={(e) => setSelectedProfile(e.target.value)}
                      >
                        <option value="">Select a saved profile</option>
                        {Object.keys(profiles).map((name) => (
                          <option key={name} value={name}>
                            {name}
                          </option>
                        ))}
                      </select>
                      <button
                        className="btn-small"
                        onClick={handleLoadProfile}
                        disabled={!selectedProfile}
                      >
                        Load
                      </button>
                    </div>
                  </div>
                )}

                {/* Match keys first */}
                <div className="field">
                  <span className="field-label">Match keys (first file)</span>
                  <Select
                    isMulti
                    options={toOptions(firstCols)}
                    value={toMultiValue(matchKeysFirst)}
                    onChange={(opts) =>
                      setMatchKeysFirst((opts ?? []).map((o) => o.value))
                    }
                    placeholder="Select one or more columns"
                    styles={selectStyles}
                    menuPortalTarget={document.body}
                  />
                </div>

                {/* Match keys second */}
                <div className="field">
                  <span className="field-label">Match keys (second file)</span>
                  <Select
                    isMulti
                    options={toOptions(secondCols)}
                    value={toMultiValue(matchKeysSecond)}
                    onChange={(opts) =>
                      setMatchKeysSecond((opts ?? []).map((o) => o.value))
                    }
                    placeholder="Select one or more columns"
                    styles={selectStyles}
                    menuPortalTarget={document.body}
                  />
                </div>

                {/* Compare col first */}
                <div className="field">
                  <span className="field-label">Compare column (first file)</span>
                  <Select
                    options={toOptions(firstCols)}
                    value={toSingleValue(compareColFirst)}
                    onChange={(opt) => opt && setCompareColFirst(opt.value)}
                    styles={selectStyles}
                    menuPortalTarget={document.body}
                  />
                </div>

                {/* Compare col second */}
                <div className="field">
                  <span className="field-label">Compare column (second file)</span>
                  <Select
                    options={toOptions(secondCols)}
                    value={toSingleValue(compareColSecond)}
                    onChange={(opt) => opt && setCompareColSecond(opt.value)}
                    styles={selectStyles}
                    menuPortalTarget={document.body}
                  />
                </div>

                {/* Tolerance type */}
                <div className="field">
                  <label>Tolerance type</label>
                  <select
                    value={toleranceType}
                    onChange={(e) => setToleranceType(e.target.value)}
                  >
                    <option value="None">None</option>
                    <option value="Dollar ($)">Dollar ($)</option>
                    <option value="Percentage (%)">Percentage (%)</option>
                  </select>
                </div>

                {/* Tolerance value */}
                {toleranceType !== 'None' && (
                  <div className="field">
                    <label>
                      Tolerance value{' '}
                      {toleranceType === 'Percentage (%)' ? '(%)' : '($)'}
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={toleranceType === 'Percentage (%)' ? 100 : undefined}
                      step={toleranceType === 'Percentage (%)' ? 0.1 : 0.01}
                      value={toleranceValue}
                      onChange={(e) => setToleranceValue(parseFloat(e.target.value) || 0)}
                    />
                  </div>
                )}

                {runError && <div className="msg-error">{runError}</div>}

                <button
                  className="btn-primary"
                  onClick={handleRun}
                  disabled={!canRun}
                  style={{ marginBottom: '0.5rem' }}
                >
                  {isRunning ? (
                    <>
                      <span className="spinner" />
                      Running…
                    </>
                  ) : (
                    'Run Comparison'
                  )}
                </button>

                <hr className="divider" />

                {/* Save profile */}
                <div className="field">
                  <span className="field-label">Save Configuration Profile</span>
                  <div className="input-btn-row">
                    <input
                      type="text"
                      value={profileName}
                      onChange={(e) => setProfileName(e.target.value)}
                      placeholder="e.g. Monthly Vendor Reconciliation"
                    />
                    <button className="btn-small" onClick={handleSaveProfile}>
                      Save
                    </button>
                  </div>
                </div>
                {saveMsg && <div className="msg-success">{saveMsg}</div>}
                {saveError && <div className="msg-error">{saveError}</div>}
              </>
            )}
          </div>
        </div>

        {/* ── Results ── */}
        {result && (
          <div className="results-section">
            <h3>Results</h3>

            {/* Stat cards */}
            <div className="stat-cards">
              <div className="stat-card" style={{ borderTopColor: '#d8d7ee' }}>
                <div className="stat-label">Total Records</div>
                <div className="stat-value" style={{ color: '#ffffff' }}>
                  {result.stats.total_records.toLocaleString()}
                </div>
              </div>
              <div className="stat-card" style={{ borderTopColor: '#00ab63' }}>
                <div className="stat-label">Matched</div>
                <div className="stat-value" style={{ color: '#00ab63' }}>
                  {result.stats.matched_records.toLocaleString()}
                </div>
              </div>
              <div className="stat-card" style={{ borderTopColor: '#ff4444' }}>
                <div className="stat-label">Unmatched</div>
                <div className="stat-value" style={{ color: '#ff4444' }}>
                  {unmatched.toLocaleString()}
                </div>
              </div>
              <div className="stat-card" style={{ borderTopColor: pctColor }}>
                <div className="stat-label">Match Rate</div>
                <div className="stat-value" style={{ color: pctColor }}>
                  {pct.toFixed(1)}%
                </div>
              </div>
            </div>

            <hr className="divider" />

            {/* Filters */}
            <div className="filter-row">
              <label>
                <input
                  type="checkbox"
                  checked={showDiffsOnly}
                  onChange={(e) => {
                    setShowDiffsOnly(e.target.checked)
                    if (e.target.checked) setShowMatchesOnly(false)
                  }}
                />
                Show differences only
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={showMatchesOnly}
                  onChange={(e) => {
                    setShowMatchesOnly(e.target.checked)
                    if (e.target.checked) setShowDiffsOnly(false)
                  }}
                />
                Show matches only
              </label>
            </div>

            <p className="preview-label">
              Preview Results ({filteredRows.length} rows)
            </p>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    {result.columns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredRows.map((row, i) => (
                    <tr
                      key={i}
                      className={row['Difference'] === true ? 'row-diff' : ''}
                    >
                      {result.columns.map((col) => (
                        <td key={col}>{formatCell(row[col])}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <a
              href={getDownloadUrl(result.download_token)}
              download="reconciliation_results.xlsx"
            >
              <button className="btn-primary">Download Results</button>
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
