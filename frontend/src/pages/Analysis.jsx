import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Play, 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  Cpu, 
  Film, 
  Users, 
  Sparkles,
  BarChart3 
} from 'lucide-react';
import { API_BASE_URL } from '../config';
import VideoUploader from '../components/VideoUploader';
import TrackResults from '../components/TrackResults';
import EvidenceViewer from '../components/EvidenceViewer';

export default function Analysis({ onRefreshStats }) {
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [resultsData, setResultsData] = useState(null);
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Poll for status when activeTaskId is processing
  useEffect(() => {
    let interval = null;

    if (activeTaskId && isProcessing) {
      interval = setInterval(async () => {
        try {
          const res = await axios.get(`${API_BASE_URL}/api/tasks/${activeTaskId}/status`);
          const data = res.data;
          setTaskStatus(data);

          if (data.status === 'completed') {
            setIsProcessing(false);
            setResultsData(data.result);
            if (onRefreshStats) onRefreshStats();
          } else if (data.status === 'failed') {
            setIsProcessing(false);
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [activeTaskId, isProcessing, onRefreshStats]);

  const handleTaskCreated = (taskId) => {
    setActiveTaskId(taskId);
    setIsProcessing(true);
    setResultsData(null);
    setTaskStatus({ status: 'processing', progress: 0, current_frame: 0, total_frames: 0 });
  };

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
          Surveillance Stream Processing
        </h1>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          Ingest raw footage, execute YOLO ByteTrack algorithms, and extract optimal facial fidelity frames
        </p>
      </div>

      {/* Video Uploader */}
      <VideoUploader onTaskCreated={handleTaskCreated} isProcessing={isProcessing} />

      {/* Real-Time Processing Status Monitor */}
      {isProcessing && taskStatus && (
        <div className="glass-panel" style={{ padding: '24px', marginTop: '24px', border: '1px solid var(--border-glow)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Loader2 size={22} color="var(--accent-cyan)" className="pulse-indicator" />
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Processing Video Stream (Task #{activeTaskId})
                </h3>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Extracting frames, evaluating Laplacian sharpness & tracking identity paths
                </p>
              </div>
            </div>

            <span className="badge badge-good">
              {taskStatus.processing_fps || 24} FPS Active
            </span>
          </div>

          {/* Progress Bar */}
          <div style={{
            height: '8px',
            backgroundColor: 'var(--border-subtle)',
            borderRadius: '999px',
            overflow: 'hidden',
            marginBottom: '14px'
          }}>
            <div style={{
              width: `${taskStatus.progress || 0}%`,
              height: '100%',
              background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-indigo))',
              transition: 'width 0.4s ease'
            }} />
          </div>

          {/* Progress Telemetry */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '0.78rem',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-secondary)'
          }}>
            <span>Progress: {taskStatus.progress || 0}%</span>
            <span>Frame: {taskStatus.current_frame || 0} / {taskStatus.total_frames || '...'}</span>
            <span>Persons Discovered: {taskStatus.tracks_count || 0}</span>
          </div>
        </div>
      )}

      {/* Failed Task Error Banner */}
      {taskStatus?.status === 'failed' && (
        <div className="glass-panel" style={{
          padding: '20px 24px',
          marginTop: '24px',
          border: '1px solid rgba(244, 63, 94, 0.4)',
          backgroundColor: 'rgba(244, 63, 94, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <AlertCircle size={24} color="#f43f5e" />
            <div>
              <h4 style={{ color: 'var(--text-primary)', fontSize: '1rem', fontWeight: 700 }}>Processing Error</h4>
              <p style={{ color: '#fb7185', fontSize: '0.825rem' }}>
                {taskStatus.error || 'Video could not be processed. Please try again with another video sequence.'}
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              setActiveTaskId(null);
              setTaskStatus(null);
            }}
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '8px 16px' }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Completed Results Summary Banner */}
      {resultsData && (
        <div className="glass-panel" style={{
          padding: '24px',
          marginTop: '24px',
          marginBottom: '28px',
          border: '1px solid rgba(16, 185, 129, 0.35)',
          background: 'linear-gradient(180deg, rgba(16, 185, 129, 0.08) 0%, var(--bg-card) 100%)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <CheckCircle2 size={24} color="var(--accent-emerald)" />
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Analysis Successfully Completed
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  Processed {resultsData.metadata?.frames_processed} frames in {resultsData.metadata?.elapsed_time_sec}s
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <span className="badge badge-excellent">
                {resultsData.summary?.unique_persons_tracked} Persons Tracked
              </span>
              <span className="badge badge-good">
                Avg Score: {resultsData.summary?.average_best_quality}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tracked Results Gallery */}
      <div style={{ marginTop: '28px' }}>
        <TrackResults
          tracks={resultsData?.tracks || []}
          onSelectTrack={(track) => setSelectedTrack(track)}
        />
      </div>

      {/* Modal Evidence Dossier Inspector */}
      {selectedTrack && (
        <EvidenceViewer
          track={selectedTrack}
          onClose={() => setSelectedTrack(null)}
        />
      )}
    </div>
  );
}
