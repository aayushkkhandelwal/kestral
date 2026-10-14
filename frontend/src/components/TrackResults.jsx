import React from 'react';
import { Eye, Clock, Sparkles, UserCheck, ShieldAlert } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function TrackResults({ tracks = [], onSelectTrack }) {
  if (!tracks || tracks.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '48px 24px', textAlign: 'center' }}>
        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: 'rgba(255, 255, 255, 0.03)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 16px',
          color: 'var(--text-muted)'
        }}>
          <UserCheck size={28} />
        </div>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
          No Tracked Subjects Yet
        </h3>
        <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', maxWidth: '420px', margin: '0 auto' }}>
          Run video analysis to isolate tracked individuals, compute facial fidelity, and view extracted evidence.
        </p>
      </div>
    );
  }

  const getGradeBadge = (grade, score, hasRealFace) => {
    if (!hasRealFace) {
      return <span className="badge badge-fair">⚠️ Face Not Visible</span>;
    }
    switch (grade) {
      case 'EXCELLENT':
        return <span className="badge badge-excellent">★ {score}% Face</span>;
      case 'GOOD':
        return <span className="badge badge-good">✓ {score}% Face</span>;
      case 'FAIR':
        return <span className="badge badge-fair">~ {score}% Face</span>;
      default:
        return <span className="badge badge-poor">! {score}% Low</span>;
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Tracked Person Evidence ({tracks.length})
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Ranked by biometric clarity score & optimal identification frame
          </p>
        </div>

        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          Click card to inspect biometric metrics
        </span>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: '20px'
      }}>
        {tracks.map((track) => {
          const faceUrl = `${API_BASE_URL}${track.face_image_url}`;
          const quality = track.quality || {};

          return (
            <div
              key={track.track_id}
              className="glass-panel"
              onClick={() => onSelectTrack(track)}
              style={{
                cursor: 'pointer',
                overflow: 'hidden',
                transition: 'transform 0.2s ease, border-color 0.2s ease',
                display: 'flex',
                flexDirection: 'column'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-3px)';
                e.currentTarget.style.borderColor = 'var(--border-focus)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = 'var(--border-subtle)';
              }}
            >
              {/* Evidence Crop Thumbnail */}
              <div style={{
                position: 'relative',
                height: '180px',
                backgroundColor: '#05070c',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden'
              }}>
                <img
                  src={faceUrl}
                  alt={`Subject #${track.track_id}`}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain',
                    transition: 'transform 0.3s ease'
                  }}
                  onError={(e) => {
                    // Fallback thumbnail if image hasn't finished writing
                    e.target.style.display = 'none';
                  }}
                />

                {/* Score badge overlay */}
                <div style={{ position: 'absolute', top: '10px', right: '10px' }}>
                  {getGradeBadge(quality.grade, track.best_score, track.has_real_face)}
                </div>

                {/* ID badge overlay */}
                <div style={{
                  position: 'absolute',
                  bottom: '10px',
                  left: '10px',
                  backgroundColor: 'rgba(0, 0, 0, 0.75)',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: '#fff'
                }}>
                  ID #{track.track_id}
                </div>
              </div>

              {/* Card Body */}
              <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px', flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    Subject #{track.track_id}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <Clock size={13} />
                    <span>{track.duration_seconds}s span</span>
                  </div>
                </div>

                {/* Metrics Breakdown Bar */}
                <div style={{
                  backgroundColor: 'var(--bg-input)',
                  padding: '10px',
                  borderRadius: 'var(--radius-sm)',
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '8px',
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-mono)'
                }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Laplacian: </span>
                    <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{quality.sharpness ?? 'N/A'}</span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Resolution: </span>
                    <span style={{ color: 'var(--text-primary)' }}>{quality.crop_width}x{quality.crop_height}</span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Best Frame: </span>
                    <span style={{ color: 'var(--text-primary)' }}>#{track.best_frame_idx}</span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Timestamp: </span>
                    <span style={{ color: 'var(--accent-emerald)' }}>{track.best_timestamp}s</span>
                  </div>
                </div>

                {/* Inspect Action */}
                <button
                  className="btn btn-secondary"
                  style={{
                    width: '100%',
                    padding: '8px',
                    fontSize: '0.8rem',
                    marginTop: 'auto'
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectTrack(track);
                  }}
                >
                  <Eye size={14} />
                  <span>Inspect Evidence & Metrics</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
