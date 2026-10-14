import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  ShieldCheck, 
  UserCheck, 
  Clock, 
  RotateCw, 
  FileText, 
  Lock, 
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function AuditLog({ currentUser, onSwitchUser }) {
  const [logs, setLogs] = useState([]);
  const [usersInfo, setUsersInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAuditData = async () => {
    try {
      const [auditRes, usersRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/audit`, { headers: { 'X-User': currentUser } }),
        axios.get(`${API_BASE_URL}/api/audit/users`, { headers: { 'X-User': currentUser } })
      ]);
      setLogs(auditRes.data || []);
      setUsersInfo(usersRes.data || null);
    } catch (err) {
      console.error('Failed to load audit data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditData();
  }, [currentUser]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.03em' }}>
            System Audit Trail & Identity Governance
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Tamper-evident log of all biometric queries, transaction correlations, video uploads, and ROI configurations
          </p>
        </div>

        {/* User Switcher Card */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '8px 14px',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid var(--border-subtle)'
        }}>
          <Lock size={16} color="var(--accent-cyan)" />
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Demo Identity:</span>
          <select
            value={currentUser}
            onChange={e => onSwitchUser(e.target.value)}
            style={{
              padding: '6px 10px',
              borderRadius: '6px',
              backgroundColor: '#070b14',
              border: '1px solid var(--border-subtle)',
              color: '#fff',
              fontSize: '0.8rem',
              fontWeight: 700
            }}
          >
            <option value="investigator">Special Agent Roy (Investigator)</option>
            <option value="admin">Director Sarah Connor (Admin)</option>
          </select>
        </div>
      </div>

      {/* Demo Grade Auth Warning */}
      <div style={{
        padding: '12px 18px',
        borderRadius: 'var(--radius-md)',
        backgroundColor: 'rgba(6, 182, 212, 0.1)',
        border: '1px solid rgba(6, 182, 212, 0.25)',
        fontSize: '0.8rem',
        color: 'var(--accent-cyan)'
      }}>
        ℹ️ <strong>DEMO-GRADE ACCESS CONTROL:</strong> Authenticated via simulated HTTP header identity verification (<code>X-User: {currentUser}</code>). Production deployments integrate enterprise SAML/OAuth2 and hardware security tokens.
      </div>

      {/* Audit Log Table */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FileText size={20} color="var(--accent-cyan)" />
            <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
              Chronological Audit Trail ({logs.length})
            </h2>
          </div>
          <button
            onClick={fetchAuditData}
            className="btn btn-secondary"
            style={{ padding: '6px 12px', fontSize: '0.75rem' }}
          >
            <RotateCw size={13} />
            <span>Refresh Logs</span>
          </button>
        </div>

        {logs.length === 0 ? (
          <div style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No audit events recorded yet. Perform actions like uploading video, creating transactions, or searching faces to record events.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  <th style={{ padding: '10px 14px' }}>ID</th>
                  <th style={{ padding: '10px 14px' }}>TIMESTAMP (UTC)</th>
                  <th style={{ padding: '10px 14px' }}>USER</th>
                  <th style={{ padding: '10px 14px' }}>ROLE</th>
                  <th style={{ padding: '10px 14px' }}>ACTION</th>
                  <th style={{ padding: '10px 14px' }}>AUDIT DETAILS</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((l) => (
                  <tr
                    key={l.id}
                    style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}
                  >
                    <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      #{l.id}
                    </td>
                    <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)', color: '#fff' }}>
                      {l.ts?.replace('T', ' ').slice(0, 19)}
                    </td>
                    <td style={{ padding: '12px 14px', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                      {l.user}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        backgroundColor: l.role === 'admin' ? 'rgba(244, 63, 94, 0.15)' : 'rgba(6, 182, 212, 0.15)',
                        color: l.role === 'admin' ? '#fb7185' : 'var(--accent-cyan)',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        textTransform: 'uppercase'
                      }}>
                        {l.role}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', fontWeight: 700, color: '#fff' }}>
                      {l.action}
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--text-secondary)' }}>
                      {l.detail}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
