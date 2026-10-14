import React, { useState, useEffect } from 'react';
import { 
  X, 
  Download, 
  Sparkles, 
  ShieldCheck, 
  Maximize2, 
  Crosshair, 
  Clock, 
  Layers,
  Activity,
  AlertTriangle,
  Compass,
  Sun,
  Eye,
  Sliders,
  CheckCircle2
} from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function EvidenceViewer({ track, onClose }) {
  const [activeCropUrl, setActiveCropUrl] = useState(null);
  const [activeFrameIdx, setActiveFrameIdx] = useState(null);
  const [activeTimestamp, setActiveTimestamp] = useState(null);
  const [activeScore, setActiveScore] = useState(null);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    if (track) {
      setActiveCropUrl(`${API_BASE_URL}${track.face_image_url}`);
      setActiveFrameIdx(track.best_frame_idx);
      setActiveTimestamp(track.best_timestamp);
      setActiveScore(track.best_score);
    }
  }, [track]);

  if (!track) return null;

  const quality = track.quality || {};
  const fullFrameUrl = `${API_BASE_URL}${track.full_frame_url}`;
  const runnerUps = track.runner_ups || [];
  const flags = quality.flags || [];

  const subScores = [
    {
      label: 'Composite Quality Score',
      value: `${activeScore ?? track.best_score}%`,
      pct: activeScore ?? track.best_score,
      color: 'var(--accent-cyan)'
    },
    {
      label: 'Size-Normalized Sharpness',
      value: `${quality.sharpness_normalized ?? 0}%`,
      pct: quality.sharpness_normalized ?? 0,
      color: '#38bdf8'
    },
    {
      label: 'Pixel Resolution / Size',
      value: `${quality.size_score ?? quality.resolution_score ?? 0}% (${quality.crop_width || 0}x${quality.crop_height || 0})`,
      pct: quality.size_score ?? quality.resolution_score ?? 0,
      color: 'var(--accent-emerald)'
    },
    {
      label: 'Geometric Pose / Symmetry',
      value: `${quality.pose_score ?? 70}% (yaw: ${quality.yaw_proxy ?? 0.0})`,
      pct: quality.pose_score ?? 70,
      color: 'var(--accent-indigo)'
    },
    {
      label: 'Photometric Exposure',
      value: `${quality.exposure_score ?? quality.brightness_score ?? 0}%`,
      pct: quality.exposure_score ?? quality.brightness_score ?? 0,
      color: 'var(--accent-amber)'
    }
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
          maxWidth: '1140px',
          maxHeight: '92vh',
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-glow)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.4), 0 0 30px var(--accent-indigo-glow)',
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
          backgroundColor: 'var(--bg-input)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '8px',
              backgroundColor: 'rgba(6, 182, 212, 0.15)',
              border: '1px solid rgba(6, 182, 212, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-cyan)'
            }}>
              <ShieldCheck size={22} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                Evidence Dossier: Subject #{track.track_id}
              </h2>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Active Frame #{activeFrameIdx} • T+{activeTimestamp}s • {track.total_detections} Tracked Samples
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
              <span>Export Full Capture</span>
            </button>
            <button
              onClick={onClose}
              style={{
                background: 'var(--bg-input)',
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
            gridTemplateColumns: '1.35fr 1.05fr',
            gap: '24px'
          }}
        >
          {/* Left Column: Visual Capture Frame & Runner-ups */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
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
                SURVEILLANCE SCENE CONTEXT
              </div>
            </div>

            {/* Active Face Crop Display & Flags */}
            <div style={{
              display: 'flex',
              gap: '16px',
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)'
            }}>
              <div style={{
                width: '100px',
                height: '100px',
                borderRadius: '8px',
                overflow: 'hidden',
                border: '2px solid var(--accent-cyan)',
                backgroundColor: '#05070c',
                flexShrink: 0
              }}>
                <img
                  src={activeCropUrl}
                  alt="Selected Biometric Face Crop"
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              </div>

              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
                  <span style={{
                    padding: '3px 8px',
                    borderRadius: '4px',
                    backgroundColor: track.has_real_face ? 'rgba(16, 185, 129, 0.2)' : 'rgba(244, 63, 94, 0.2)',
                    color: track.has_real_face ? '#34d399' : '#fb7185',
                    fontSize: '0.72rem',
                    fontWeight: 800
                  }}>
                    {track.has_real_face ? 'VERIFIED REAL FACE' : 'HEAD CROP (FACING AWAY)'}
                  </span>

                  {quality.enhanced && (
                    <span style={{
                      padding: '3px 8px',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(245, 158, 11, 0.2)',
                      color: '#fbbf24',
                      fontSize: '0.72rem',
                      fontWeight: 700
                    }}>
                      CLAHE LOW-LIGHT ENHANCED
                    </span>
                  )}

                  {flags.map((flag, idx) => (
                    <span
                      key={idx}
                      style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        backgroundColor: 'rgba(255, 255, 255, 0.08)',
                        color: 'var(--text-secondary)',
                        fontSize: '0.7rem',
                        fontFamily: 'var(--font-mono)'
                      }}
                    >
                      #{flag.toUpperCase()}
                    </span>
                  ))}
                </div>

                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Active Resolution: {quality.crop_width || 0}x{quality.crop_height || 0}px • Metric Grade: {quality.grade || 'N/A'}
                </p>
              </div>
            </div>

            {/* Runner-Ups Temporal Candidate Strip */}
            {runnerUps.length > 0 && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                  <Layers size={15} color="var(--accent-cyan)" />
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    Alternative Evidence Frames ({runnerUps.length} Runner-ups)
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '12px', overflowX: 'auto', paddingBottom: '6px' }}>
                  {/* Primary Best Frame Item */}
                  <div
                    onClick={() => {
                      setActiveCropUrl(`${API_BASE_URL}${track.face_image_url}`);
                      setActiveFrameIdx(track.best_frame_idx);
                      setActiveTimestamp(track.best_timestamp);
                      setActiveScore(track.best_score);
                    }}
                    style={{
                      width: '84px',
                      flexShrink: 0,
                      cursor: 'pointer',
                      borderRadius: '6px',
                      overflow: 'hidden',
                      border: activeFrameIdx === track.best_frame_idx ? '2px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                      backgroundColor: 'var(--bg-input)',
                      padding: '4px',
                      textAlign: 'center'
                    }}
                  >
                    <img
                      src={`${API_BASE_URL}${track.face_image_url}`}
                      alt="Primary"
                      style={{ width: '100%', height: '64px', objectFit: 'cover', borderRadius: '4px' }}
                    />
                    <div style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--accent-cyan)', marginTop: '4px' }}>
                      #1 Best ({track.best_score})
                    </div>
                  </div>

                  {/* Runner-Ups */}
                  {runnerUps.map((ru, idx) => (
                    <div
                      key={idx}
                      onClick={() => {
                        setActiveCropUrl(`${API_BASE_URL}${ru.face_image_url}`);
                        setActiveFrameIdx(ru.frame_idx);
                        setActiveTimestamp(ru.timestamp);
                        setActiveScore(ru.score);
                      }}
                      style={{
                        width: '84px',
                        flexShrink: 0,
                        cursor: 'pointer',
                        borderRadius: '6px',
                        overflow: 'hidden',
                        border: activeFrameIdx === ru.frame_idx ? '2px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                        backgroundColor: 'var(--bg-input)',
                        padding: '4px',
                        textAlign: 'center'
                      }}
                    >
                      <img
                        src={`${API_BASE_URL}${ru.face_image_url}`}
                        alt={`Runner-up ${idx + 1}`}
                        style={{ width: '100%', height: '64px', objectFit: 'cover', borderRadius: '4px' }}
                      />
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        T+{ru.timestamp}s ({ru.score})
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Multi-Dimensional Quality Breakdown */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{
              padding: '20px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                <Sliders size={18} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Quality v2 Multi-Metric Breakdown
                </h3>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {subScores.map((s, idx) => (
                  <div key={idx}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '6px' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>{s.label}</span>
                      <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{s.value}</span>
                    </div>
                    <div style={{ height: '7px', borderRadius: '3px', backgroundColor: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, Math.max(0, s.pct))}%`, height: '100%', backgroundColor: s.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Trajectory & Spatiotemporal Dwell Info */}
            <div style={{
              padding: '20px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                <Compass size={18} color="var(--accent-indigo)" />
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Spatiotemporal Surveillance Trajectory
                </h3>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                <div style={{ padding: '10px', borderRadius: '6px', backgroundColor: 'var(--bg-secondary)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>FIRST APPEARANCE</div>
                  <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginTop: '2px' }}>T+{track.first_seen_time}s</div>
                </div>
                <div style={{ padding: '10px', borderRadius: '6px', backgroundColor: 'var(--bg-secondary)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>LAST APPEARANCE</div>
                  <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginTop: '2px' }}>T+{track.last_seen_time}s</div>
                </div>
                <div style={{ padding: '10px', borderRadius: '6px', backgroundColor: 'var(--bg-secondary)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>TOTAL DWELL TIME</div>
                  <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, marginTop: '2px' }}>{track.duration_seconds} sec</div>
                </div>
                <div style={{ padding: '10px', borderRadius: '6px', backgroundColor: 'var(--bg-secondary)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>SAMPLED TRAJECTORY</div>
                  <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginTop: '2px' }}>{track.trajectory?.length ?? track.total_detections} pts</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
