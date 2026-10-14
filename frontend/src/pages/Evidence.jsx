import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  ShieldCheck, 
  Search, 
  Filter, 
  Sparkles, 
  Download, 
  Eye, 
  ArrowUpDown,
  RefreshCw 
} from 'lucide-react';
import { API_BASE_URL } from '../config';
import TrackResults from '../components/TrackResults';
import EvidenceViewer from '../components/EvidenceViewer';

export default function Evidence() {
  const [allTracks, setAllTracks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterGrade, setFilterGrade] = useState('ALL');
  const [sortBy, setSortBy] = useState('SCORE_DESC');
  const [selectedTrack, setSelectedTrack] = useState(null);

  const fetchEvidenceHistory = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/history`);
      const historyList = res.data || [];
      
      // Fetch full results for each task to gather all tracks
      let combinedTracks = [];
      for (const item of historyList) {
        try {
          const detailRes = await axios.get(`${API_BASE_URL}/api/tasks/${item.task_id}/results`);
          if (detailRes.data?.tracks) {
            const tracksWithTask = detailRes.data.tracks.map(t => ({
              ...t,
              origin_task_id: item.task_id
            }));
            combinedTracks = combinedTracks.concat(tracksWithTask);
          }
        } catch (e) {
          console.warn(`Could not load details for task ${item.task_id}:`, e);
        }
      }
      setAllTracks(combinedTracks);
    } catch (err) {
      console.error('Failed to load evidence vault:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvidenceHistory();
  }, []);

  // Filter and sort tracks
  const filteredTracks = allTracks.filter((t) => {
    const matchesSearch = 
      t.track_id.toString().includes(searchQuery) ||
      (t.origin_task_id && t.origin_task_id.toLowerCase().includes(searchQuery.toLowerCase()));

    if (!matchesSearch) return false;

    if (filterGrade === 'ALL') return true;
    return t.quality?.grade === filterGrade;
  }).sort((a, b) => {
    if (sortBy === 'SCORE_DESC') return b.best_score - a.best_score;
    if (sortBy === 'DURATION_DESC') return b.duration_seconds - a.duration_seconds;
    if (sortBy === 'TIME_ASC') return a.best_timestamp - b.best_timestamp;
    return 0;
  });

  return (
    <div>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
            Biometric Evidence Vault
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Central repository of highest-fidelity facial captures, ranked by biometric quality index
          </p>
        </div>

        <button
          onClick={fetchEvidenceHistory}
          className="btn btn-secondary"
          style={{ padding: '8px 16px', fontSize: '0.825rem' }}
        >
          <RefreshCw size={15} />
          <span>Refresh Vault</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel" style={{
        padding: '16px 20px',
        marginBottom: '28px',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: '16px',
        justifyContent: 'space-between'
      }}>
        {/* Search Input */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          backgroundColor: 'var(--bg-input)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          padding: '8px 14px',
          minWidth: '260px'
        }}>
          <Search size={16} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search Subject ID or Task ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.85rem',
              width: '100%'
            }}
          />
        </div>

        {/* Controls Row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Grade Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Grade:</span>
            <select
              value={filterGrade}
              onChange={(e) => setFilterGrade(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-input)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.825rem',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="ALL">All Fidelity Grades</option>
              <option value="EXCELLENT">Excellent (82%+)</option>
              <option value="GOOD">Good (65%+)</option>
              <option value="FAIR">Fair (45%+)</option>
              <option value="POOR">Low (&lt;45%)</option>
            </select>
          </div>

          {/* Sort By */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-input)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.825rem',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="SCORE_DESC">Quality Score (High to Low)</option>
              <option value="DURATION_DESC">Track Duration (Longest)</option>
              <option value="TIME_ASC">Timestamp (Earliest First)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Gallery */}
      <TrackResults
        tracks={filteredTracks}
        onSelectTrack={(track) => setSelectedTrack(track)}
      />

      {/* Modal Inspector */}
      {selectedTrack && (
        <EvidenceViewer
          track={selectedTrack}
          onClose={() => setSelectedTrack(null)}
        />
      )}
    </div>
  );
}
