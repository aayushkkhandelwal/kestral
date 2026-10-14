import React, { useEffect } from 'react';
import { 
  X, 
  Download, 
  Sparkles, 
  ShieldCheck, 
  Maximize2, 
  Crosshair, 
  Clock, 
  Layers,
  Activity 
} from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function EvidenceViewer({ track, onClose }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!track) return null;

  const quality = track.quality || {};
  const fullFrameUrl = `${API_BASE_URL}${track.full_frame_url}`;
  const faceUrl = `${API_BASE_URL}${track.face_image_url}`;

  const metrics = [
    { label: 'Overall Clarity Score', value: `${track.best_score}%`, max: 100, score: track.best_score, color: 'var(--accent-cyan)' },
    { label: 'Laplacian Sharpness', value: quality.sharpness ?? '0', max: 350, score: quality.sharpness_normalized ?? 50, color: '#38bdf8' },
    { label: 'Luminance Balance', value: `${quality.brightness ?? 0} / 255`, max: 100, score: quality.brightness_score ?? 70, color: 'var(--accent-amber)' },
    { label: 'Dynamic Contrast', value: `${quality.contrast ?? 0}`, max: 100, score: quality.contrast_score ?? 60, color: 'var(--accent-indigo)' },
    { label: 'Sensor Resolution', value: `${quality.crop_width} x ${quality.crop_height} px`, max: 100, score: quality.resolution_score ?? 65, color: 'var(--accent-emerald)' }
  ];

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = fullFrameUrl;
    link.download = `kestral_evidence_track_${track.track_id}.jpg`;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(8px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px'
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '1100px',
          maxHeight: '90vh',
          backgroundColor: '#0a0e1a',
          border: '1px solid var(--border-glow)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.8), 0 0 30px var(--accent-indigo-glow)',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 'var(--radius-xl)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: 'rgba(255, 255, 255, 0.02)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              backgroundColor: 'rgba(6, 182, 212, 0.15)',
              border: '1px solid rgba(6, 182, 212, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-cyan)'
            }}>
              <ShieldCheck size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.02em' }}>
                Evidence Dossier: Subject #{track.track_id}
              </h2>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Frame #{track.best_frame_idx} • T+{track.best_timestamp}s • {track.total_detections} Total Detections
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={handleDownload}
              className="btn btn-secondary"
              style={{ padding: '8px 14px', fontSize: '0.8rem' }}
            >
              <Download size={15} />
              <span>Export Capture</span>
            </button>
            <button
              onClick={onClose}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-secondary)',
                borderRadius: '8px',
                width: '36px',
                height: '36px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer'
              }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Modal Content Grid */}
        <div 
          className="evidence-modal-grid"
          style={{
            padding: '24px',
            display: 'grid',
            gridTemplateColumns: '1.4fr 1fr',
            gap: '24px'
          }}
        >
          {/* Left Column: Visual Capture Frame */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{
              position: 'relative',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
              border: '1px solid var(--border-subtle)',
              backgroundColor: '#000',
              aspectRatio: '16/9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <img
                src={fullFrameUrl}
                alt="Full Surveillance Capture"
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
              <div style={{
                position: 'absolute',
                top: '12px',
                left: '12px',
                backgroundColor: 'rgba(0,0,0,0.7)',
                padding: '4px 10px',
                borderRadius: '4px',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.72rem',
                color: 'var(--accent-emerald)',
                border: '1px solid rgba(16, 185, 129, 0.3)'
              }}>
                FULL CONTEXT FRAME
              </div>
            </div>

            {/* Sub-crops row */}
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
              <div style={{
                width: '120px',
                height: '120px',
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
                border: '1px solid var(--accent-cyan)',
                backgroundColor: '#05070c',
                flexShrink: 0
              }}>
                <img
                  src={faceUrl}
                  alt="Biometric Face Crop"
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                />
              </div>

              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                <p style={{ fontWeight: 600, color: '#fff', marginBottom: '4px' }}>
                  Isolated Biometric Crop
                </p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {quality.is_heuristic ? 'Estimated head/upper-body ROI' : 'Confirmed facial cascade detection'}
                </p>
                <div style={{ marginTop: '6px', display: 'flex', gap: '6px' }}>
                  <span className="badge badge-excellent">{quality.grade} FIDELITY</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Multi-Metric Analysis */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            backgroundColor: 'rgba(0, 0, 0, 0.3)',
            padding: '20px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>
                Biometric Quality Analysis
              </h3>
              <Activity size={16} color="var(--accent-cyan)" />
            </div>

            {/* Metric Bars */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '6px' }}>
              {metrics.map((m, idx) => (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{m.label}</span>
                    <span style={{ color: '#fff', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{m.value}</span>
                  </div>
                  <div style={{
                    height: '6px',
                    backgroundColor: 'rgba(255, 255, 255, 0.08)',
                    borderRadius: '999px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${Math.min(100, Math.max(5, m.score))}%`,
                      height: '100%',
                      backgroundColor: m.color,
                      borderRadius: '999px'
                    }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Telemetry metadata table */}
            <div style={{
              marginTop: '12px',
              paddingTop: '16px',
              borderTop: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>First Tracked:</span>
                <span style={{ color: '#fff' }}>T+{track.first_seen_time}s</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Last Tracked:</span>
                <span style={{ color: '#fff' }}>T+{track.last_seen_time}s</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Active Duration:</span>
                <span style={{ color: 'var(--accent-cyan)' }}>{track.duration_seconds}s</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Person BBox:</span>
                <span style={{ color: '#fff' }}>[{track.person_bbox?.join(', ')}]</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
