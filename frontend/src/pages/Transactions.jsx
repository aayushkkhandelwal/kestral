import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  CreditCard, 
  MapPin, 
  AlertTriangle, 
  CheckCircle, 
  RotateCw, 
  Plus, 
  ShieldAlert, 
  Layers, 
  Trash2, 
  Save, 
  Crosshair, 
  ArrowRight,
  Clock
} from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function Transactions({ onNavigateToEvidence }) {
  const [transactions, setTransactions] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState('');
  const [atmId, setAtmId] = useState('ATM_CENTRAL');
  const [txnId, setTxnId] = useState('');
  const [startSec, setStartSec] = useState('5.0');
  const [endSec, setEndSec] = useState('18.0');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null);

  // ROI Editor state
  const [roiPolygon, setRoiPolygon] = useState([]);
  const [thumbnailUrl, setThumbnailUrl] = useState('');
  const [savingRoi, setSavingRoi] = useState(false);
  const imgRef = useRef(null);

  const fetchTransactions = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/transactions`);
      setTransactions(res.data || []);
    } catch (err) {
      console.error('Error fetching transactions:', err);
    }
  };

  const fetchHistoryAndRoi = async () => {
    try {
      const histRes = await axios.get(`${API_BASE_URL}/api/history`);
      const hData = histRes.data || [];
      setHistory(hData);
      if (hData.length > 0 && !selectedTask) {
        setSelectedTask(hData[0].task_id);
      }

      // Fetch ROI for active ATM
      const roiRes = await axios.get(`${API_BASE_URL}/api/rois/${atmId}`);
      if (roiRes.data?.polygon) {
        setRoiPolygon(roiRes.data.polygon);
      }
    } catch (err) {
      console.error('Error fetching history/ROI:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
    fetchHistoryAndRoi();
  }, []);

  // Update thumbnail when selected task changes
  useEffect(() => {
    if (!selectedTask) return;
    const taskObj = history.find(h => h.task_id === selectedTask);
    if (taskObj?.metadata?.thumbnail_url) {
      setThumbnailUrl(`${API_BASE_URL}${taskObj.metadata.thumbnail_url}`);
    } else {
      setThumbnailUrl(`${API_BASE_URL}/results/${selectedTask}/thumbnail.jpg`);
    }
  }, [selectedTask, history]);

  // Generate default transaction ID
  useEffect(() => {
    setTxnId(`TXN-${Math.floor(1000 + Math.random() * 9000)}`);
  }, []);

  const handleCreateTransaction = async (e) => {
    e.preventDefault();
    if (!selectedTask || !atmId || !txnId) {
      setMessage({ type: 'error', text: 'Please fill in all transaction fields' });
      return;
    }

    setSubmitting(true);
    setMessage(null);
    try {
      const res = await axios.post(`${API_BASE_URL}/api/transactions`, {
        txn_id: txnId,
        atm_id: atmId,
        task_id: selectedTask,
        start_s: parseFloat(startSec),
        end_s: parseFloat(endSec)
      });
      setMessage({ type: 'success', text: `Transaction ${txnId} linked to Track #${res.data.track_id ?? 'None'}` });
      setTxnId(`TXN-${Math.floor(1000 + Math.random() * 9000)}`);
      fetchTransactions();
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to link transaction' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleRelink = async (id) => {
    try {
      const res = await axios.post(`${API_BASE_URL}/api/transactions/${id}/relink`);
      setMessage({ type: 'success', text: `Relinked ${id}: Track #${res.data.track_id} (conf=${res.data.confidence})` });
      fetchTransactions();
    } catch (err) {
      setMessage({ type: 'error', text: 'Relinking failed' });
    }
  };

  // Click on thumbnail to append polygon vertex
  const handleCanvasClick = (e) => {
    if (!imgRef.current) return;
    const rect = imgRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Scale to reference 1280x720 video coordinates
    const scaleX = 1280.0 / rect.width;
    const scaleY = 720.0 / rect.height;

    const frameX = Math.round(clickX * scaleX);
    const frameY = Math.round(clickY * scaleY);

    setRoiPolygon(prev => [...prev, [frameX, frameY]]);
  };

  const handleSaveRoi = async () => {
    if (roiPolygon.length < 3) {
      alert('ATM interaction zone requires at least 3 points to form a polygon.');
      return;
    }
    setSavingRoi(true);
    try {
      await axios.put(`${API_BASE_URL}/api/rois/${atmId}`, {
        polygon: roiPolygon,
        frame_width: 1280,
        frame_height: 720
      });
      alert(`ATM zone polygon saved for ${atmId}`);
    } catch (err) {
      alert('Failed to save ROI polygon');
    } finally {
      setSavingRoi(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.03em' }}>
          ATM Transaction Linking & Zone Geometry
        </h1>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          Spatiotemporal dwell association between bank transaction records and suspect CCTV tracking trajectories
        </p>
      </div>

      {message && (
        <div style={{
          padding: '12px 18px',
          borderRadius: 'var(--radius-md)',
          backgroundColor: message.type === 'error' ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
          border: `1px solid ${message.type === 'error' ? 'rgba(244, 63, 94, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
          color: message.type === 'error' ? '#fb7185' : '#34d399',
          fontSize: '0.85rem'
        }}>
          {message.text}
        </div>
      )}

      {/* Grid: Transaction Form & Interactive ROI Zone Drawer */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1.3fr', gap: '24px' }}>
        {/* Left: Register Transaction Form */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
            <CreditCard size={20} color="var(--accent-cyan)" />
            <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
              Link New ATM Withdrawal
            </h2>
          </div>

          <form onSubmit={handleCreateTransaction} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Transaction ID
              </label>
              <input
                type="text"
                value={txnId}
                onChange={e => setTxnId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'rgba(0,0,0,0.3)',
                  border: '1px solid var(--border-subtle)',
                  color: '#fff',
                  fontFamily: 'var(--font-mono)'
                }}
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                ATM Terminal ID
              </label>
              <input
                type="text"
                value={atmId}
                onChange={e => setAtmId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'rgba(0,0,0,0.3)',
                  border: '1px solid var(--border-subtle)',
                  color: '#fff',
                  fontFamily: 'var(--font-mono)'
                }}
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Associated Video Feed Task
              </label>
              <select
                value={selectedTask}
                onChange={e => setSelectedTask(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: '#070b14',
                  border: '1px solid var(--border-subtle)',
                  color: '#fff'
                }}
                required
              >
                {history.length === 0 && <option value="">No processed video feeds available</option>}
                {history.map(h => (
                  <option key={h.task_id} value={h.task_id}>
                    Task {h.task_id} ({h.summary?.unique_persons_tracked ?? 0} tracks, {h.metadata?.duration_seconds ?? 0}s)
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Start Window (Sec)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={startSec}
                  onChange={e => setStartSec(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'rgba(0,0,0,0.3)',
                    border: '1px solid var(--border-subtle)',
                    color: '#fff',
                    fontFamily: 'var(--font-mono)'
                  }}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  End Window (Sec)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={endSec}
                  onChange={e => setEndSec(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'rgba(0,0,0,0.3)',
                    border: '1px solid var(--border-subtle)',
                    color: '#fff',
                    fontFamily: 'var(--font-mono)'
                  }}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="btn btn-primary"
              style={{ marginTop: '8px', padding: '12px' }}
            >
              <Plus size={16} />
              <span>{submitting ? 'Evaluating Linking...' : 'Correlate & Link Transaction'}</span>
            </button>
          </form>
        </div>

        {/* Right: Interactive ATM Surveillance Zone Canvas */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Crosshair size={20} color="var(--accent-emerald)" />
              <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
                ATM Zone Polygon: {atmId}
              </h2>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                onClick={() => setRoiPolygon([])}
                className="btn btn-secondary"
                style={{ padding: '6px 10px', fontSize: '0.75rem' }}
                title="Clear polygon vertices"
              >
                <Trash2 size={13} />
                <span>Reset</span>
              </button>
              <button
                type="button"
                onClick={handleSaveRoi}
                disabled={savingRoi}
                className="btn"
                style={{
                  padding: '6px 12px',
                  fontSize: '0.75rem',
                  backgroundColor: 'var(--accent-emerald)',
                  color: '#000',
                  fontWeight: 700
                }}
              >
                <Save size={13} />
                <span>{savingRoi ? 'Saving...' : 'Save Zone'}</span>
              </button>
            </div>
          </div>

          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Click anywhere on the surveillance frame below to define vertex coordinates for the ATM withdrawal interaction zone.
          </p>

          <div
            style={{
              position: 'relative',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
              backgroundColor: '#000',
              border: '1px solid var(--border-subtle)',
              aspectRatio: '16/9',
              cursor: 'crosshair'
            }}
            onClick={handleCanvasClick}
          >
            {thumbnailUrl ? (
              <img
                ref={imgRef}
                src={thumbnailUrl}
                alt="ATM Surveillance Reference Frame"
                style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
              />
            ) : (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                Select a video task to load camera preview
              </div>
            )}

            {/* SVG Polygon Overlay */}
            <svg
              style={{
                position: 'absolute',
                inset: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none'
              }}
              viewBox="0 0 1280 720"
            >
              {roiPolygon.length >= 3 && (
                <polygon
                  points={roiPolygon.map(p => `${p[0]},${p[1]}`).join(' ')}
                  fill="rgba(16, 185, 129, 0.25)"
                  stroke="#10b981"
                  strokeWidth="3"
                  strokeDasharray="6,4"
                />
              )}
              {roiPolygon.map((p, idx) => (
                <g key={idx}>
                  <circle cx={p[0]} cy={p[1]} r="7" fill="#10b981" stroke="#fff" strokeWidth="2" />
                  <text x={p[0] + 9} y={p[1] + 4} fill="#fff" fontSize="16" fontWeight="bold">
                    #{idx + 1}
                  </text>
                </g>
              ))}
            </svg>
          </div>

          <div style={{ marginTop: '10px', fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Vertices: {roiPolygon.length} {roiPolygon.length >= 3 ? '(Active Enclosed Polygon)' : '(Need 3+ points)'}
          </div>
        </div>
      </div>

      {/* Transactions History Table */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Layers size={20} color="var(--accent-indigo)" />
            <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
              Linked Transaction Records ({transactions.length})
            </h2>
          </div>
          <button
            onClick={fetchTransactions}
            className="btn btn-secondary"
            style={{ padding: '6px 12px', fontSize: '0.75rem' }}
          >
            <RotateCw size={13} />
            <span>Refresh</span>
          </button>
        </div>

        {transactions.length === 0 ? (
          <div style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No ATM cash withdrawal transactions recorded yet. Create a transaction using the form above.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  <th style={{ padding: '10px 14px' }}>TXN ID</th>
                  <th style={{ padding: '10px 14px' }}>ATM</th>
                  <th style={{ padding: '10px 14px' }}>TIME WINDOW</th>
                  <th style={{ padding: '10px 14px' }}>LINKED PERSON</th>
                  <th style={{ padding: '10px 14px' }}>CONFIDENCE</th>
                  <th style={{ padding: '10px 14px' }}>STATUS</th>
                  <th style={{ padding: '10px 14px' }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((t) => {
                  const hasLink = t.track_id !== null && t.track_id !== undefined;
                  const isAmbiguous = t.ambiguous;
                  return (
                    <tr
                      key={t.txn_id}
                      style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                        backgroundColor: isAmbiguous ? 'rgba(245, 158, 11, 0.05)' : 'transparent'
                      }}
                    >
                      <td style={{ padding: '12px 14px', fontWeight: 700, color: '#fff', fontFamily: 'var(--font-mono)' }}>
                        {t.txn_id}
                      </td>
                      <td style={{ padding: '12px 14px', color: 'var(--text-secondary)' }}>
                        {t.atm_id}
                      </td>
                      <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        {t.start_s}s - {t.end_s}s ({Math.round(t.end_s - t.start_s)}s)
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        {hasLink ? (
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            color: 'var(--accent-cyan)',
                            fontWeight: 700
                          }}>
                            Track #{t.track_id}
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>No Subject in Zone</span>
                        )}
                      </td>
                      <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)' }}>
                        {hasLink ? `${Math.round(t.confidence * 100)}%` : '0%'}
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        {isAmbiguous ? (
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            backgroundColor: 'rgba(245, 158, 11, 0.15)',
                            color: '#fbbf24',
                            border: '1px solid rgba(245, 158, 11, 0.3)',
                            fontSize: '0.72rem',
                            fontWeight: 700
                          }}>
                            <AlertTriangle size={12} />
                            AMBIGUOUS
                          </span>
                        ) : hasLink ? (
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            backgroundColor: 'rgba(16, 185, 129, 0.15)',
                            color: '#34d399',
                            border: '1px solid rgba(16, 185, 129, 0.3)',
                            fontSize: '0.72rem',
                            fontWeight: 700
                          }}>
                            <CheckCircle size={12} />
                            RESOLVED
                          </span>
                        ) : (
                          <span style={{
                            padding: '3px 8px',
                            borderRadius: '4px',
                            backgroundColor: 'rgba(255, 255, 255, 0.05)',
                            color: 'var(--text-muted)',
                            fontSize: '0.72rem'
                          }}>
                            UNLINKED
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <button
                          onClick={() => handleRelink(t.txn_id)}
                          className="btn btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                          title="Recompute spatiotemporal dwell association"
                        >
                          <RotateCw size={12} />
                          <span>Relink</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
