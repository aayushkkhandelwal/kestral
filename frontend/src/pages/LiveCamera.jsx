import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { 
  Camera, 
  CameraOff, 
  Play, 
  Square, 
  Activity, 
  Clock, 
  Users, 
  Smile, 
  AlertTriangle, 
  ShieldCheck, 
  Settings, 
  RotateCcw, 
  Volume2, 
  VolumeX, 
  CheckCircle2, 
  Sparkles,
  Info,
  Maximize2
} from 'lucide-react';
import { API_BASE_URL } from '../config';

/**
 * Web Audio API synthesizer for clean 15-second alert chime
 */
function playAlertChime() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880.00, ctx.currentTime + 0.15); // A5
    osc.frequency.exponentialRampToValueAtTime(1174.66, ctx.currentTime + 0.35); // D6

    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + 0.65);
  } catch (e) {
    // Audio context may be restricted by browser autoplay policy before user gesture
  }
}

/**
 * Formats seconds into MM:SS format
 */
function formatDuration(seconds) {
  if (!seconds || seconds < 0) return '00:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

export default function LiveCamera() {
  // Camera & Stream State
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraStatus, setCameraStatus] = useState('idle'); // 'idle' | 'starting' | 'live' | 'error'
  const [errorMessage, setErrorMessage] = useState(null);
  const [errorType, setErrorType] = useState(null);

  // Real-time Detection Telemetry
  const [peopleCount, setPeopleCount] = useState(0);
  const [facesCount, setFacesCount] = useState(0);
  const [activeTracksList, setActiveTracksList] = useState([]);
  const [bannerAlert, setBannerAlert] = useState(null);
  const [detectionHistory, setDetectionHistory] = useState([]);

  // Performance & Hardware Telemetry
  const [latencyMs, setLatencyMs] = useState(0);
  const [detectionFps, setDetectionFps] = useState(0);
  const [streamResolution, setStreamResolution] = useState(null);

  // Configurable Settings
  const [inferenceInterval, setInferenceInterval] = useState(600); // ms
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.35);
  const [faceThreshold, setFaceThreshold] = useState(0.35);
  const [gracePeriod, setGracePeriod] = useState(1.5); // seconds
  const [showLandmarks, setShowLandmarks] = useState(true);
  const [showBoxes, setShowBoxes] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [showSettings, setShowSettings] = useState(false);

  // Context & LAN Diagnostics
  const isSecureContext = typeof window !== 'undefined' ? window.isSecureContext : true;
  const isLocalhost = typeof window !== 'undefined' 
    ? (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    : true;

  // DOM & Pipeline Refs
  const videoRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const offscreenCanvasRef = useRef(null);
  const streamRef = useRef(null);
  const isInferringRef = useRef(false);
  const animFrameIdRef = useRef(null);
  const intervalTimerRef = useRef(null);

  // Temporal Tracking Registry
  // Map of trackId -> { trackId, firstSeen, lastSeen, alertTriggered, bbox, confidence, faceBbox, faceConfidence, landmarks }
  const trackerRegistryRef = useRef(new Map());
  const latestDetectionsRef = useRef({ people: [], faces: [] });
  const latencyHistoryRef = useRef([]);

  // ========================================================
  // Camera Life-Cycle Management
  // ========================================================
  const startCamera = async () => {
    setErrorMessage(null);
    setErrorType(null);
    setCameraStatus('starting');

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraStatus('error');
      setErrorType('unsupported');
      setErrorMessage(
        'Webcam access (navigator.mediaDevices.getUserMedia) is not supported in this browser or context. Note: On LAN HTTP connections, browsers require HTTPS or localhost for camera permissions.'
      );
      return;
    }

    try {
      const constraints = {
        video: {
          width: { ideal: 1280, max: 1920 },
          height: { ideal: 720, max: 1080 },
          facingMode: 'user'
        },
        audio: false
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play().then(() => {
            setCameraActive(true);
            setCameraStatus('live');
            setStreamResolution({
              width: videoRef.current.videoWidth,
              height: videoRef.current.videoHeight
            });
          }).catch(err => {
            console.error('[LiveCamera] Play error:', err);
          });
        };
      }
    } catch (err) {
      console.error('[LiveCamera] Camera access failed:', err);
      setCameraStatus('error');
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setErrorType('permission');
        setErrorMessage('Camera permission was denied. Please allow camera access in your browser settings and try again.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setErrorType('notFound');
        setErrorMessage('No camera device was detected on your laptop or system. Please verify camera hardware connection.');
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setErrorType('inUse');
        setErrorMessage('Camera is currently in use by another application (e.g. Zoom, Teams, or another tab). Please release the device and retry.');
      } else if (err.name === 'OverconstrainedError') {
        setErrorType('overconstrained');
        setErrorMessage('Requested camera resolution could not be satisfied by hardware.');
      } else {
        setErrorType('generic');
        setErrorMessage(`Unable to initialize camera: ${err.message || 'Unknown error'}`);
      }
    }
  };

  const stopCamera = useCallback(async () => {
    // 1. Terminate all hardware tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch (e) {
          console.warn('Track stop error:', e);
        }
      });
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    // 2. Clear timers and animation loops
    if (intervalTimerRef.current) {
      clearInterval(intervalTimerRef.current);
      intervalTimerRef.current = null;
    }
    if (animFrameIdRef.current) {
      cancelAnimationFrame(animFrameIdRef.current);
      animFrameIdRef.current = null;
    }

    // 3. Clear canvas overlay
    if (overlayCanvasRef.current) {
      const ctx = overlayCanvasRef.current.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, overlayCanvasRef.current.width, overlayCanvasRef.current.height);
      }
    }

    // 4. Reset tracker on backend
    try {
      await axios.post(`${API_BASE_URL}/api/camera/reset`, {}, { timeout: 2000 });
    } catch (e) {
      // Backend may be offline or resetting
    }

    // 5. Reset local tracker registry & status
    trackerRegistryRef.current.clear();
    latestDetectionsRef.current = { people: [], faces: [] };
    isInferringRef.current = false;
    setActiveTracksList([]);
    setPeopleCount(0);
    setFacesCount(0);
    setCameraActive(false);
    setCameraStatus('idle');
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  // ========================================================
  // Real-Time Frame Sampling & Inference Cycle
  // ========================================================
  const sampleAndDetectFrame = useCallback(async () => {
    if (!cameraActive || isInferringRef.current || !videoRef.current) return;
    if (videoRef.current.readyState < 2) return; // HAVE_CURRENT_DATA

    const video = videoRef.current;
    const vw = video.videoWidth;
    const vh = video.videoHeight;
    if (!vw || !vh) return;

    // Offscreen canvas setup
    if (!offscreenCanvasRef.current) {
      offscreenCanvasRef.current = document.createElement('canvas');
    }
    const offCanvas = offscreenCanvasRef.current;
    
    // Scale frame for fast LAN/laptop transmission (max 640px)
    const maxDim = 640;
    const scale = Math.min(1.0, maxDim / Math.max(vw, vh));
    const targetW = Math.round(vw * scale);
    const targetH = Math.round(vh * scale);

    offCanvas.width = targetW;
    offCanvas.height = targetH;
    const offCtx = offCanvas.getContext('2d');
    if (!offCtx) return;

    offCtx.drawImage(video, 0, 0, targetW, targetH);

    // Convert to JPEG Blob
    offCanvas.toBlob(async (blob) => {
      if (!blob) return;

      isInferringRef.current = true;
      const tStart = performance.now();

      try {
        const formData = new FormData();
        formData.append('file', blob, 'frame.jpg');

        const res = await axios.post(
          `${API_BASE_URL}/api/camera/detect?conf_threshold=${confidenceThreshold}&face_conf_threshold=${faceThreshold}`,
          formData,
          {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 5000
          }
        );

        const data = res.data;
        const roundTripMs = Math.round(performance.now() - tStart);

        // Update latency history and FPS
        setLatencyMs(data.processing_time_ms || roundTripMs);
        latencyHistoryRef.current.push(roundTripMs);
        if (latencyHistoryRef.current.length > 8) latencyHistoryRef.current.shift();
        const avgCycle = latencyHistoryRef.current.reduce((a, b) => a + b, 0) / latencyHistoryRef.current.length;
        const computedFps = Math.min(30, Math.round((1000 / Math.max(1, avgCycle + inferenceInterval)) * 10) / 10);
        setDetectionFps(computedFps);

        // Map normalized coordinates from scaled frame back to original video resolution
        const invScale = 1.0 / scale;
        const mappedPeople = (data.people || []).map(p => ({
          ...p,
          bbox: [
            Math.round(p.bbox[0] * invScale),
            Math.round(p.bbox[1] * invScale),
            Math.round(p.bbox[2] * invScale),
            Math.round(p.bbox[3] * invScale),
          ],
          face_bbox: p.face_bbox ? [
            Math.round(p.face_bbox[0] * invScale),
            Math.round(p.face_bbox[1] * invScale),
            Math.round(p.face_bbox[2] * invScale),
            Math.round(p.face_bbox[3] * invScale),
          ] : null,
          landmarks: (p.landmarks || []).map(pt => [
            Math.round(pt[0] * invScale),
            Math.round(pt[1] * invScale)
          ])
        }));

        const mappedFaces = (data.faces || []).map(f => ({
          ...f,
          bbox: [
            Math.round(f.bbox[0] * invScale),
            Math.round(f.bbox[1] * invScale),
            Math.round(f.bbox[2] * invScale),
            Math.round(f.bbox[3] * invScale),
          ],
          landmarks: (f.landmarks || []).map(pt => [
            Math.round(pt[0] * invScale),
            Math.round(pt[1] * invScale)
          ])
        }));

        latestDetectionsRef.current = { people: mappedPeople, faces: mappedFaces };
        setPeopleCount(mappedPeople.length);
        setFacesCount(mappedFaces.length);

        // Update 15-second tracking state machine
        const nowSec = Date.now() / 1000;
        const currentSeenIds = new Set();

        mappedPeople.forEach(person => {
          const tid = person.track_id;
          currentSeenIds.add(tid);

          const existing = trackerRegistryRef.current.get(tid);
          if (!existing) {
            // New tracked person
            trackerRegistryRef.current.set(tid, {
              trackId: tid,
              firstSeenTime: nowSec,
              lastSeenTime: nowSec,
              continuousSeconds: 0.0,
              alertTriggered: false,
              status: 'active',
              confidence: person.confidence,
              bbox: person.bbox,
              faceBbox: person.face_bbox,
              faceConfidence: person.face_confidence,
              landmarks: person.landmarks || []
            });
          } else {
            // Existing track: Check grace period
            const gap = nowSec - existing.lastSeenTime;
            if (gap <= gracePeriod) {
              existing.lastSeenTime = nowSec;
              existing.status = 'active';
              existing.confidence = person.confidence;
              existing.bbox = person.bbox;
              existing.faceBbox = person.face_bbox;
              existing.faceConfidence = person.face_confidence;
              existing.landmarks = person.landmarks || [];
              existing.continuousSeconds = nowSec - existing.firstSeenTime;

              // Check 15-second trigger condition
              if (existing.continuousSeconds >= 15.0 && !existing.alertTriggered) {
                existing.alertTriggered = true;

                // 15-second alert event payload
                const eventObj = {
                  id: `EVT-${Date.now().toString().slice(-6)}`,
                  trackId: tid,
                  startTime: new Date(existing.firstSeenTime * 1000).toLocaleTimeString(),
                  alertTime: new Date(nowSec * 1000).toLocaleTimeString(),
                  durationSec: Math.floor(existing.continuousSeconds),
                  confidence: person.confidence,
                  hasFace: Boolean(person.face_bbox),
                  faceConfidence: person.face_confidence
                };

                setDetectionHistory(prev => [eventObj, ...prev.slice(0, 49)]);
                setBannerAlert(eventObj);

                if (soundEnabled) {
                  playAlertChime();
                }
              }
            } else {
              // Absent beyond grace period: Reset visibility timer for this track!
              existing.firstSeenTime = nowSec;
              existing.lastSeenTime = nowSec;
              existing.continuousSeconds = 0.0;
              existing.alertTriggered = false;
              existing.status = 'active';
              existing.bbox = person.bbox;
              existing.faceBbox = person.face_bbox;
            }
          }
        });

        // Handle absent tracks beyond grace period
        for (const [tid, item] of trackerRegistryRef.current.entries()) {
          if (!currentSeenIds.has(tid)) {
            const timeSinceSeen = nowSec - item.lastSeenTime;
            if (timeSinceSeen > gracePeriod) {
              item.status = 'expired';
              // Cleanup expired tracks after 4 seconds
              if (timeSinceSeen > gracePeriod + 4.0) {
                trackerRegistryRef.current.delete(tid);
              }
            } else {
              item.status = 'grace';
            }
          }
        }

      } catch (err) {
        console.warn('[LiveCamera] Detection request error:', err.message);
      } finally {
        isInferringRef.current = false;
      }
    }, 'image/jpeg', 0.85);
  }, [cameraActive, confidenceThreshold, faceThreshold, gracePeriod, inferenceInterval, soundEnabled]);

  // Set up sampling interval
  useEffect(() => {
    if (!cameraActive) {
      if (intervalTimerRef.current) {
        clearInterval(intervalTimerRef.current);
        intervalTimerRef.current = null;
      }
      return;
    }

    intervalTimerRef.current = setInterval(sampleAndDetectFrame, inferenceInterval);
    return () => {
      if (intervalTimerRef.current) {
        clearInterval(intervalTimerRef.current);
        intervalTimerRef.current = null;
      }
    };
  }, [cameraActive, inferenceInterval, sampleAndDetectFrame]);

  // ========================================================
  // Canvas Overlay Drawing Loop (60 FPS Native Sync)
  // ========================================================
  const drawOverlay = useCallback(() => {
    const video = videoRef.current;
    const canvas = overlayCanvasRef.current;
    if (!video || !canvas || !cameraActive) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Match canvas dimensions to video element display size
    const displayW = video.clientWidth;
    const displayH = video.clientHeight;
    const videoW = video.videoWidth || 1280;
    const videoH = video.videoHeight || 720;

    if (canvas.width !== displayW || canvas.height !== displayH) {
      canvas.width = displayW;
      canvas.height = displayH;
    }

    ctx.clearRect(0, 0, displayW, displayH);

    // Compute coordinate mapping scale (contain / letterbox preservation)
    const scaleX = displayW / videoW;
    const scaleY = displayH / videoH;

    const nowSec = Date.now() / 1000;
    const currentActiveList = [];

    // 1. Draw Person Bounding Boxes
    if (showBoxes) {
      for (const [tid, track] of trackerRegistryRef.current.entries()) {
        const timeSinceSeen = nowSec - track.lastSeenTime;
        if (timeSinceSeen > gracePeriod) continue; // Don't draw expired tracks

        const isAlerted = track.alertTriggered;
        const elapsedSec = Math.max(0, nowSec - track.firstSeenTime);
        const timerText = formatDuration(elapsedSec);

        currentActiveList.push({
          trackId: tid,
          elapsedSec,
          timerText,
          isAlerted,
          confidence: track.confidence,
          hasFace: Boolean(track.faceBbox),
          faceConfidence: track.faceConfidence,
          status: track.status
        });

        const [px1, py1, px2, py2] = track.bbox;
        const x = px1 * scaleX;
        const y = py1 * scaleY;
        const w = (px2 - px1) * scaleX;
        const h = (py2 - py1) * scaleY;

        // Styling: Crimson/Rose alert glow if 15s reached; Cyan cyber-box otherwise
        ctx.save();
        if (isAlerted) {
          ctx.strokeStyle = '#f43f5e';
          ctx.lineWidth = 3.0;
          ctx.shadowColor = 'rgba(244, 63, 94, 0.7)';
          ctx.shadowBlur = 16;
        } else {
          ctx.strokeStyle = '#06b6d4';
          ctx.lineWidth = 2.0;
          ctx.shadowColor = 'rgba(6, 182, 212, 0.4)';
          ctx.shadowBlur = 8;
        }

        // Draw modern corner-bracketed bounding box
        const cornerLen = Math.min(24, w * 0.25, h * 0.25);
        ctx.beginPath();
        // Top-left
        ctx.moveTo(x, y + cornerLen);
        ctx.lineTo(x, y);
        ctx.lineTo(x + cornerLen, y);
        // Top-right
        ctx.moveTo(x + w - cornerLen, y);
        ctx.lineTo(x + w, y);
        ctx.lineTo(x + w, y + cornerLen);
        // Bottom-right
        ctx.moveTo(x + w, y + h - cornerLen);
        ctx.lineTo(x + w, y + h);
        ctx.lineTo(x + w - cornerLen, y + h);
        // Bottom-left
        ctx.moveTo(x + cornerLen, y + h);
        ctx.lineTo(x, y + h);
        ctx.lineTo(x, y + h - cornerLen);
        ctx.stroke();

        // Subtle semi-transparent full outline
        ctx.lineWidth = 1.0;
        ctx.globalAlpha = 0.45;
        ctx.strokeRect(x, y, w, h);
        ctx.globalAlpha = 1.0;

        // Bounding Box Header Pill
        const headerText = `ID #${tid}  ⏱ ${timerText}  ${Math.round(track.confidence * 100)}%`;
        ctx.font = '600 12px "JetBrains Mono", monospace';
        const textMetrics = ctx.measureText(headerText);
        const pillW = textMetrics.width + 16;
        const pillH = 22;
        const pillY = Math.max(4, y - pillH - 4);

        // Header background
        ctx.fillStyle = isAlerted ? 'rgba(225, 29, 72, 0.92)' : 'rgba(15, 23, 42, 0.88)';
        ctx.beginPath();
        ctx.roundRect(x, pillY, pillW, pillH, 5);
        ctx.fill();

        ctx.strokeStyle = isAlerted ? '#fb7185' : 'rgba(6, 182, 212, 0.5)';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Header text
        ctx.fillStyle = '#ffffff';
        ctx.fillText(headerText, x + 8, pillY + 15);

        // If alert triggered: Alert banner pill under box
        if (isAlerted) {
          const alertPillText = '🚨 15s PERSISTENT TARGET';
          const alertW = ctx.measureText(alertPillText).width + 16;
          ctx.fillStyle = 'rgba(244, 63, 94, 0.95)';
          ctx.beginPath();
          ctx.roundRect(x, y + h + 4, alertW, 20, 4);
          ctx.fill();
          ctx.fillStyle = '#fff';
          ctx.fillText(alertPillText, x + 8, y + h + 18);
        }

        ctx.restore();
      }
    }

    // 2. Draw Face Bounding Boxes & Facial Landmarks
    const latestFaces = latestDetectionsRef.current.faces || [];
    if (showBoxes) {
      latestFaces.forEach(face => {
        const [fx1, fy1, fx2, fy2] = face.bbox;
        const fx = fx1 * scaleX;
        const fy = fy1 * scaleY;
        const fw = (fx2 - fx1) * scaleX;
        const fh = (fy2 - fy1) * scaleY;

        ctx.save();
        ctx.strokeStyle = '#10b981'; // Emerald
        ctx.lineWidth = 1.8;
        ctx.shadowColor = 'rgba(16, 185, 129, 0.4)';
        ctx.shadowBlur = 6;
        ctx.strokeRect(fx, fy, fw, fh);

        // Face tag
        const fText = `FACE ${Math.round(face.confidence * 100)}%`;
        ctx.font = '500 10px "JetBrains Mono", monospace';
        const fMetrics = ctx.measureText(fText);
        ctx.fillStyle = 'rgba(6, 78, 59, 0.9)';
        ctx.fillRect(fx, Math.max(0, fy - 16), fMetrics.width + 10, 16);
        ctx.fillStyle = '#34d399';
        ctx.fillText(fText, fx + 5, Math.max(0, fy - 16) + 12);
        ctx.restore();

        // 3. Draw 5-Point Facial Landmarks (Eyes, Nose, Mouth Corners)
        if (showLandmarks && face.landmarks && face.landmarks.length >= 5) {
          ctx.save();
          face.landmarks.forEach((pt, idx) => {
            const lx = pt[0] * scaleX;
            const ly = pt[1] * scaleY;

            ctx.fillStyle = idx < 2 ? '#38bdf8' : (idx === 2 ? '#f59e0b' : '#34d399');
            ctx.shadowColor = 'rgba(255, 255, 255, 0.8)';
            ctx.shadowBlur = 6;
            ctx.beginPath();
            ctx.arc(lx, ly, 3.2, 0, 2 * Math.PI);
            ctx.fill();

            // Subtle outer ring
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.7)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(lx, ly, 5.0, 0, 2 * Math.PI);
            ctx.stroke();
          });
          ctx.restore();
        }
      });
    }

    // Sort active tracks by trackId
    currentActiveList.sort((a, b) => a.trackId - b.trackId);
    setActiveTracksList(currentActiveList);

    // Continue animation loop
    animFrameIdRef.current = requestAnimationFrame(drawOverlay);
  }, [cameraActive, gracePeriod, showBoxes, showLandmarks]);

  useEffect(() => {
    if (cameraActive) {
      animFrameIdRef.current = requestAnimationFrame(drawOverlay);
    }
    return () => {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
        animFrameIdRef.current = null;
      }
    };
  }, [cameraActive, drawOverlay]);

  // Reset local and backend tracker
  const handleResetTracker = async () => {
    trackerRegistryRef.current.clear();
    latestDetectionsRef.current = { people: [], faces: [] };
    setActiveTracksList([]);
    try {
      await axios.post(`${API_BASE_URL}/api/camera/reset`);
    } catch (e) {
      console.warn('Backend reset error:', e);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.03em' }}>
              Live Camera Intelligence
            </h1>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              background: cameraActive ? 'rgba(16, 185, 129, 0.15)' : 'rgba(148, 163, 184, 0.1)',
              border: `1px solid ${cameraActive ? 'rgba(16, 185, 129, 0.3)' : 'rgba(148, 163, 184, 0.2)'}`,
              borderRadius: '999px',
              fontSize: '0.75rem',
              fontWeight: 700,
              color: cameraActive ? '#34d399' : 'var(--text-muted)'
            }}>
              <span style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: cameraActive ? '#10b981' : '#64748b',
                boxShadow: cameraActive ? '0 0 10px #10b981' : 'none'
              }} />
              {cameraActive ? 'FEED LIVE' : 'CAMERA OFF'}
            </span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Real-time laptop webcam tracking, 5-point neural face landmarks & 15-second continuous persistence detection
          </p>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="btn"
            style={{
              padding: '9px 14px',
              fontSize: '0.825rem',
              background: showSettings ? 'rgba(6, 182, 212, 0.15)' : 'rgba(255, 255, 255, 0.05)',
              border: showSettings ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
              color: showSettings ? 'var(--accent-cyan)' : '#fff'
            }}
          >
            <Settings size={15} />
            <span>Config</span>
          </button>

          <button
            onClick={handleResetTracker}
            disabled={!cameraActive}
            className="btn"
            style={{
              padding: '9px 14px',
              fontSize: '0.825rem',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-subtle)',
              color: cameraActive ? 'var(--text-secondary)' : 'var(--text-muted)',
              cursor: cameraActive ? 'pointer' : 'not-allowed'
            }}
            title="Reset active track IDs and continuous visibility timers"
          >
            <RotateCcw size={15} />
            <span>Reset Tracks</span>
          </button>

          {!cameraActive ? (
            <button
              onClick={startCamera}
              className="btn btn-primary"
              style={{
                padding: '10px 22px',
                fontSize: '0.875rem',
                fontWeight: 700,
                boxShadow: '0 0 20px rgba(6, 182, 212, 0.35)'
              }}
            >
              <Camera size={18} />
              <span>Start Camera</span>
            </button>
          ) : (
            <button
              onClick={stopCamera}
              className="btn"
              style={{
                padding: '10px 22px',
                fontSize: '0.875rem',
                fontWeight: 700,
                backgroundColor: 'rgba(244, 63, 94, 0.15)',
                border: '1px solid rgba(244, 63, 94, 0.4)',
                color: '#fb7185'
              }}
            >
              <CameraOff size={18} />
              <span>Stop Camera</span>
            </button>
          )}
        </div>
      </div>

      {/* LAN Insecure Context Warning (if accessed over plain HTTP on LAN IP) */}
      {!isSecureContext && !isLocalhost && (
        <div style={{
          padding: '14px 18px',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '12px',
          color: '#fbbf24',
          fontSize: '0.825rem'
        }}>
          <Info size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <strong>Browser Security Notice (LAN HTTP):</strong> You are accessing Kestral over a local Wi-Fi IP (<code>{window.location.hostname}</code>) without HTTPS. Modern browsers (Chrome, Edge, Safari) restrict webcam permissions to secure contexts (<code>localhost</code> or <code>https://</code>). To access your webcam from this device:
            <ul style={{ marginTop: '6px', marginLeft: '16px', lineHeight: 1.6 }}>
              <li>Open Chrome on this device and navigate to <code>chrome://flags/#unsafely-treat-insecure-origin-as-secure</code></li>
              <li>Add <code>http://{window.location.host}</code> to the allowed origins list, enable the flag, and relaunch Chrome.</li>
            </ul>
          </div>
        </div>
      )}

      {/* Prominent 15-Second Detection Alert Toast / Banner */}
      {bannerAlert && (
        <div style={{
          padding: '16px 20px',
          background: 'linear-gradient(135deg, rgba(225, 29, 72, 0.25), rgba(15, 23, 42, 0.95))',
          border: '1px solid #f43f5e',
          borderRadius: 'var(--radius-md)',
          boxShadow: '0 0 30px rgba(244, 63, 94, 0.35)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          animation: 'pulseGlow 2s infinite ease-in-out',
          flexWrap: 'wrap',
          gap: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              backgroundColor: '#f43f5e',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px #f43f5e'
            }}>
              <AlertTriangle size={24} color="#ffffff" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '1rem', fontWeight: 800, color: '#ffffff', letterSpacing: '0.04em' }}>
                  PERSON DETECTED FOR 15 SECONDS
                </span>
                <span style={{
                  padding: '2px 8px',
                  backgroundColor: 'rgba(255, 255, 255, 0.15)',
                  borderRadius: '4px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  color: '#fecdd3'
                }}>
                  TRACK #{bannerAlert.trackId}
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#fda4af', marginTop: '2px' }}>
                Continuous visibility duration: <strong>{bannerAlert.durationSec}s</strong> | Triggered at: <strong>{bannerAlert.alertTime}</strong> | Target confidence: <strong>{Math.round(bannerAlert.confidence * 100)}%</strong>
              </p>
            </div>
          </div>

          <button
            onClick={() => setBannerAlert(null)}
            style={{
              padding: '6px 14px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: '#ffffff',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Dismiss Alert
          </button>
        </div>
      )}

      {/* Error Message Alert */}
      {errorMessage && (
        <div style={{
          padding: '14px 18px',
          backgroundColor: 'rgba(244, 63, 94, 0.12)',
          border: '1px solid rgba(244, 63, 94, 0.35)',
          borderRadius: 'var(--radius-md)',
          color: '#fb7185',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <AlertTriangle size={18} style={{ flexShrink: 0 }} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Settings Drawer / Flyout */}
      {showSettings && (
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Settings size={18} color="var(--accent-cyan)" />
              <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>
                Inference & Detection Calibration
              </h2>
            </div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Real-time parameter adjustments apply instantly
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
            {/* Interval Slider */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '6px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Inference Interval:</span>
                <span style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{inferenceInterval} ms</span>
              </div>
              <input
                type="range"
                min="300"
                max="2000"
                step="50"
                value={inferenceInterval}
                onChange={(e) => setInferenceInterval(Number(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
              />
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Slower = lower CPU/GPU load</span>
            </div>

            {/* Person Confidence Threshold */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '6px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Person Confidence:</span>
                <span style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{Math.round(confidenceThreshold * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.2"
                max="0.8"
                step="0.05"
                value={confidenceThreshold}
                onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
              />
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>YOLOv8 ByteTrack filtering</span>
            </div>

            {/* Face Confidence Threshold */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '6px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Face Confidence:</span>
                <span style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{Math.round(faceThreshold * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.2"
                max="0.8"
                step="0.05"
                value={faceThreshold}
                onChange={(e) => setFaceThreshold(Number(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
              />
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Deep Neural Net score</span>
            </div>

            {/* Grace Period */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '6px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Timer Grace Period:</span>
                <span style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{gracePeriod}s</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="3.0"
                step="0.5"
                value={gracePeriod}
                onChange={(e) => setGracePeriod(Number(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
              />
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Tolerates brief occlusion</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#fff', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={showBoxes}
                onChange={(e) => setShowBoxes(e.target.checked)}
                style={{ accentColor: 'var(--accent-cyan)' }}
              />
              <span>Display Bounding Boxes</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#fff', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={showLandmarks}
                onChange={(e) => setShowLandmarks(e.target.checked)}
                style={{ accentColor: 'var(--accent-cyan)' }}
              />
              <span>Display 5-Point Facial Landmarks</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#fff', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={soundEnabled}
                onChange={(e) => setSoundEnabled(e.target.checked)}
                style={{ accentColor: 'var(--accent-cyan)' }}
              />
              <span>Play 15-Second Audio Chime</span>
            </label>
          </div>
        </div>
      )}

      {/* Main Forensic Viewport Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(320px, 1fr)', gap: '24px' }}>
        {/* Left Column: Live Video Canvas Area */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="glass-panel" style={{
            position: 'relative',
            borderRadius: 'var(--radius-lg)',
            overflow: 'hidden',
            backgroundColor: '#000',
            aspectRatio: '16/9',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '380px',
            border: cameraActive ? '1px solid rgba(6, 182, 212, 0.4)' : '1px solid var(--border-subtle)',
            boxShadow: cameraActive ? '0 0 30px rgba(6, 182, 212, 0.15)' : 'none'
          }}>
            {/* HTML5 Video Element */}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                display: cameraActive ? 'block' : 'none'
              }}
            />

            {/* Canvas Overlay for Detections & Landmarks */}
            <canvas
              ref={overlayCanvasRef}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none',
                display: cameraActive ? 'block' : 'none'
              }}
            />

            {/* Offline / Placeholder Screen */}
            {!cameraActive && (
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '40px',
                textAlign: 'center',
                color: 'var(--text-muted)'
              }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '16px'
                }}>
                  <Camera size={28} color="var(--text-secondary)" />
                </div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff', marginBottom: '6px' }}>
                  Laptop Camera Inactive
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', maxWidth: '380px', marginBottom: '20px' }}>
                  Click <strong>"Start Camera"</strong> to request browser permission and activate live neural detection.
                </p>
                <button
                  onClick={startCamera}
                  className="btn btn-primary"
                  style={{ padding: '10px 24px', fontSize: '0.875rem' }}
                >
                  <Play size={16} fill="currentColor" />
                  <span>Activate Camera Feed</span>
                </button>
              </div>
            )}

            {/* Live Feed Status Bar (HUD) */}
            {cameraActive && (
              <div style={{
                position: 'absolute',
                top: '12px',
                left: '12px',
                right: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                pointerEvents: 'none',
                zIndex: 10
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 12px',
                  backgroundColor: 'rgba(15, 23, 42, 0.85)',
                  backdropFilter: 'blur(8px)',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)',
                  color: '#fff'
                }}>
                  <span style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: '#10b981',
                    boxShadow: '0 0 10px #10b981'
                  }} />
                  <span style={{ fontWeight: 700 }}>LIVE WEBCAM</span>
                  <span style={{ color: 'var(--text-muted)' }}>|</span>
                  <span style={{ color: 'var(--accent-cyan)' }}>
                    {streamResolution ? `${streamResolution.width}x${streamResolution.height}` : '720p'}
                  </span>
                </div>

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '6px 12px',
                  backgroundColor: 'rgba(15, 23, 42, 0.85)',
                  backdropFilter: 'blur(8px)',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)'
                }}>
                  <span style={{ color: 'var(--text-muted)' }}>FPS:</span>
                  <span style={{ color: '#fff', fontWeight: 700 }}>{detectionFps}</span>
                  <span style={{ color: 'var(--text-muted)' }}>|</span>
                  <span style={{ color: 'var(--text-muted)' }}>LATENCY:</span>
                  <span style={{ color: latencyMs < 80 ? '#34d399' : latencyMs < 180 ? '#fbbf24' : '#fb7185', fontWeight: 700 }}>
                    {latencyMs}ms
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Legend and Detection Telemetry Badges */}
          <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '18px', flexWrap: 'wrap', fontSize: '0.78rem' }}>
              <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>OVERLAY LEGEND:</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '12px', height: '12px', border: '2px solid #06b6d4', borderRadius: '2px' }} />
                <span style={{ color: 'var(--text-secondary)' }}>Tracked Person</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '12px', height: '12px', border: '2px solid #10b981', borderRadius: '2px' }} />
                <span style={{ color: 'var(--text-secondary)' }}>Face Detection</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '8px', height: '8px', backgroundColor: '#38bdf8', borderRadius: '50%' }} />
                <span style={{ color: 'var(--text-secondary)' }}>5-Point Landmarks</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '12px', height: '12px', border: '2px solid #f43f5e', backgroundColor: 'rgba(244, 63, 94, 0.25)', borderRadius: '2px' }} />
                <span style={{ color: '#fb7185', fontWeight: 600 }}>15s Alert Active</span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-cyan)' }}>
                <Users size={15} />
                <span>{peopleCount} {peopleCount === 1 ? 'Person' : 'People'}</span>
              </div>
              <span style={{ color: 'var(--border-subtle)' }}>•</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-emerald)' }}>
                <Smile size={15} />
                <span>{facesCount} {facesCount === 1 ? 'Face' : 'Faces'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Active Track Cards & Detection History */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Active Track Targets Panel */}
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Users size={18} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>
                  Tracked Persons ({activeTracksList.length})
                </h3>
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Target: 15.0s
              </span>
            </div>

            {activeTracksList.length === 0 ? (
              <div style={{
                padding: '24px 16px',
                textAlign: 'center',
                color: 'var(--text-muted)',
                fontSize: '0.8rem',
                border: '1px dashed var(--border-subtle)',
                borderRadius: '8px'
              }}>
                {cameraActive ? 'No subjects currently in camera view' : 'Start camera to begin continuous subject tracking'}
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '280px', overflowY: 'auto' }}>
                {activeTracksList.map(track => {
                  const pct = Math.min(100, Math.round((track.elapsedSec / 15.0) * 100));
                  const is15s = track.elapsedSec >= 15.0;

                  return (
                    <div
                      key={track.trackId}
                      style={{
                        padding: '12px 14px',
                        backgroundColor: is15s ? 'rgba(225, 29, 72, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                        border: is15s ? '1px solid rgba(244, 63, 94, 0.5)' : '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '8px',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{
                            padding: '2px 6px',
                            backgroundColor: is15s ? '#f43f5e' : 'var(--accent-cyan)',
                            color: '#fff',
                            borderRadius: '4px',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            fontFamily: 'var(--font-mono)'
                          }}>
                            TRACK #{track.trackId}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                            {track.hasFace ? 'Face Locked' : 'Upper Body'}
                          </span>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 700, color: is15s ? '#fb7185' : '#fff' }}>
                          <Clock size={13} color={is15s ? '#f43f5e' : 'var(--accent-cyan)'} />
                          <span>{track.timerText}</span>
                        </div>
                      </div>

                      {/* 15-Second Progress Bar */}
                      <div>
                        <div style={{
                          height: '5px',
                          backgroundColor: 'rgba(255, 255, 255, 0.08)',
                          borderRadius: '999px',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            height: '100%',
                            width: `${pct}%`,
                            backgroundColor: is15s ? '#f43f5e' : 'var(--accent-cyan)',
                            transition: 'width 0.15s ease-out',
                            boxShadow: is15s ? '0 0 10px #f43f5e' : '0 0 8px var(--accent-cyan)'
                          }} />
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                          <span>00:00</span>
                          <span style={{ color: is15s ? '#fb7185' : 'var(--text-secondary)', fontWeight: 600 }}>
                            {is15s ? 'CRITICAL PERSISTENCE TRIGGERED' : `${pct}% towards 15s alert`}
                          </span>
                          <span>00:15</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Detection Event History Log */}
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px', flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={18} color="var(--accent-indigo)" />
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>
                  15s Alert Event Log ({detectionHistory.length})
                </h3>
              </div>
              {detectionHistory.length > 0 && (
                <button
                  onClick={() => setDetectionHistory([])}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-muted)',
                    fontSize: '0.72rem',
                    cursor: 'pointer'
                  }}
                >
                  Clear Log
                </button>
              )}
            </div>

            {detectionHistory.length === 0 ? (
              <div style={{
                padding: '28px 16px',
                textAlign: 'center',
                color: 'var(--text-muted)',
                fontSize: '0.8rem',
                border: '1px dashed var(--border-subtle)',
                borderRadius: '8px'
              }}>
                No 15-second events triggered yet. Once a subject remains visible for 15 continuous seconds, the event will be logged here.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '340px', overflowY: 'auto' }}>
                {detectionHistory.map(evt => (
                  <div
                    key={evt.id}
                    style={{
                      padding: '10px 12px',
                      backgroundColor: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.78rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{
                        color: '#fb7185',
                        fontWeight: 700,
                        fontFamily: 'var(--font-mono)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        <AlertTriangle size={13} />
                        TRACK #{evt.trackId}
                      </span>
                      <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                        {evt.alertTime}
                      </span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.72rem' }}>
                      <span>Continuous: {evt.durationSec}s</span>
                      <span>Confidence: {Math.round(evt.confidence * 100)}%</span>
                      <span>Face: {evt.hasFace ? `${Math.round((evt.faceConfidence || 0) * 100)}%` : 'No face'}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
