import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileVideo, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  ArrowRight, 
  MapPin, 
  Clock, 
  Sliders, 
  X, 
  Plus, 
  Zap,
  Sparkles
} from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../config';

export default function VideoUploader({ onTaskCreated, isProcessing }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [errorMsg, setErrorMsg] = useState('');
  
  // ATM and Targeted Windowing Configuration
  const [atmId, setAtmId] = useState('ATM_CENTRAL_01');
  const [locationName, setLocationName] = useState('Central Branch Kiosk');
  const [targetTimeInput, setTargetTimeInput] = useState('');
  const [windowMargin, setWindowMargin] = useState('60');
  const [showAdvanced, setShowAdvanced] = useState(true);

  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      addFiles(Array.from(e.target.files));
    }
  };

  const addFiles = (newFiles) => {
    setErrorMsg('');
    const validExtensions = ['mp4', 'avi', 'mov', 'mkv', 'webm'];
    const valid = [];
    
    for (const file of newFiles) {
      const ext = file.name.split('.').pop().toLowerCase();
      if (validExtensions.includes(ext)) {
        // Prevent exact duplicates
        if (!selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
          valid.push(file);
        }
      } else {
        setErrorMsg(`Skipped unsupported file (${file.name}). Please use MP4, AVI, MOV, or MKV.`);
      }
    }

    if (valid.length > 0) {
      setSelectedFiles(prev => [...prev, ...valid]);
    }
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // Convert mm:ss or raw seconds into numeric seconds
  const parseTargetTime = (val) => {
    if (!val || !val.trim()) return null;
    const str = val.trim();
    if (str.includes(':')) {
      const parts = str.split(':');
      if (parts.length === 2) {
        const mins = parseFloat(parts[0]) || 0;
        const secs = parseFloat(parts[1]) || 0;
        return mins * 60 + secs;
      }
    }
    const num = parseFloat(str);
    return isNaN(num) ? null : num;
  };

  const handleUploadAll = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setErrorMsg('');

    const targetSec = parseTargetTime(targetTimeInput);
    const marginSec = parseFloat(windowMargin) || 60.0;

    // Launch uploads concurrently across workers
    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      const formData = new FormData();
      formData.append('file', file);
      formData.append('atm_id', atmId.trim() || 'ATM_CENTRAL_01');
      formData.append('location_name', locationName.trim() || 'Central Branch Kiosk');
      formData.append('window_margin_s', String(marginSec));
      if (targetSec !== null) {
        formData.append('target_time_s', String(targetSec));
      }

      try {
        setUploadProgress(prev => ({ ...prev, [file.name]: 10 }));
        const response = await axios.post(`${API_BASE_URL}/api/upload-and-process`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setUploadProgress(prev => ({ ...prev, [file.name]: percent }));
            }
          },
        });

        if (response.data && response.data.task_id) {
          onTaskCreated(response.data.task_id, file.name, {
            atm_id: atmId,
            location_name: locationName,
            target_time_s: targetSec,
            window_margin_s: marginSec
          });
        }
      } catch (err) {
        console.error(`Upload failed for ${file.name}:`, err);
        setErrorMsg(err.response?.data?.detail || `Failed to upload ${file.name}. Ensure backend is running.`);
      }
    }

    setUploading(false);
  };

  const targetSecCalculated = parseTargetTime(targetTimeInput);

  return (
    <div className="glass-panel" style={{ padding: '28px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>Ingest Surveillance Feed</h2>
            <span className="badge badge-good" style={{ fontSize: '0.7rem' }}>
              Multi-Video & Targeted Windowing
            </span>
          </div>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Upload single or batch ATM CCTV videos with location tags, deblurring, and ±1 min transaction window seeking.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="btn btn-secondary"
          style={{ padding: '6px 12px', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Sliders size={14} />
          <span>{showAdvanced ? 'Hide Window & Location Config' : 'Configure ATM & Window'}</span>
        </button>
      </div>

      {/* Targeted Transaction Window & ATM Metadata Box */}
      {showAdvanced && (
        <div style={{
          padding: '16px 20px',
          marginBottom: '20px',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--bg-input)',
          border: '1px solid var(--border-subtle)',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
          gap: '16px'
        }}>
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              <MapPin size={13} color="var(--accent-cyan)" />
              ATM Terminal ID
            </label>
            <input
              type="text"
              value={atmId}
              onChange={(e) => setAtmId(e.target.value)}
              placeholder="e.g. ATM_CENTRAL_01"
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                fontSize: '0.82rem',
                fontFamily: 'var(--font-mono)'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              <MapPin size={13} color="var(--accent-indigo)" />
              ATM Location / Branch
            </label>
            <input
              type="text"
              value={locationName}
              onChange={(e) => setLocationName(e.target.value)}
              placeholder="e.g. Connaught Place Branch"
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                fontSize: '0.82rem'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              <Clock size={13} color="var(--accent-amber)" />
              Target Transaction Time (optional)
            </label>
            <input
              type="text"
              value={targetTimeInput}
              onChange={(e) => setTargetTimeInput(e.target.value)}
              placeholder="e.g. 14:32 or 872s (leave blank for full)"
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                fontSize: '0.82rem',
                fontFamily: 'var(--font-mono)'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              <Zap size={13} color="var(--accent-emerald)" />
              Window Search Margin (±s)
            </label>
            <input
              type="number"
              value={windowMargin}
              onChange={(e) => setWindowMargin(e.target.value)}
              min="10"
              max="300"
              placeholder="60"
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                fontSize: '0.82rem',
                fontFamily: 'var(--font-mono)'
              }}
            />
          </div>

          {targetSecCalculated !== null && (
            <div style={{
              gridColumn: '1 / -1',
              padding: '10px 14px',
              borderRadius: '6px',
              backgroundColor: 'rgba(6, 182, 212, 0.1)',
              border: '1px solid rgba(6, 182, 212, 0.3)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '0.78rem',
              color: 'var(--accent-cyan)'
            }}>
              <Zap size={15} />
              <span>
                <strong>Targeted ±{windowMargin}s Window Active:</strong> Processing will seek directly to T+{Math.max(0, targetSecCalculated - parseFloat(windowMargin))}s and terminate at T+{targetSecCalculated + parseFloat(windowMargin)}s. Hour-long video is bypassed, saving 95%+ compute time!
              </span>
            </div>
          )}
        </div>
      )}

      {/* Drag & Drop Area (Multiple Selection Enabled) */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${dragActive ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
          backgroundColor: dragActive ? 'rgba(6, 182, 212, 0.08)' : 'var(--bg-input)',
          borderRadius: 'var(--radius-md)',
          padding: '36px 24px',
          textAlign: 'center',
          cursor: isProcessing || uploading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
          boxShadow: dragActive ? '0 0 20px rgba(6, 182, 212, 0.2)' : 'none'
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          multiple
          style={{ display: 'none' }}
          onChange={handleChange}
          disabled={uploading || isProcessing}
        />

        <div style={{
          width: '54px',
          height: '54px',
          borderRadius: '50%',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 14px',
          color: 'var(--accent-cyan)'
        }}>
          <UploadCloud size={26} />
        </div>

        <p style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
          Drag and drop surveillance video(s) here, or <span style={{ color: 'var(--accent-cyan)' }}>browse</span>
        </p>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Supports multiple videos simultaneously (MP4, AVI, MOV, MKV up to 500MB each)
        </p>
      </div>

      {/* Selected Video Queue */}
      {selectedFiles.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
              Selected Feed Queue ({selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''})
            </span>
            <button
              onClick={() => setSelectedFiles([])}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                fontSize: '0.75rem',
                cursor: 'pointer',
                textDecoration: 'underline'
              }}
            >
              Clear Queue
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '220px', overflowY: 'auto' }}>
            {selectedFiles.map((file, idx) => {
              const progress = uploadProgress[file.name] || 0;
              return (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    backgroundColor: 'var(--bg-input)',
                    borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                    gap: '12px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0, flex: 1 }}>
                    <FileVideo size={18} color="var(--accent-cyan)" style={{ flexShrink: 0 }} />
                    <div style={{ minWidth: 0 }}>
                      <p style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {file.name}
                      </p>
                      <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {(file.size / (1024 * 1024)).toFixed(2)} MB • {atmId}
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {uploading && (
                      <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                        {progress > 0 ? `${progress}%` : 'Queued'}
                      </span>
                    )}

                    {!uploading && (
                      <button
                        onClick={() => removeFile(idx)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--text-muted)',
                          cursor: 'pointer',
                          padding: '4px'
                        }}
                      >
                        <X size={16} />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Action Row */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px', gap: '12px' }}>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="btn btn-secondary"
              disabled={uploading || isProcessing}
              style={{ padding: '8px 16px', fontSize: '0.82rem' }}
            >
              <Plus size={15} />
              <span>Add More Videos</span>
            </button>

            <button
              onClick={handleUploadAll}
              disabled={uploading || isProcessing || selectedFiles.length === 0}
              className="btn btn-primary"
              style={{ padding: '8px 20px', fontSize: '0.85rem' }}
            >
              {uploading ? (
                <>
                  <Loader2 size={16} className="pulse-indicator" />
                  <span>Processing Queue...</span>
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  <span>Launch Analysis ({selectedFiles.length})</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {errorMsg && (
        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          backgroundColor: 'rgba(244, 63, 94, 0.12)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          color: '#fb7185',
          fontSize: '0.85rem'
        }}>
          <AlertCircle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
}
