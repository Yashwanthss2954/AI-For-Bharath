import { useEffect, useMemo, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

async function fetchJson(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options)
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const message = payload.detail?.message || payload.detail || 'Request failed'
    throw new Error(typeof message === 'string' ? message : 'Request failed')
  }
  return payload
}

function App() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [reviewQueue, setReviewQueue] = useState([])
  const [decisionBusyKey, setDecisionBusyKey] = useState('')

  const [ubids, setUbids] = useState([])
  const [searchParams, setSearchParams] = useState({
    name: '',
    pincode: '',
    pan: '',
    gstin: '',
    source_record_id: '',
  })

  const [activityRows, setActivityRows] = useState([])

  const loadDashboard = async (params = null) => {
    setLoading(true)
    setError('')
    try {
      const query = new URLSearchParams()
      const currentParams = params || searchParams
      Object.entries(currentParams).forEach(([key, value]) => {
        if (value) query.set(key, value)
      })

      const [reviewPayload, ubidPayload, activityPayload] = await Promise.all([
        fetchJson('/review/queue?limit=20'),
        fetchJson(`/ubids/search${query.toString() ? `?${query.toString()}` : ''}`),
        fetchJson('/activity/status'),
      ])

      setReviewQueue(reviewPayload.items || [])
      setUbids(ubidPayload.items || [])
      setActivityRows(activityPayload.items || [])
    } catch (e) {
      setError(e.message || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboard()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const activityCounts = useMemo(() => {
    const counts = { Active: 0, Dormant: 0, Closed: 0 }
    activityRows.forEach((row) => {
      if (counts[row.status] !== undefined) counts[row.status] += 1
    })
    return counts
  }, [activityRows])

  const metrics = useMemo(() => {
    const total = ubids.length || 0
    const activePct = total ? ((activityCounts.Active / total) * 100).toFixed(1) : '0.0'
    return [
      {
        label: 'Businesses Unified',
        value: total.toLocaleString(),
        delta: 'From current UBID registry',
      },
      {
        label: 'Ambiguous Cases Routed',
        value: reviewQueue.length.toLocaleString(),
        delta: 'Pending reviewer action',
      },
      {
        label: 'Closed Entities',
        value: activityCounts.Closed.toLocaleString(),
        delta: 'Derived from activity events',
      },
      {
        label: 'Active Business Signals',
        value: `${activePct}%`,
        delta: 'Across linked UBIDs',
      },
    ]
  }, [activityCounts, reviewQueue.length, ubids.length])

  const intelFeed = useMemo(
    () => [
      `Active UBIDs currently tracked: ${activityCounts.Active}`,
      `Dormant UBIDs requiring targeted follow-up: ${activityCounts.Dormant}`,
      `Review queue in progress: ${reviewQueue.length} cases`,
    ],
    [activityCounts.Active, activityCounts.Dormant, reviewQueue.length],
  )

  const onSearchChange = (event) => {
    const { name, value } = event.target
    setSearchParams((prev) => ({ ...prev, [name]: value }))
  }

  const onSearchSubmit = async (event) => {
    event.preventDefault()
    await loadDashboard(searchParams)
  }

  const onSearchReset = async () => {
    const emptyParams = {
      name: '',
      pincode: '',
      pan: '',
      gstin: '',
      source_record_id: '',
    }
    setSearchParams(emptyParams)
    await loadDashboard(emptyParams)
  }

  const submitDecision = async (row, decision) => {
    const key = `${row.left_record_id}||${row.right_record_id}`
    setDecisionBusyKey(key)
    setError('')
    try {
      await fetchJson('/review/decision', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          left_record_id: row.left_record_id,
          right_record_id: row.right_record_id,
          decision,
          reviewer: 'ui-reviewer',
          notes: `Decision from dashboard: ${decision}`,
        }),
      })
      await loadDashboard()
    } catch (e) {
      setError(e.message || 'Failed to submit reviewer decision')
    } finally {
      setDecisionBusyKey('')
    }
  }

  return (
    <div className="page-shell">
      <div className="bg-orb orb-a" />
      <div className="bg-orb orb-b" />
      <div className="bg-grid" />

      <header className="topbar glass panel-reveal">
        <div className="brand-block">
          <span className="brand-emblem">KCI</span>
          <div>
            <p className="brand-kicker">Government of Karnataka</p>
            <h1>Unified Business Intelligence Command Center</h1>
          </div>
        </div>
        <button className="primary-btn" onClick={() => loadDashboard()}>
          Refresh Live Data
        </button>
      </header>

      {error && (
        <section className="glass panel-reveal error-banner">
          <p>{error}</p>
        </section>
      )}

      <section className="hero glass panel-reveal">
        <div>
          <p className="eyebrow">Theme 1: UBID + Active Business Intelligence</p>
          <h2>One identity spine. Explainable decisions. Real-time policy visibility.</h2>
          <p className="hero-copy">
            This dashboard unifies fragmented departmental records, attaches evidence-backed
            confidence scores, and classifies each UBID as Active, Dormant, or Closed with
            reversible governance workflows.
          </p>
        </div>
        <div className="hero-pillars">
          <article>
            <h3>Identity Resolution</h3>
            <p>Rules + ML scoring with strict false-merge protection.</p>
          </article>
          <article>
            <h3>Human Review</h3>
            <p>Ambiguous cases are surfaced, audited, and model-fed.</p>
          </article>
          <article>
            <h3>Activity Intelligence</h3>
            <p>Status inferred from renewals, inspections, filings, and usage.</p>
          </article>
        </div>
      </section>

      <section className="metric-grid">
        {metrics.map((metric, index) => (
          <article
            className="metric-card glass panel-reveal"
            key={metric.label}
            style={{ animationDelay: `${index * 90}ms` }}
          >
            <p>{metric.label}</p>
            <h3>{loading ? '...' : metric.value}</h3>
            <span>{metric.delta}</span>
          </article>
        ))}
      </section>

      <section className="glass panel-reveal search-card">
        <div className="section-head">
          <h3>UBID Search</h3>
          <span className="chip neutral">PAN / GSTIN / Name / Source ID</span>
        </div>
        <form className="search-grid" onSubmit={onSearchSubmit}>
          <input
            name="name"
            value={searchParams.name}
            onChange={onSearchChange}
            placeholder="Business Name"
          />
          <input
            name="pincode"
            value={searchParams.pincode}
            onChange={onSearchChange}
            placeholder="Pincode"
          />
          <input name="pan" value={searchParams.pan} onChange={onSearchChange} placeholder="PAN" />
          <input
            name="gstin"
            value={searchParams.gstin}
            onChange={onSearchChange}
            placeholder="GSTIN"
          />
          <input
            name="source_record_id"
            value={searchParams.source_record_id}
            onChange={onSearchChange}
            placeholder="Source Record ID"
          />
          <div className="form-actions">
            <button className="primary-btn" type="submit">
              Search
            </button>
            <button className="ghost-btn" type="button" onClick={onSearchReset}>
              Reset
            </button>
          </div>
        </form>
      </section>

      <section className="content-grid">
        <article className="glass panel-reveal review-card">
          <div className="section-head">
            <h3>Review Queue</h3>
            <span className="chip warning">{reviewQueue.length} Pending Cases</span>
          </div>
          <div className="table-wrap" style={{ maxHeight: '400px', overflowY: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Record Pair</th>
                  <th>Evidence</th>
                  <th>Confidence</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {reviewQueue.length === 0 && !loading && (
                  <tr>
                    <td colSpan="4">No pending review items.</td>
                  </tr>
                )}
                {reviewQueue.map((item) => {
                  const rowKey = `${item.left_record_id}||${item.right_record_id}`
                  const busy = decisionBusyKey === rowKey
                  return (
                    <tr key={rowKey}>
                      <td>{item.left_record_id} + {item.right_record_id}</td>
                      <td>{item.why}</td>
                      <td>{item.score}</td>
                      <td>
                        <div className="row-actions">
                          <button
                            className="chip-btn accept"
                            type="button"
                            disabled={busy}
                            onClick={() => submitDecision(item, 'merge')}
                          >
                            Merge
                          </button>
                          <button
                            className="chip-btn reject"
                            type="button"
                            disabled={busy}
                            onClick={() => submitDecision(item, 'reject')}
                          >
                            Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </article>

        <article className="glass panel-reveal intel-card">
          <div className="section-head">
            <h3>Policy Intelligence Feed</h3>
            <span className="chip neutral">Live Sandbox</span>
          </div>
          <ul>
            {intelFeed.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
          <div className="status-band">
            <div>
              <p>Active</p>
              <strong>{activityCounts.Active}</strong>
            </div>
            <div>
              <p>Dormant</p>
              <strong>{activityCounts.Dormant}</strong>
            </div>
            <div>
              <p>Closed</p>
              <strong>{activityCounts.Closed}</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="glass panel-reveal ubid-results">
        <div className="section-head">
          <h3>UBID Search Results</h3>
          <span className="chip neutral">{ubids.length} matched entities</span>
        </div>
        <div className="table-wrap" style={{ maxHeight: '500px', overflowY: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>UBID</th>
                <th>Business</th>
                <th>Pincode</th>
                <th>Status</th>
                <th>Anchors</th>
              </tr>
            </thead>
            <tbody>
              {ubids.length === 0 && !loading && (
                <tr>
                  <td colSpan="5">No UBIDs found for current filters.</td>
                </tr>
              )}
              {ubids.map((row) => (
                <tr key={row.ubid}>
                  <td>{row.ubid}</td>
                  <td>{row.business_name}</td>
                  <td>{row.pincode}</td>
                  <td>{row.status || 'Unknown'}</td>
                  <td>
                    <div className="anchor-lines">
                      <span>PAN: {row.anchor_pan || '-'}</span>
                      <span>GSTIN: {row.anchor_gstin || '-'}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

export default App
