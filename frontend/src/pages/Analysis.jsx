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
  BarChart3,
  MapPin,
  Clock,
  Layers,
  ChevronRight
} from 'lucide-react';
import { API_BASE_URL } from '../config';
import VideoUploader from '../components/VideoUploader';
import TrackResults from '../components/TrackResults';
import EvidenceViewer from '../components/EvidenceViewer';

export default function Analysis({ onRefreshStats }) {
  // Map of taskId -> taskState
  const [tasks, setTasks] = useState({});
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [selectedTrack, setSelectedTrack] = useState(null);

  // Poll for status of all active (running) tasks
  useEffect(() => {
    const runningTaskIds = Object.keys(tasks).filter(id => {
      const s = tasks[id]?.status;
      return s === 'queued' || s === 'processing';
    });

    if (runningTaskIds.length === 0) return;

    const interval = setInterval(async () => {
      for (const tid of runningTaskIds) {
        try {
          const res = await axios.get(`${API_BASE_URL}/api/tasks/${tid}/status`);
          const data = res.data;

          setTasks(prev => {
            const current = prev[tid] || {};
            const updated = {
              ...current,
              ...data,
              // If finished, store the full result payload
              result: data.status === 'completed' ? data.result : current.result
            };
            return { ...prev, [tid]: updated };
          });

          if (data.status === 'completed' && onRefreshStats) {
            onRefreshStats();
          }
        } catch (err) {
          console.error(`Polling error for task ${tid}:`, err);
        }
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [tasks, onRefreshStats]);

  const handleTaskCreated = (taskId, filename, metadata) => {
    const newTask = {
      task_id: taskId,
      filename: filename || `Task-${taskId}`,
      status: 'processing',
      progress: 0,
      current_frame: 0,
      total_frames: 0,
      tracks_count: 0,
      metadata: metadata || {},
      created_at: new Date().toLocaleTimeString()
    };

    setTasks(prev => ({ ...prev, [taskId]: newTask }));
    setActiveTaskId(taskId);
  };

  const activeTask = activeTaskId ? tasks[activeTaskId] : null;
  const isAnyProcessing = Object.values(tasks).some(t => t.status === 'processing' || t.status === 'queued');
  const taskList = Object.values(tasks);

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
          Surveillance Stream Processing
        </h1>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          Ingest raw CCTV footage, process concurrent feeds with adaptive frame stride, and extract optimal facial fidelity evidence
        </p>
      </div>

      {/* Video Uploader */}
      <VideoUploader onTaskCreated={handleTaskCreated} isProcessing={false} />

      {/* Concurrent Task Queue Bar */}
      {taskList.length > 0 && (
        <div style={{ marginTop: '24px', marginBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Concurrent Analysis Feeds ({taskList.length})
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Worker Pool: 3 Parallel Processors
            </span>
          </div>

          <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', paddingBottom: '4px' }}>
            {taskList.map(task => {
              const isSelected = task.task_id === activeTaskId;
              const isRunning = task.status === 'processing' || task.status === 'queued';
              const isDone = task.status === 'completed';
              const isFailed = task.status === 'failed';

              return (
                <button
                  key={task.task_id}
                  onClick={() => setActiveTaskId(task.task_id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '8px 14px',
                    borderRadius: '8px',
                    border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                    backgroundColor: isSelected ? 'rgba(6, 182, 212, 0.12)' : 'var(--bg-input)',
                    color: isSelected ? 'var(--accent-cyan)' : 'var(--text-primary)',
                    cursor: 'pointer',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {isRunning && <Loader2 size={14} className="pulse-indicator" color="var(--accent-cyan)" />}
                  {isDone && <CheckCircle2 size={14} color="var(--accent-emerald)" />}
                  {isFailed && <AlertCircle size={14} color="#f43f5e" />}

                  <span>{task.filename || task.task_id}</span>
                  {isRunning && (
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--accent-cyan)' }}>
                      {task.progress || 0}%
                    </span>
                  )}
                  {isDone && (
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--accent-emerald)' }}>
                      {task.result?.tracks?.length ?? task.tracks_count ?? 0} tracks
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Real-Time Processing Status Monitor for Active Task */}
      {activeTask && (activeTask.status === 'processing' || activeTask.status === 'queued') && (
        <div className="glass-panel" style={{ padding: '24px', marginTop: '20px', border: '1px solid var(--border-glow)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Loader2 size={22} color="var(--accent-cyan)" className="pulse-indicator" />
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Processing Video Stream ({activeTask.filename} • #{activeTask.task_id})
                </h3>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Extracting frames, evaluating Laplacian sharpness, deblurring & tracking biometric identity paths
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {activeTask.atm_id && (
                <span className="badge badge-secondary" style={{ fontSize: '0.72rem' }}>
                  {activeTask.atm_id}
                </span>
              )}
              <span className="badge badge-good">
                {activeTask.processing_fps || 24} FPS Active
              </span>
            </div>
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
              width: `${activeTask.progress || 0}%`,
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
            color: 'var(--text-secondary)',
            flexWrap: 'wrap',
            gap: '8px'
          }}>
            <span>Progress: {activeTask.progress || 0}%</span>
            <span>Frame: {activeTask.current_frame || 0} / {activeTask.total_frames || '...'}</span>
            <span>Persons Discovered: {activeTask.tracks_count || 0}</span>
          </div>
        </div>
      )}

      {/* Failed Task Error Banner */}
      {activeTask?.status === 'failed' && (
        <div className="glass-panel" style={{
          padding: '20px 24px',
          marginTop: '20px',
          border: '1px solid rgba(244, 63, 94, 0.4)',
          backgroundColor: 'rgba(244, 63, 94, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <AlertCircle size={24} color="#f43f5e" />
            <div>
              <h4 style={{ color: 'var(--text-primary)', fontSize: '1rem', fontWeight: 700 }}>Processing Error ({activeTask.filename})</h4>
              <p style={{ color: '#fb7185', fontSize: '0.825rem' }}>
                {activeTask.error || 'Video could not be processed. Please try again with another video sequence.'}
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              setTasks(prev => {
                const copy = { ...prev };
                delete copy[activeTaskId];
                return copy;
              });
              setActiveTaskId(null);
            }}
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '8px 16px' }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Completed Results Summary Banner */}
      {activeTask?.status === 'completed' && activeTask.result && (
        <div className="glass-panel" style={{
          padding: '24px',
          marginTop: '20px',
          marginBottom: '28px',
          border: '1px solid rgba(16, 185, 129, 0.35)',
          background: 'linear-gradient(180deg, rgba(16, 185, 129, 0.08) 0%, var(--bg-card) 100%)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <CheckCircle2 size={24} color="var(--accent-emerald)" />
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    Analysis Completed: {activeTask.filename}
                  </h3>
                  {activeTask.result?.metadata?.atm_id && (
                    <span className="badge badge-secondary" style={{ fontSize: '0.72rem' }}>
                      📍 {activeTask.result.metadata.location_name || activeTask.result.metadata.atm_id}
                    </span>
                  )}
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  Processed {activeTask.result.metadata?.frames_processed} frames in {activeTask.result.metadata?.elapsed_time_sec}s
                  {activeTask.result.metadata?.window_applied && (
                    <span style={{ color: 'var(--accent-cyan)', marginLeft: '6px' }}>
                      (Targeted window: {activeTask.result.metadata.window_start_s}s - {activeTask.result.metadata.window_end_s}s)
                    </span>
                  )}
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <span className="badge badge-excellent">
                {activeTask.result.summary?.unique_persons_tracked} Persons Tracked
              </span>
              <span className="badge badge-good">
                Avg Score: {activeTask.result.summary?.average_best_quality}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tracked Results Gallery */}
      <div style={{ marginTop: '24px' }}>
        <TrackResults
          tracks={activeTask?.result?.tracks || []}
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
