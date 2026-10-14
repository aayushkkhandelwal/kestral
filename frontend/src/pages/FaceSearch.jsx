import React, { useState } from 'react';
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
  Image as ImageIcon
} from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function FaceSearch({ onNavigateToEvidence }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [topK, setTopK] = useState(5);
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

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
      const res = await axios.post(
        `${API_BASE_URL}/api/search/face?top_k=${topK}`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );
      setResults(res.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Face similarity search failed. Ensure backend has processed footage.');
    } finally {
      setSearching(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.03em' }}>
          Biometric Facial Similarity Search
        </h1>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          128-dimensional deep feature matching across archived surveillance evidence (YuNet + SFace)
        </p>
      </div>

      {/* Legal & Investigative Disclaimer Banner */}
      <div style={{
        padding: '14px 18px',
        borderRadius: 'var(--radius-md)',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}>
        <AlertCircle size={20} color="#fbbf24" style={{ flexShrink: 0 }} />
        <div style={{ fontSize: '0.825rem', color: '#fde68a' }}>
          <strong>INVESTIGATIVE NOTICE:</strong> Results represent statistical visual similarity only, computed on CCTV evidence. This tool does not establish legal identity and requires certified forensic and investigator review.
        </div>
      </div>

      {/* Search Input Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: '24px' }}>
        {/* Upload Probe Card */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff', marginBottom: '16px' }}>
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
                backgroundColor: 'rgba(0, 0, 0, 0.25)',
                cursor: 'pointer',
                textAlign: 'center',
                minHeight: '180px'
              }}
            >
              {previewUrl ? (
                <div style={{ position: 'relative', width: '130px', height: '130px', borderRadius: '8px', overflow: 'hidden', border: '2px solid var(--accent-cyan)' }}>
                  <img src={previewUrl} alt="Probe" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                </div>
              ) : (
                <>
                  <UploadCloud size={36} color="var(--accent-cyan)" style={{ marginBottom: '10px' }} />
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#fff' }}>Click to select face image</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>JPG, PNG, WebP up to 10MB</span>
                </>
              )}
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
            </label>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Maximum Returned Matches (Top-K)
              </label>
              <select
                value={topK}
                onChange={e => setTopK(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: '#070b14',
                  border: '1px solid var(--border-subtle)',
                  color: '#fff'
                }}
              >
                <option value={3}>Top 3 Candidates</option>
                <option value={5}>Top 5 Candidates</option>
                <option value={10}>Top 10 Candidates</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={!selectedFile || searching}
              className="btn btn-primary"
              style={{ padding: '12px', marginTop: '4px' }}
            >
              <Search size={16} />
              <span>{searching ? 'Querying Feature Vectors...' : 'Search Evidence Archive'}</span>
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
              <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
                Candidate Matches {results ? `(${results.length})` : ''}
              </h2>
            </div>
          </div>

          {!results ? (
            <div style={{ padding: '48px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Upload a probe face photo on the left to search across all archived ATM surveillance tracks.
            </div>
          ) : results.length === 0 ? (
            <div style={{ padding: '48px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No matches found in the current evidence archive. Process more surveillance clips to index subjects.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {results.map((c, idx) => {
                const simPct = Math.round(c.similarity * 100);
                const fullUrl = c.face_image_url ? `${API_BASE_URL}${c.face_image_url}` : null;

                return (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '16px',
                      padding: '14px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'rgba(0,0,0,0.3)',
                      border: idx === 0 ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)'
                    }}
                  >
                    {/* Rank Badge */}
                    <div style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      backgroundColor: idx === 0 ? 'var(--accent-cyan)' : 'rgba(255,255,255,0.06)',
                      color: idx === 0 ? '#000' : '#fff',
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
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontWeight: 800, color: '#fff', fontSize: '0.95rem' }}>
                          Task #{c.task_id} • Track #{c.track_id}
                        </span>
                        <span style={{
                          fontSize: '0.72rem',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          backgroundColor: 'rgba(6, 182, 212, 0.15)',
                          color: 'var(--accent-cyan)',
                          fontFamily: 'var(--font-mono)'
                        }}>
                          T+{c.timestamp}s
                        </span>
                      </div>

                      {/* Similarity Bar */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '6px' }}>
                        <div style={{ flex: 1, height: '6px', borderRadius: '3px', backgroundColor: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                          <div style={{ width: `${simPct}%`, height: '100%', backgroundColor: simPct > 75 ? 'var(--accent-emerald)' : 'var(--accent-cyan)' }} />
                        </div>
                        <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#fff', fontFamily: 'var(--font-mono)' }}>
                          {simPct}%
                        </span>
                      </div>

                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        {c.note}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
