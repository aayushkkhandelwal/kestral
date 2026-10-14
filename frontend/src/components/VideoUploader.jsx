import React, { useState, useRef } from 'react';
import { UploadCloud, FileVideo, CheckCircle2, AlertCircle, Loader2, ArrowRight } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../config';

export default function VideoUploader({ onTaskCreated, isProcessing }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState('');
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
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file) => {
    setErrorMsg('');
    const validExtensions = ['mp4', 'avi', 'mov', 'mkv', 'webm'];
    const ext = file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(ext)) {
      setErrorMsg(`Unsupported format (.${ext}). Please select an MP4, MOV, AVI, or MKV file.`);
      return;
    }
    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);
    setErrorMsg('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/upload-and-process`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percent);
          }
        },
      });

      if (response.data && response.data.task_id) {
        onTaskCreated(response.data.task_id, selectedFile.name);
      }
    } catch (err) {
      console.error('Upload failed:', err);
      setErrorMsg(err.response?.data?.detail || 'Failed to upload video to engine. Is backend running on port 8000?');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '28px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fff' }}>Ingest Surveillance Feed</h2>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
            Upload video sequence for multi-object tracking and biometric best-frame extraction
          </p>
        </div>

        <span className="badge badge-good">
          YOLOv8 + Cascade Engine
        </span>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${dragActive ? 'var(--accent-cyan)' : 'rgba(255, 255, 255, 0.14)'}`,
          backgroundColor: dragActive ? 'rgba(6, 182, 212, 0.05)' : 'rgba(0, 0, 0, 0.25)',
          borderRadius: 'var(--radius-md)',
          padding: '40px 24px',
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
          style={{ display: 'none' }}
          onChange={handleChange}
          disabled={uploading || isProcessing}
        />

        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 16px',
          color: 'var(--accent-cyan)'
        }}>
          <UploadCloud size={28} />
        </div>

        <p style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff', marginBottom: '6px' }}>
          Drag and drop surveillance video here, or <span style={{ color: 'var(--accent-cyan)' }}>browse</span>
        </p>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Supports MP4, AVI, MOV, MKV up to 500MB (Automatic frame stride: 2)
        </p>
      </div>

      {/* Selected File Card */}
      {selectedFile && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: '16px',
          padding: '14px 18px',
          backgroundColor: 'rgba(255, 255, 255, 0.03)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <FileVideo size={22} color="var(--accent-cyan)" />
            <div>
              <p style={{ fontSize: '0.875rem', fontWeight: 600, color: '#fff' }}>
                {selectedFile.name}
              </p>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready for processing
              </p>
            </div>
          </div>

          <button
            onClick={handleUpload}
            disabled={uploading || isProcessing}
            className="btn btn-primary"
            style={{ padding: '8px 18px' }}
          >
            {uploading ? (
              <>
                <Loader2 size={16} className="pulse-indicator" />
                <span>Uploading ({uploadProgress}%)</span>
              </>
            ) : (
              <>
                <span>Launch Analysis</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>
      )}

      {/* Upload Progress Bar */}
      {uploading && (
        <div style={{ marginTop: '14px' }}>
          <div style={{
            height: '6px',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '999px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${uploadProgress}%`,
              height: '100%',
              background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-indigo))',
              transition: 'width 0.2s ease'
            }} />
          </div>
        </div>
      )}

      {/* Error Message */}
      {errorMsg && (
        <div style={{
          marginTop: '14px',
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
