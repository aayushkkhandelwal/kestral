import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Search, 
  UploadCloud, 
  Sparkles, 
  AlertCircle, 
  ShieldCheck, 
  UserCheck, 
  ArrowRight,
  Filter,
  Image as ImageIcon,
  MapPin,
  Clock,
  Layers,
  Database,
  Wand2,
  Maximize2
} from 'lucide-react';
import { API_BASE_URL } from '../config';
import EvidenceViewer from '../components/EvidenceViewer';

export default function FaceSearch({ onNavigateToEvidence }) {
  const [activeTab, setActiveTab] = useState('search'); // 'search' | 'database'
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [topK, setTopK] = useState(5);
  const [atmFilter, setAtmFilter] = useState('');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // Database faces browser
  const [dbFaces, setDbFaces] = useState([]);
  const [loadingDb, setLoadingDb] = useState(false);

  // Modal inspection of candidate
  const [inspectingTrack, setInspectingTrack] = useState(null);

  useEffect(() => {
    if (activeTab === 'database') {
      fetchDatabaseFaces();
    }
  }, [activeTab, atmFilter]);

  const fetchDatabaseFaces = async () => {
    setLoadingDb(true);
    try {
      const url = atmFilter 
        ? `${API_BASE_URL}/api/search/database-faces?atm_id=${encodeURIComponent(atmFilter)}&limit=100`
        : `${API_BASE_URL}/api/search/database-faces?limit=100`;
      const res = await axios.get(url);
      setDbFaces(res.data.faces || []);
    } catch (err) {
      console.error('Failed to load database faces:', err);
    } finally {
      setLoadingDb(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResults(null);
      setError(null);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setSearching(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      let url = `${API_BASE_URL}/api/search/face?top_k=${topK}`;
      if (atmFilter) {
        url += `&atm_id=${encodeURIComponent(atmFilter)}`;
      }

      const res = await axios.post(url, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResults(res.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Face similarity search failed. Ensure backend has indexed footage.');
    } finally {
      setSearching(false);
    }
  };

  const openEvidenceModal = (candidate) => {
    // Construct track object compatible with EvidenceViewer
    setInspectingTrack({
      track_id: candidate.track_id,
      task_id: candidate.task_id,
      atm_id: candidate.atm_id,
      location_name: candidate.location_name,
      wall_clock_time: candidate.wall_clock_time,
      face_image_url: candidate.face_image_url,
      enhanced_image_url: candidate.enhanced_image_url,
      composite_image_url: candidate.composite_image_url,
      full_frame_url: candidate.full_frame_url || candidate.face_image_url,
      best_frame_idx: 0,
      best_timestamp: candidate.timestamp || 0.0,
      best_score: Math.round((candidate.quality_score || 85.0) * (candidate.quality_score > 1 ? 1 : 100)),
      total_detections: 1,
      first_seen_time: candidate.timestamp || 0.0,
      last_seen_time: candidate.timestamp || 0.0,
      duration_seconds: 0.0,
      has_real_face: true,
      quality: {
        sharpness_normalized: Math.round(candidate.quality_score || 80),
        size_score: 85,
        pose_score: 80,
        exposure_score: 85,
        grade: 'Verified'
      }
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
            Biometric Facial Similarity Search
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Database-backed 128D cosine vector matching across indexed ATM surveillance evidence (SQLite + YuNet + SFace)
          </p>
        </div>

        {/* Tab Switcher */}
        <div style={{
          display: 'flex',
          gap: '6px',
          backgroundColor: 'var(--bg-input)',
          padding: '4px',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)'
        }}>
          <button
            onClick={() => setActiveTab('search')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '6px',
              border: 'none',
              backgroundColor: activeTab === 'search' ? 'var(--accent-cyan)' : 'transparent',
              color: activeTab === 'search' ? '#000' : 'var(--text-secondary)',
              fontWeight: activeTab === 'search' ? 700 : 500,
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            <Search size={14} />
            <span>Probe Search</span>
          </button>

          <button
            onClick={() => setActiveTab('database')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '6px',
              border: 'none',
              backgroundColor: activeTab === 'database' ? 'var(--accent-indigo)' : 'transparent',
              color: activeTab === 'database' ? '#fff' : 'var(--text-secondary)',
              fontWeight: activeTab === 'database' ? 700 : 500,
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            <Database size={14} />
            <span>Evidence Database</span>
          </button>
        </div>
      </div>

      {/* Legal & Investigative Disclaimer Banner */}
      <div style={{
        padding: '12px 18px',
        borderRadius: 'var(--radius-md)',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}>
        <AlertCircle size={20} color="#fbbf24" style={{ flexShrink: 0 }} />
        <div style={{ fontSize: '0.825rem', color: '#fde68a' }}>
          <strong>INVESTIGATIVE NOTICE:</strong> Results represent statistical visual similarity only, computed on ATM CCTV evidence. This tool does not establish legal identity and requires certified forensic and investigator review.
        </div>
      </div>

      {/* Search Mode Tab */}
      {activeTab === 'search' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: '24px' }}>
          {/* Upload Probe Card */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px' }}>
              Upload Probe Image
            </h2>

            <form onSubmit={handleSearch} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <label
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '24px',
                  borderRadius: 'var(--radius-md)',
                  border: '2px dashed var(--border-glow)',
                  backgroundColor: 'var(--bg-input)',
                  cursor: 'pointer',
                  textAlign: 'center',
                  minHeight: '180px',
                  transition: 'border-color 0.2s ease'
                }}
              >
                {previewUrl ? (
                  <div style={{ position: 'relative', width: '130px', height: '130px', borderRadius: '8px', overflow: 'hidden', border: '2px solid var(--accent-cyan)' }}>
                    <img src={previewUrl} alt="Probe" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  </div>
                ) : (
                  <>
                    <UploadCloud size={36} color="var(--accent-cyan)" style={{ marginBottom: '10px' }} />
                    <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>Click to select face photo</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>JPG, PNG, WebP from ATM or ID</span>
                  </>
                )}
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
              </label>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Top-K Matches
                  </label>
                  <select
                    value={topK}
                    onChange={e => setTopK(Number(e.target.value))}
                    style={{
                      width: '100%',
                      padding: '8px 10px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--bg-input)',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-primary)',
                      fontSize: '0.82rem'
                    }}
                  >
                    <option value={3}>Top 3</option>
                    <option value={5}>Top 5</option>
                    <option value={10}>Top 10</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    ATM Filter (optional)
                  </label>
                  <input
                    type="text"
                    value={atmFilter}
                    onChange={e => setAtmFilter(e.target.value)}
                    placeholder="All ATMs"
                    style={{
                      width: '100%',
                      padding: '8px 10px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--bg-input)',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-primary)',
                      fontSize: '0.82rem',
                      fontFamily: 'var(--font-mono)'
                    }}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={!selectedFile || searching}
                className="btn btn-primary"
                style={{ padding: '12px', marginTop: '4px' }}
              >
                <Search size={16} />
                <span>{searching ? 'Querying Biometric Database...' : 'Search Evidence Database'}</span>
              </button>
            </form>

            {error && (
              <div style={{ marginTop: '14px', fontSize: '0.8rem', color: '#fb7185' }}>
                {error}
              </div>
            )}
          </div>

          {/* Results Column */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <UserCheck size={20} color="var(--accent-cyan)" />
                <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Database Candidate Matches {results ? `(${results.length})` : ''}
                </h2>
              </div>
            </div>

            {!results ? (
              <div style={{ padding: '48px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Upload a probe facial crop to run cosine similarity against indexed SQLite evidence faces.
              </div>
            ) : results.length === 0 ? (
              <div style={{ padding: '48px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No matches found in the current evidence archive. Process surveillance clips to index faces.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {results.map((c, idx) => {
                  const simPct = Math.round(c.similarity * 100);
                  const fullUrl = c.face_image_url ? `${API_BASE_URL}${c.face_image_url}` : null;
                  const enhancedUrl = c.enhanced_image_url ? `${API_BASE_URL}${c.enhanced_image_url}` : null;
                  const compositeUrl = c.composite_image_url ? `${API_BASE_URL}${c.composite_image_url}` : null;

                  return (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '16px',
                        padding: '14px',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: 'var(--bg-input)',
                        border: idx === 0 ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                        flexWrap: 'wrap'
                      }}
                    >
                      {/* Rank Badge */}
                      <div style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: '50%',
                        backgroundColor: idx === 0 ? 'var(--accent-cyan)' : 'rgba(255,255,255,0.06)',
                        color: idx === 0 ? '#000' : 'var(--text-primary)',
                        fontWeight: 800,
                        fontSize: '0.85rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0
                      }}>
                        #{idx + 1}
                      </div>

                      {/* Face Image */}
                      <div style={{
                        width: '64px',
                        height: '64px',
                        borderRadius: '8px',
                        overflow: 'hidden',
                        backgroundColor: '#05070c',
                        border: '1px solid var(--border-subtle)',
                        flexShrink: 0
                      }}>
                        {fullUrl ? (
                          <img src={fullUrl} alt="Candidate" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        ) : (
                          <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <ImageIcon size={20} color="var(--text-muted)" />
                          </div>
                        )}
                      </div>

                      {/* Details */}
                      <div style={{ flex: 1, minWidth: '180px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                          <span style={{ fontWeight: 800, color: 'var(--text-primary)', fontSize: '0.92rem' }}>
                            Subject #{c.track_id}
                          </span>
                          <span className="badge badge-secondary" style={{ fontSize: '0.7rem' }}>
                            📍 {c.location_name || 'ATM Kiosk'} ({c.atm_id || 'ATM'})
                          </span>
                        </div>

                        {/* Timestamp & Location Metadata */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                          <span>🕒 {c.wall_clock_time || `T+${c.timestamp}s`}</span>
                          {enhancedUrl && (
                            <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>• AI Deblurred</span>
                          )}
                          {compositeUrl && (
                            <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>• Multi-Angle Plate</span>
                          )}
                        </div>

                        {/* Similarity Bar */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '8px' }}>
                          <div style={{ flex: 1, height: '6px', borderRadius: '3px', backgroundColor: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                            <div style={{ width: `${simPct}%`, height: '100%', backgroundColor: simPct > 75 ? 'var(--accent-emerald)' : 'var(--accent-cyan)' }} />
                          </div>
                          <span style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                            {simPct}%
                          </span>
                        </div>
                      </div>

                      {/* Action Button */}
                      <div>
                        <button
                          onClick={() => openEvidenceModal(c)}
                          className="btn btn-secondary"
                          style={{ padding: '6px 12px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                        >
                          <Maximize2 size={13} />
                          <span>Inspect</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Database Explorer Tab */}
      {activeTab === 'database' && (
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Database size={20} color="var(--accent-indigo)" />
              <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Indexed Evidence Faces in SQLite Registry ({dbFaces.length})
              </h2>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <input
                type="text"
                value={atmFilter}
                onChange={e => setAtmFilter(e.target.value)}
                placeholder="Filter by ATM ID..."
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-primary)',
                  fontSize: '0.78rem',
                  fontFamily: 'var(--font-mono)'
                }}
              />
              <button
                onClick={fetchDatabaseFaces}
                className="btn btn-secondary"
                style={{ padding: '6px 12px', fontSize: '0.78rem' }}
              >
                Refresh
              </button>
            </div>
          </div>

          {loadingDb ? (
            <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
              Loading database faces...
            </div>
          ) : dbFaces.length === 0 ? (
            <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No indexed faces found in the database.
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
              gap: '16px'
            }}>
              {dbFaces.map((f, idx) => {
                const faceUrl = f.face_image_url ? `${API_BASE_URL}${f.face_image_url}` : null;
                return (
                  <div
                    key={idx}
                    style={{
                      padding: '12px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--bg-input)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '10px'
                    }}
                  >
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                      <div style={{
                        width: '56px',
                        height: '56px',
                        borderRadius: '8px',
                        overflow: 'hidden',
                        backgroundColor: '#05070c',
                        border: '1px solid var(--border-subtle)',
                        flexShrink: 0
                      }}>
                        {faceUrl ? (
                          <img src={faceUrl} alt="Indexed Face" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        ) : (
                          <ImageIcon size={20} color="var(--text-muted)" />
                        )}
                      </div>

                      <div style={{ minWidth: 0, flex: 1 }}>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                          Subject #{f.track_id}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--accent-cyan)' }}>
                          📍 {f.location_name || f.atm_id}
                        </div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {f.wall_clock_time || `T+${f.timestamp_s}s`}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                      <span className="badge badge-good" style={{ fontSize: '0.68rem' }}>
                        Fidelity: {Math.round(f.quality_score || 80)}%
                      </span>

                      <button
                        onClick={() => openEvidenceModal(f)}
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '0.72rem' }}
                      >
                        Inspect Dossier
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Evidence Viewer Dossier Modal */}
      {inspectingTrack && (
        <EvidenceViewer
          track={inspectingTrack}
          onClose={() => setInspectingTrack(null)}
        />
      )}
    </div>
  );
}
