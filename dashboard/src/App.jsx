import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [queue, setQueue] = useState([])
  const [contracts, setContracts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Expert usage: real data fetching from FastAPI backend
    fetch('http://localhost:8000/hitl/queue')
      .then(res => res.json())
      .then(data => setQueue(data.items || []))
      .catch(e => console.error("HITL Error:", e))

    fetch('http://localhost:8000/contracts')
      .then(res => res.json())
      .then(data => {
          setContracts(data.contracts || [])
          setLoading(false)
      })
      .catch(e => console.error("Contract Error:", e))
  }, [])

  const resolveItem = (id, status) => {
    fetch(`http://localhost:8000/hitl/${id}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    }).then(() => {
        setQueue(prev => prev.filter(i => i.id !== id))
    })
  }

  return (
    <div className="app-container">
      <header>
        <h1>⚖️ Legal Contract Agent</h1>
        <div className="status-badge">
            <span className="tag tag-success">Active Pipeline</span>
        </div>
      </header>

      <main className="grid">
        <section className="hitl-queue glass-card">
          <h2>🔔 HITL Approval Queue</h2>
          {queue.length === 0 ? (
            <p className="placeholder">All clear. No pending blocker items.</p>
          ) : (
            <div className="queue-list">
              {queue.map(item => (
                <div key={item.id} className="queue-item">
                  <div className="item-info">
                    <span className="tag tag-danger">{item.stage.toUpperCase()}</span>
                    <strong>{item.reason}</strong>
                    <p>{item.item_type}: {item.contract_id}</p>
                  </div>
                  <div className="item-actions">
                    <button onClick={() => resolveItem(item.id, 'approved')}>Approve</button>
                    <button className="secondary" onClick={() => resolveItem(item.id, 'rejected')}>Reject</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="contracts-summary glass-card">
          <h2>🚀 Ready for Action</h2>
          <div className="contract-list">
            {contracts.map(c => (
              <div key={c.id} className="contract-item">
                <div className="info">
                    <strong>{c.source_filename}</strong>
                    <p style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>{c.contract_type} • {c.status}</p>
                </div>
                <div style={{marginTop: '1rem'}}>
                    <a href={`http://localhost:8000/contracts/${c.id}/download/redline`} download>
                        <button style={{width: '100%'}}>Download Redline</button>
                    </a>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="disclaimer-footer">
        <p>NOT LEGAL ADVICE — For informational and drafting purposes only. Review by licensed counsel required. All AI outputs are grounded in source documentation.</p>
      </footer>
    </div>
  )
}

export default App
