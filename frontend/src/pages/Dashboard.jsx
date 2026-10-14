import React from 'react';
import { 
  Play, 
  ArrowRight, 
  Clock, 
  CheckCircle, 
  Layers, 
  ShieldCheck, 
  Video, 
  Cpu, 
  Film,
  Camera
} from 'lucide-react';
import StatsCards from '../components/StatsCards';

export default function Dashboard({ 
  stats, 
  history = [], 
  onNavigateToAnalysis, 
  onNavigateToEvidence,
  onNavigateToLiveCamera
}) {
  return (
    <div>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
            Mission Control & Analytics
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Real-time biometric evidence extraction, subject re-identification & surveillance feed processing
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {onNavigateToLiveCamera && (
            <button
              onClick={onNavigateToLiveCamera}
              className="btn"
              style={{
                padding: '10px 18px',
                fontSize: '0.875rem',
                backgroundColor: 'rgba(6, 182, 212, 0.12)',
                border: '1px solid rgba(6, 182, 212, 0.35)',
                color: 'var(--accent-cyan)',
                fontWeight: 600
              }}
            >
              <Camera size={16} />
              <span>Launch Live Camera</span>
            </button>
          )}

          <button
            onClick={onNavigateToAnalysis}
            className="btn btn-primary"
            style={{ padding: '10px 20px', fontSize: '0.875rem' }}
          >
            <Play size={16} fill="currentColor" />
            <span>New Video Analysis</span>
          </button>
        </div>
      </div>

      {/* Aggregate KPI Stats Cards */}
      <StatsCards stats={stats} />

      {/* Two Column Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1.2fr', gap: '24px', marginBottom: '32px' }}>
        {/* Recent Analyses Table */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Film size={20} color="var(--accent-cyan)" />
              <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Recent Surveillance Feeds
              </h2>
            </div>
            <button
              onClick={onNavigateToEvidence}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--accent-cyan)',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <span>View All Evidence</span>
              <ArrowRight size={14} />
            </button>
          </div>

          {history.length === 0 ? (
            <div style={{ padding: '36px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No videos processed yet. Click <strong>"New Video Analysis"</strong> to upload your first surveillance stream.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.825rem' }}>
                <thead>
                  <tr style={{ color: 'var(--text-muted)', textAlign: 'left', borderBottom: '1px solid var(--border-subtle)' }}>
                    <th style={{ padding: '10px 8px' }}>TASK ID</th>
                    <th style={{ padding: '10px 8px' }}>RESOLUTION</th>
                    <th style={{ padding: '10px 8px' }}>DURATION</th>
                    <th style={{ padding: '10px 8px' }}>SUBJECTS</th>
                    <th style={{ padding: '10px 8px' }}>AVG QUALITY</th>
                  </tr>
                </thead>
                <tbody>
                  {history.slice(0, 5).map((item) => (
                    <tr
                      key={item.task_id}
                      style={{ borderBottom: '1px solid var(--border-subtle)' }}
                    >
                      <td style={{ padding: '12px 8px', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                        #{item.task_id}
                      </td>
                      <td style={{ padding: '12px 8px', color: 'var(--text-primary)' }}>
                        {item.metadata?.resolution || '1920x1080'}
                      </td>
                      <td style={{ padding: '12px 8px', color: 'var(--text-secondary)' }}>
                        {item.metadata?.duration_seconds || '0'}s
                      </td>
                      <td style={{ padding: '12px 8px', color: 'var(--text-primary)', fontWeight: 600 }}>
                        {item.summary?.unique_persons_tracked || 0} Persons
                      </td>
                      <td style={{ padding: '12px 8px' }}>
                        <span className="badge badge-good">
                          {item.summary?.average_best_quality || 75}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pipeline Architecture & Operational Health */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Cpu size={20} color="var(--accent-indigo)" />
            <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Vision Pipeline Health
            </h2>
          </div>

          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Fully automated asynchronous multi-stage processing stack running on FastAPI.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '6px' }}>
            <div style={{
              padding: '12px 14px',
              backgroundColor: 'var(--bg-input)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <div>
                <p style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>YOLO Tracking Stage</p>
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Class 0 Person Filtering + ByteTrack</p>
              </div>
              <span className="badge badge-excellent">Active</span>
            </div>

            <div style={{
              padding: '12px 14px',
              backgroundColor: 'var(--bg-input)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <div>
                <p style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>Biometric Cascade Stage</p>
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>OpenCV Frontal/Profile Facial Detectors</p>
              </div>
              <span className="badge badge-excellent">Active</span>
            </div>

            <div style={{
              padding: '12px 14px',
              backgroundColor: 'var(--bg-input)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <div>
                <p style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>Best-Frame Arbiter</p>
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Laplacian Variance & Exposure Normalizer</p>
              </div>
              <span className="badge badge-excellent">Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
