'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import axios from 'axios'
import {
  Camera,
  CameraOff,
  RotateCcw,
  Clock,
  Users,
  Smile,
  AlertTriangle,
  ShieldCheck,
  Settings,
  Volume2,
  VolumeX,
  Maximize2,
  Activity,
  Sparkles,
  Info,
  CheckCircle2,
  Sliders,
  X,
  Eye,
  Download,
  User,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { API_BASE_URL } from '@/lib/config'
import { cn } from '@/lib/utils'

function playAlertChime() {
  try {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
    if (!AudioContextClass) return
    const ctx = new AudioContextClass()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()

    osc.type = 'sine'
    osc.frequency.setValueAtTime(587.33, ctx.currentTime) // D5
    osc.frequency.exponentialRampToValueAtTime(880.0, ctx.currentTime + 0.15) // A5
    osc.frequency.exponentialRampToValueAtTime(1174.66, ctx.currentTime + 0.35) // D6

    gain.gain.setValueAtTime(0.15, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6)

    osc.connect(gain)
    gain.connect(ctx.destination)

    osc.start()
    osc.stop(ctx.currentTime + 0.65)
  } catch {
    // Audio context may be restricted by browser autoplay policy before user gesture
  }
}

function formatDuration(seconds: number) {
  if (!seconds || seconds < 0) return '00:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function extractCropDataUrl(
  source: HTMLVideoElement | HTMLCanvasElement,
  bbox: number[],
  sourceWidth: number,
  sourceHeight: number,
  paddingRatio = 0.2
): string {
  try {
    if (!source || !bbox || bbox.length < 4 || !sourceWidth || !sourceHeight) return ''
    const [x1, y1, x2, y2] = bbox
    const bw = Math.max(10, x2 - x1)
    const bh = Math.max(10, y2 - y1)
    const padX = Math.round(bw * paddingRatio)
    const padY = Math.round(bh * paddingRatio)
    const sx = Math.max(0, x1 - padX)
    const sy = Math.max(0, y1 - padY)
    const sw = Math.min(sourceWidth - sx, bw + padX * 2)
    const sh = Math.min(sourceHeight - sy, bh + padY * 2)
    if (sw <= 0 || sh <= 0) return ''

    const c = document.createElement('canvas')
    c.width = Math.max(48, Math.min(sw, 480))
    c.height = Math.max(48, Math.min(sh, 480))
    const ctx = c.getContext('2d')
    if (!ctx) return ''
    ctx.drawImage(source, sx, sy, sw, sh, 0, 0, c.width, c.height)
    return c.toDataURL('image/jpeg', 0.88)
  } catch (err) {
    console.warn('Crop extraction error:', err)
    return ''
  }
}

export type SecurityEvent = {
  id: string
  trackId: number | string
  startTime: string
  alertTime: string
  durationSec: number
  confidence: number
  hasFace: boolean
  faceConfidence?: number
  acknowledged?: boolean
  acknowledgedAt?: string
  snapshotUrl?: string
  bbox?: number[]
  faceBbox?: number[]
  landmarks?: number[][]
}

export function LiveCameraView() {
  // Camera & Stream State
  const [cameraActive, setCameraActive] = useState(false)
  const [cameraStatus, setCameraStatus] = useState<'idle' | 'starting' | 'live' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Real-time Detection Telemetry
  const [peopleCount, setPeopleCount] = useState(0)
  const [facesCount, setFacesCount] = useState(0)
  const [activeTracksList, setActiveTracksList] = useState<any[]>([])
  const [bannerAlert, setBannerAlert] = useState<SecurityEvent | null>(null)
  const [detectionHistory, setDetectionHistory] = useState<SecurityEvent[]>([])
  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const [selectedPersonModal, setSelectedPersonModal] = useState<SecurityEvent | null>(null)

  const handleAcknowledge = useCallback((eventObj: SecurityEvent) => {
    const ackTime = new Date().toLocaleTimeString()

    let snap = eventObj.snapshotUrl
    if (!snap) {
      const regItem = trackerRegistryRef.current.get(eventObj.trackId)
      if (regItem?.snapshotUrl) {
        snap = regItem.snapshotUrl
      } else if (videoRef.current && (regItem?.faceBbox || regItem?.bbox)) {
        const box = regItem.faceBbox || regItem.bbox
        snap = extractCropDataUrl(videoRef.current, box, videoRef.current.videoWidth || 1280, videoRef.current.videoHeight || 720)
      }
    }

    const updated: SecurityEvent = {
      ...eventObj,
      snapshotUrl: snap || eventObj.snapshotUrl,
      acknowledged: true,
      acknowledgedAt: ackTime,
    }
    setBannerAlert(updated)
    setDetectionHistory((prev) =>
      prev.map((item) => (item.id === eventObj.id ? updated : item))
    )
    setToastMessage(`Incident for Subject #${eventObj.trackId} successfully acknowledged at ${ackTime}`)
    setTimeout(() => {
      setToastMessage((cur) => (cur?.includes(`Subject #${eventObj.trackId}`) ? null : cur))
    }, 4500)
  }, [])

  // Performance Telemetry
  const [latencyMs, setLatencyMs] = useState(0)
  const [detectionFps, setDetectionFps] = useState(0)
  const [streamResolution, setStreamResolution] = useState<{ width: number; height: number } | null>(
    null
  )

  // Configurable Settings
  const [inferenceInterval, setInferenceInterval] = useState(600) // ms
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.35)
  const [faceThreshold, setFaceThreshold] = useState(0.35)
  const [gracePeriod, setGracePeriod] = useState(1.5) // seconds
  const [showLandmarks, setShowLandmarks] = useState(true)
  const [showBoxes, setShowBoxes] = useState(true)
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [showSettings, setShowSettings] = useState(false)

  // DOM & Pipeline Refs
  const videoRef = useRef<HTMLVideoElement>(null)
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null)
  const offscreenCanvasRef = useRef<HTMLCanvasElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const isInferringRef = useRef(false)
  const animFrameIdRef = useRef<number | null>(null)
  const intervalTimerRef = useRef<NodeJS.Timeout | null>(null)

  // Temporal Tracking Registry
  const trackerRegistryRef = useRef<Map<number | string, any>>(new Map())
  const latencyHistoryRef = useRef<number[]>([])

  // Start Camera
  const startCamera = async () => {
    setErrorMessage(null)
    setCameraStatus('starting')

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraStatus('error')
      setErrorMessage(
        'Webcam access (navigator.mediaDevices.getUserMedia) is not supported in this browser context. Note: On LAN connections, browsers require HTTPS or localhost for camera access.'
      )
      return
    }

    try {
      const constraints: MediaStreamConstraints = {
        video: {
          width: { ideal: 1280, max: 1920 },
          height: { ideal: 720, max: 1080 },
          facingMode: 'user',
        },
        audio: false,
      }

      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream

      setCameraActive(true)
      setCameraStatus('live')

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current
          .play()
          .then(() => {
            if (videoRef.current) {
              setStreamResolution({
                width: videoRef.current.videoWidth || 1280,
                height: videoRef.current.videoHeight || 720,
              })
            }
          })
          .catch((err) => {
            console.warn('[LiveCamera] Play error:', err)
          })
      }
    } catch (err: any) {
      console.error('[LiveCamera] Camera access failed:', err)
      setCameraStatus('error')
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setErrorMessage(
          'Camera permission was denied. Please allow camera permissions in your browser bar.'
        )
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setErrorMessage('No camera device was detected on your hardware.')
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setErrorMessage('Camera is currently in use by another application. Please close it and retry.')
      } else {
        setErrorMessage(`Unable to initialize camera: ${err.message || 'Unknown error'}`)
      }
    }
  }

  // Stop Camera
  const stopCamera = useCallback(async () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop()
        } catch (e) {
          console.warn('Track stop error:', e)
        }
      })
      streamRef.current = null
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null
    }

    if (intervalTimerRef.current) {
      clearInterval(intervalTimerRef.current)
      intervalTimerRef.current = null
    }
    if (animFrameIdRef.current) {
      cancelAnimationFrame(animFrameIdRef.current)
      animFrameIdRef.current = null
    }

    if (overlayCanvasRef.current) {
      const ctx = overlayCanvasRef.current.getContext('2d')
      if (ctx) {
        ctx.clearRect(0, 0, overlayCanvasRef.current.width, overlayCanvasRef.current.height)
      }
    }

    try {
      await axios.post(`${API_BASE_URL}/api/camera/reset`, {}, { timeout: 2000 })
    } catch {
      // Backend may be offline or resetting
    }

    trackerRegistryRef.current.clear()
    isInferringRef.current = false
    setActiveTracksList([])
    setPeopleCount(0)
    setFacesCount(0)
    setCameraActive(false)
    setCameraStatus('idle')
  }, [])

  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [stopCamera])

  useEffect(() => {
    if (cameraActive && streamRef.current && videoRef.current) {
      if (videoRef.current.srcObject !== streamRef.current) {
        videoRef.current.srcObject = streamRef.current
        videoRef.current.play().catch(console.warn)
      }
    }
  }, [cameraActive])

  // Sample Frame & Dispatch to /api/camera/detect
  const sampleAndDetectFrame = useCallback(async () => {
    if (!cameraActive || isInferringRef.current || !videoRef.current) return
    if (videoRef.current.readyState < 2) return

    const video = videoRef.current
    const vw = video.videoWidth
    const vh = video.videoHeight
    if (!vw || !vh) return

    if (!offscreenCanvasRef.current) {
      offscreenCanvasRef.current = document.createElement('canvas')
    }
    const offCanvas = offscreenCanvasRef.current

    const maxDim = 640
    const scale = Math.min(1.0, maxDim / Math.max(vw, vh))
    const targetW = Math.round(vw * scale)
    const targetH = Math.round(vh * scale)

    offCanvas.width = targetW
    offCanvas.height = targetH
    const offCtx = offCanvas.getContext('2d')
    if (!offCtx) return

    offCtx.drawImage(video, 0, 0, targetW, targetH)

    offCanvas.toBlob(
      async (blob) => {
        if (!blob) return

        isInferringRef.current = true
        const tStart = performance.now()

        try {
          const formData = new FormData()
          formData.append('file', blob, 'frame.jpg')

          const res = await axios.post(
            `${API_BASE_URL}/api/camera/detect?conf_threshold=${confidenceThreshold}&face_conf_threshold=${faceThreshold}`,
            formData,
            {
              headers: { 'Content-Type': 'multipart/form-data' },
              timeout: 5000,
            }
          )

          const data = res.data
          const roundTripMs = Math.round(performance.now() - tStart)

          setLatencyMs(data.processing_time_ms || roundTripMs)
          latencyHistoryRef.current.push(roundTripMs)
          if (latencyHistoryRef.current.length > 8) latencyHistoryRef.current.shift()
          const avgCycle =
            latencyHistoryRef.current.reduce((a, b) => a + b, 0) / latencyHistoryRef.current.length
          const computedFps =
            Math.min(30, Math.round((1000 / Math.max(1, avgCycle + inferenceInterval)) * 10) / 10)
          setDetectionFps(computedFps)

          const invScale = 1.0 / scale
          const mappedPeople = (data.people || []).map((p: any) => ({
            ...p,
            bbox: [
              Math.round(p.bbox[0] * invScale),
              Math.round(p.bbox[1] * invScale),
              Math.round(p.bbox[2] * invScale),
              Math.round(p.bbox[3] * invScale),
            ],
            face_bbox: p.face_bbox
              ? [
                  Math.round(p.face_bbox[0] * invScale),
                  Math.round(p.face_bbox[1] * invScale),
                  Math.round(p.face_bbox[2] * invScale),
                  Math.round(p.face_bbox[3] * invScale),
                ]
              : null,
            landmarks: (p.landmarks || []).map((pt: number[]) => [
              Math.round(pt[0] * invScale),
              Math.round(pt[1] * invScale),
            ]),
          }))

          setPeopleCount(mappedPeople.length)
          setFacesCount((data.faces || []).length)

          const nowSec = Date.now() / 1000
          const currentSeenIds = new Set()

          mappedPeople.forEach((person: any) => {
            const tid = person.track_id
            currentSeenIds.add(tid)

            const cropBox = person.face_bbox || person.bbox
            const cropSnapshot = (videoRef.current && cropBox)
              ? extractCropDataUrl(videoRef.current, cropBox, vw, vh, person.face_bbox ? 0.3 : 0.1)
              : ''

            const existing = trackerRegistryRef.current.get(tid)
            if (!existing) {
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
                landmarks: person.landmarks || [],
                snapshotUrl: cropSnapshot,
              })
            } else {
              const gap = nowSec - existing.lastSeenTime
              if (gap <= gracePeriod) {
                existing.lastSeenTime = nowSec
                existing.status = 'active'
                existing.confidence = person.confidence
                existing.bbox = person.bbox
                existing.faceBbox = person.face_bbox
                existing.faceConfidence = person.face_confidence
                existing.landmarks = person.landmarks || []
                existing.continuousSeconds = nowSec - existing.firstSeenTime
                if (cropSnapshot) {
                  existing.snapshotUrl = cropSnapshot
                }

                if (existing.continuousSeconds >= 15.0 && !existing.alertTriggered) {
                  existing.alertTriggered = true

                  const eventObj: SecurityEvent = {
                    id: `EVT-${Date.now().toString().slice(-6)}`,
                    trackId: tid,
                    startTime: new Date(existing.firstSeenTime * 1000).toLocaleTimeString(),
                    alertTime: new Date(nowSec * 1000).toLocaleTimeString(),
                    durationSec: Math.floor(existing.continuousSeconds),
                    confidence: person.confidence,
                    hasFace: Boolean(person.face_bbox),
                    faceConfidence: person.face_confidence,
                    snapshotUrl: cropSnapshot || existing.snapshotUrl,
                    bbox: person.bbox,
                    faceBbox: person.face_bbox,
                    landmarks: person.landmarks || [],
                  }

                  setDetectionHistory((prev) => [eventObj, ...prev.slice(0, 49)])
                  setBannerAlert(eventObj)

                  if (soundEnabled) {
                    playAlertChime()
                  }
                }
              } else {
                existing.firstSeenTime = nowSec
                existing.lastSeenTime = nowSec
                existing.continuousSeconds = 0.0
                existing.alertTriggered = false
                existing.status = 'active'
                existing.bbox = person.bbox
                existing.faceBbox = person.face_bbox
                if (cropSnapshot) {
                  existing.snapshotUrl = cropSnapshot
                }
              }
            }
          })

          for (const [tid, item] of trackerRegistryRef.current.entries()) {
            if (!currentSeenIds.has(tid)) {
              const timeSinceSeen = nowSec - item.lastSeenTime
              if (timeSinceSeen > gracePeriod) {
                item.status = 'expired'
                if (timeSinceSeen > gracePeriod + 4.0) {
                  trackerRegistryRef.current.delete(tid)
                }
              } else {
                item.status = 'grace'
              }
            }
          }
        } catch (err: any) {
          console.warn('[LiveCamera] Detection request error:', err.message)
        } finally {
          isInferringRef.current = false
        }
      },
      'image/jpeg',
      0.85
    )
  }, [
    cameraActive,
    confidenceThreshold,
    faceThreshold,
    gracePeriod,
    inferenceInterval,
    soundEnabled,
  ])

  // Periodic sampling interval
  useEffect(() => {
    if (!cameraActive) {
      if (intervalTimerRef.current) {
        clearInterval(intervalTimerRef.current)
        intervalTimerRef.current = null
      }
      return
    }

    intervalTimerRef.current = setInterval(sampleAndDetectFrame, inferenceInterval)
    return () => {
      if (intervalTimerRef.current) {
        clearInterval(intervalTimerRef.current)
        intervalTimerRef.current = null
      }
    }
  }, [cameraActive, inferenceInterval, sampleAndDetectFrame])

  // Overlay Canvas 60FPS render loop
  const drawOverlay = useCallback(() => {
    const video = videoRef.current
    const canvas = overlayCanvasRef.current
    if (!video || !canvas || !cameraActive) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const displayW = video.clientWidth
    const displayH = video.clientHeight
    const videoW = video.videoWidth || 1280
    const videoH = video.videoHeight || 720

    if (canvas.width !== displayW || canvas.height !== displayH) {
      canvas.width = displayW
      canvas.height = displayH
    }

    ctx.clearRect(0, 0, displayW, displayH)

    const scaleX = displayW / videoW
    const scaleY = displayH / videoH
    const nowSec = Date.now() / 1000
    const currentActiveList: any[] = []

    if (showBoxes) {
      for (const [tid, track] of trackerRegistryRef.current.entries()) {
        const timeSinceSeen = nowSec - track.lastSeenTime
        if (timeSinceSeen > gracePeriod) continue

        const isAlerted = track.alertTriggered
        const elapsedSec = Math.max(0, nowSec - track.firstSeenTime)
        const timerText = formatDuration(elapsedSec)

        currentActiveList.push({
          trackId: tid,
          elapsedSec,
          timerText,
          isAlerted,
          confidence: track.confidence,
          hasFace: Boolean(track.faceBbox),
          faceConfidence: track.faceConfidence,
          status: track.status,
        })

        const [px1, py1, px2, py2] = track.bbox
        const x = px1 * scaleX
        const y = py1 * scaleY
        const w = (px2 - px1) * scaleX
        const h = (py2 - py1) * scaleY

        // Draw person cyber brackets
        ctx.save()
        if (isAlerted) {
          ctx.strokeStyle = '#f43f5e'
          ctx.shadowColor = 'rgba(244, 63, 94, 0.7)'
          ctx.shadowBlur = 10
        } else {
          ctx.strokeStyle = '#06b6d4'
          ctx.shadowColor = 'rgba(6, 182, 212, 0.5)'
          ctx.shadowBlur = 6
        }
        ctx.lineWidth = 2

        const corner = Math.min(20, Math.min(w, h) * 0.25)
        ctx.beginPath()
        // Top-left
        ctx.moveTo(x, y + corner)
        ctx.lineTo(x, y)
        ctx.lineTo(x + corner, y)
        // Top-right
        ctx.moveTo(x + w - corner, y)
        ctx.lineTo(x + w, y)
        ctx.lineTo(x + w, y + corner)
        // Bottom-right
        ctx.moveTo(x + w, y + h - corner)
        ctx.lineTo(x + w, y + h)
        ctx.lineTo(x + w - corner, y + h)
        // Bottom-left
        ctx.moveTo(x + corner, y + h)
        ctx.lineTo(x, y + h)
        ctx.lineTo(x, y + h - corner)
        ctx.stroke()

        // Header Tag
        ctx.fillStyle = isAlerted ? 'rgba(244, 63, 94, 0.9)' : 'rgba(6, 182, 212, 0.9)'
        const tagText = isAlerted
          ? `⚠️ TRACK #${tid} · ${timerText} (ALERT)`
          : `TRACK #${tid} · ${timerText}`
        ctx.font = 'bold 11px monospace'
        const tagWidth = ctx.measureText(tagText).width + 12
        ctx.fillRect(x, Math.max(0, y - 20), tagWidth, 20)

        ctx.fillStyle = '#ffffff'
        ctx.fillText(tagText, x + 6, Math.max(14, y - 6))
        ctx.restore()

        // Face Box
        if (track.faceBbox) {
          const [fx1, fy1, fx2, fy2] = track.faceBbox
          const fx = fx1 * scaleX
          const fy = fy1 * scaleY
          const fw = (fx2 - fx1) * scaleX
          const fh = (fy2 - fy1) * scaleY

          ctx.save()
          ctx.strokeStyle = '#10b981'
          ctx.lineWidth = 1.5
          ctx.strokeRect(fx, fy, fw, fh)

          ctx.fillStyle = 'rgba(16, 185, 129, 0.85)'
          const fText = `FACE ${Math.round((track.faceConfidence || 0.8) * 100)}%`
          ctx.font = 'bold 9px monospace'
          const fWidth = ctx.measureText(fText).width + 8
          ctx.fillRect(fx, Math.max(0, fy - 14), fWidth, 14)
          ctx.fillStyle = '#ffffff'
          ctx.fillText(fText, fx + 4, Math.max(10, fy - 3))
          ctx.restore()
        }

        // 5-point Landmarks
        if (showLandmarks && track.landmarks && track.landmarks.length > 0) {
          ctx.save()
          ctx.fillStyle = '#facc15'
          ctx.shadowColor = 'rgba(250, 204, 21, 0.8)'
          ctx.shadowBlur = 4
          for (const [lx, ly] of track.landmarks) {
            ctx.beginPath()
            ctx.arc(lx * scaleX, ly * scaleY, 3, 0, Math.PI * 2)
            ctx.fill()
          }
          ctx.restore()
        }
      }
    }

    setActiveTracksList(currentActiveList)
    animFrameIdRef.current = requestAnimationFrame(drawOverlay)
  }, [cameraActive, gracePeriod, showBoxes, showLandmarks])

  useEffect(() => {
    if (cameraActive) {
      animFrameIdRef.current = requestAnimationFrame(drawOverlay)
    }
    return () => {
      if (animFrameIdRef.current) cancelAnimationFrame(animFrameIdRef.current)
    }
  }, [cameraActive, drawOverlay])

  // Reset tracker on backend & locally
  const handleResetTracker = async () => {
    try {
      await axios.post(`${API_BASE_URL}/api/camera/reset`)
      trackerRegistryRef.current.clear()
      setActiveTracksList([])
      setPeopleCount(0)
      setFacesCount(0)
    } catch (e: any) {
      console.warn('Tracker reset warning:', e.message)
    }
  }

  return (
    <div className="flex flex-col gap-8">
      {/* 1. VIEW HEADER & ACTION BAR */}
      <div className="flex flex-col gap-4 rounded-2xl border bg-card p-6 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
              Live Surveillance & Laptop Camera Vision
            </h1>
            <Badge
              variant="outline"
              className={cn(
                'font-mono text-[11px] font-semibold',
                cameraActive
                  ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400'
                  : 'border-border text-muted-foreground'
              )}
            >
              {cameraActive ? '● STREAM ACTIVE' : 'OFFLINE'}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground sm:text-sm">
            Real-time ByteTrack multi-person tracking, 5-point facial landmark alignment & 15-second
            persistence security arbiter
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSettings((v) => !v)}
            className="h-9 gap-1.5 text-xs"
          >
            <Settings className="size-4" />
            <span>Config</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleResetTracker}
            disabled={!cameraActive}
            className="h-9 gap-1.5 text-xs"
          >
            <RotateCcw className="size-4" />
            <span>Reset Tracker</span>
          </Button>

          <Button
            size="sm"
            onClick={cameraActive ? stopCamera : startCamera}
            className={cn(
              'h-9 gap-2 px-5 text-xs font-bold text-white shadow-md transition-all sm:text-sm',
              cameraActive
                ? 'bg-rose-600 hover:bg-rose-500'
                : 'bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500'
            )}
          >
            {cameraActive ? (
              <>
                <CameraOff className="size-4" />
                <span>Stop Camera</span>
              </>
            ) : (
              <>
                <Camera className="size-4" />
                <span>Start Camera</span>
              </>
            )}
          </Button>
        </div>
      </div>

      {/* 2. CONFIGURATION DRAWER / SETTINGS PANEL */}
      {showSettings && (
        <div className="rounded-2xl border border-cyan-500/30 bg-muted/20 p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between border-b pb-3">
            <div className="flex items-center gap-2">
              <Sliders className="size-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-foreground">
                Vision Engine Parameters & Thresholds
              </h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSettings(false)}
              className="h-7 text-xs"
            >
              Close
            </Button>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {/* Inference Interval */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between font-mono text-xs">
                <span className="text-muted-foreground">Inference Rate:</span>
                <span className="font-bold text-cyan-400">{inferenceInterval} ms</span>
              </div>
              <input
                type="range"
                min="300"
                max="1200"
                step="50"
                value={inferenceInterval}
                onChange={(e) => setInferenceInterval(parseInt(e.target.value))}
                className="h-1.5 w-full cursor-pointer accent-cyan-500"
              />
              <span className="text-[10px] text-muted-foreground">
                Lower ms = higher FPS, higher CPU load
              </span>
            </div>

            {/* Confidence Threshold */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between font-mono text-xs">
                <span className="text-muted-foreground">Person Conf:</span>
                <span className="font-bold text-cyan-400">{confidenceThreshold}</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.8"
                step="0.05"
                value={confidenceThreshold}
                onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                className="h-1.5 w-full cursor-pointer accent-cyan-500"
              />
              <span className="text-[10px] text-muted-foreground">YOLO person filter cutoff</span>
            </div>

            {/* Grace Period */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between font-mono text-xs">
                <span className="text-muted-foreground">Grace Window:</span>
                <span className="font-bold text-cyan-400">{gracePeriod}s</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="4.0"
                step="0.5"
                value={gracePeriod}
                onChange={(e) => setGracePeriod(parseFloat(e.target.value))}
                className="h-1.5 w-full cursor-pointer accent-cyan-500"
              />
              <span className="text-[10px] text-muted-foreground">
                Seconds before absent track resets timer
              </span>
            </div>

            {/* Toggles */}
            <div className="flex flex-col gap-2 font-mono text-xs">
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={showLandmarks}
                  onChange={(e) => setShowLandmarks(e.target.checked)}
                  className="rounded accent-cyan-500"
                />
                <span>5-Point Facial Landmarks</span>
              </label>
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={showBoxes}
                  onChange={(e) => setShowBoxes(e.target.checked)}
                  className="rounded accent-cyan-500"
                />
                <span>Track Bounding Brackets</span>
              </label>
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={soundEnabled}
                  onChange={(e) => setSoundEnabled(e.target.checked)}
                  className="rounded accent-cyan-500"
                />
                <span>15s Alert Audio Chime</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* 3. HARDWARE & INFERENCE TELEMETRY CARDS */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="flex items-center gap-3.5 rounded-2xl border bg-card p-4 shadow-sm">
          <div className="flex size-11 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
            <Users className="size-5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Subjects in View</p>
            <p className="text-xl font-bold font-mono text-foreground sm:text-2xl">{peopleCount}</p>
          </div>
        </div>

        <div className="flex items-center gap-3.5 rounded-2xl border bg-card p-4 shadow-sm">
          <div className="flex size-11 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400">
            <Smile className="size-5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Faces Verified</p>
            <p className="text-xl font-bold font-mono text-foreground sm:text-2xl">{facesCount}</p>
          </div>
        </div>

        <div className="flex items-center gap-3.5 rounded-2xl border bg-card p-4 shadow-sm">
          <div className="flex size-11 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400">
            <Activity className="size-5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Inference Latency</p>
            <p className="text-xl font-bold font-mono text-foreground sm:text-2xl">{latencyMs} ms</p>
          </div>
        </div>

        <div className="flex items-center gap-3.5 rounded-2xl border bg-card p-4 shadow-sm">
          <div className="flex size-11 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400">
            <Clock className="size-5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Inference Throughput</p>
            <p className="text-xl font-bold font-mono text-foreground sm:text-2xl">
              {detectionFps} FPS
            </p>
          </div>
        </div>
      </div>

      {/* 4. 15-SECOND CRITICAL PERSISTENCE BANNER WITH PERSON DETAILS */}
      {bannerAlert && (() => {
        const activeItem = trackerRegistryRef.current.get(bannerAlert.trackId)
        const currentSnapshot = bannerAlert.snapshotUrl || activeItem?.snapshotUrl

        return (
          <div
            className={cn(
              'relative overflow-hidden rounded-2xl border p-5 shadow-lg transition-all',
              bannerAlert.acknowledged
                ? 'border-emerald-500/40 bg-emerald-500/15'
                : 'border-rose-500/50 bg-rose-500/15'
            )}
          >
            {/* Top Bar: Alert Heading & Actions */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-border/30 pb-4">
              <div className="flex items-center gap-3.5">
                <div
                  className={cn(
                    'flex size-10 shrink-0 items-center justify-center rounded-xl text-white',
                    bannerAlert.acknowledged
                      ? 'bg-emerald-600 shadow-sm'
                      : 'bg-rose-600 animate-pulse'
                  )}
                >
                  {bannerAlert.acknowledged ? (
                    <CheckCircle2 className="size-5" />
                  ) : (
                    <AlertTriangle className="size-5" />
                  )}
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h4
                      className={cn(
                        'text-sm font-bold sm:text-base',
                        bannerAlert.acknowledged
                          ? 'text-emerald-950 dark:text-emerald-200'
                          : 'text-rose-950 dark:text-rose-100'
                      )}
                    >
                      {bannerAlert.acknowledged
                        ? `PERSISTENCE EVENT ACKNOWLEDGED: Subject #${bannerAlert.trackId}`
                        : `CRITICAL PERSISTENCE TRIGGER: Subject #${bannerAlert.trackId}`}
                    </h4>
                    {bannerAlert.acknowledged ? (
                      <Badge
                        variant="outline"
                        className="border-emerald-600/40 bg-emerald-500/20 text-emerald-900 dark:text-emerald-200 font-mono text-[11px] font-semibold"
                      >
                        ✓ Acknowledged at {bannerAlert.acknowledgedAt}
                      </Badge>
                    ) : (
                      <Badge
                        variant="outline"
                        className="border-rose-600/40 bg-rose-500/20 text-rose-900 dark:text-rose-200 font-mono text-[11px] font-semibold"
                      >
                        Stationary Dwell Limit Exceeded
                      </Badge>
                    )}
                  </div>
                  <p
                    className={cn(
                      'text-xs mt-0.5',
                      bannerAlert.acknowledged
                        ? 'text-emerald-900/90 dark:text-emerald-300/80'
                        : 'text-rose-900/90 dark:text-rose-200/90'
                    )}
                  >
                    Subject has remained continuously stationary in ATM / camera field of view for{' '}
                    <strong>{bannerAlert.durationSec} seconds</strong> (Triggered at {bannerAlert.alertTime}).
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedPersonModal({ ...bannerAlert, snapshotUrl: currentSnapshot })}
                  className="bg-background/80 text-xs font-semibold hover:bg-muted shadow-sm gap-1.5"
                >
                  <Eye className="size-3.5 text-primary" />
                  View Person Dossier
                </Button>
                {!bannerAlert.acknowledged ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAcknowledge({ ...bannerAlert, snapshotUrl: currentSnapshot })}
                    className="border-rose-500/60 bg-background/90 text-xs font-semibold text-rose-800 hover:bg-rose-500/20 dark:text-rose-100 shadow-sm"
                  >
                    <CheckCircle2 className="mr-1.5 size-3.5 text-rose-600" />
                    Acknowledge
                  </Button>
                ) : (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setBannerAlert(null)}
                    className="text-xs text-muted-foreground hover:text-foreground"
                  >
                    Dismiss
                  </Button>
                )}
              </div>
            </div>

            {/* Embedded Person Details Card */}
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-[auto_1fr] gap-4 rounded-xl border border-border/50 bg-background/70 p-3.5 backdrop-blur-sm">
              {/* Person Snapshot Thumbnail */}
              <div className="flex flex-col items-center justify-center">
                {currentSnapshot ? (
                  <div
                    className="group relative size-20 overflow-hidden rounded-xl border-2 border-primary/50 bg-black cursor-pointer hover:border-primary transition-all shadow-md"
                    onClick={() => setSelectedPersonModal({ ...bannerAlert, snapshotUrl: currentSnapshot })}
                    title="Click to expand full person dossier"
                  >
                    <img
                      src={currentSnapshot}
                      alt={`Subject #${bannerAlert.trackId} live capture`}
                      className="size-full object-cover transition-transform group-hover:scale-105"
                    />
                    <div className="absolute bottom-0 inset-x-0 bg-black/75 py-0.5 text-center font-mono text-[9px] text-white">
                      {bannerAlert.hasFace ? 'FACE CROP' : 'BODY CROP'}
                    </div>
                  </div>
                ) : (
                  <div
                    className="flex size-20 flex-col items-center justify-center rounded-xl border border-dashed bg-muted/40 p-2 text-center text-muted-foreground cursor-pointer hover:bg-muted/60"
                    onClick={() => setSelectedPersonModal(bannerAlert)}
                  >
                    <User className="size-6 mb-1 text-primary/70" />
                    <span className="font-mono text-[9px]">ID #{bannerAlert.trackId}</span>
                  </div>
                )}
              </div>

              {/* Person Telemetry Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 text-xs">
                <div className="flex flex-col gap-0.5 rounded-lg border bg-card/60 p-2.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Subject Track</span>
                  <span className="font-mono font-bold text-foreground">Subject #{bannerAlert.trackId}</span>
                  <span className="text-[10px] text-muted-foreground">YOLOv8 ByteTrack ID</span>
                </div>

                <div className="flex flex-col gap-0.5 rounded-lg border bg-card/60 p-2.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Biometric Status</span>
                  <span className="font-bold text-foreground flex items-center gap-1">
                    {bannerAlert.hasFace ? (
                      <>
                        <CheckCircle2 className="size-3 text-emerald-500" />
                        Face Verified ({Math.round((bannerAlert.faceConfidence || 0) * 100)}%)
                      </>
                    ) : (
                      <>
                        <Activity className="size-3 text-amber-500" />
                        Silhouette / Body
                      </>
                    )}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {bannerAlert.hasFace ? 'YuNet 5-pt Landmarks' : 'Face Occluded / Profile'}
                  </span>
                </div>

                <div className="flex flex-col gap-0.5 rounded-lg border bg-card/60 p-2.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Continuous Dwell</span>
                  <span className="font-mono font-bold text-rose-600 dark:text-rose-400 flex items-center gap-1">
                    <Clock className="size-3" />
                    {bannerAlert.durationSec}s Stationary
                  </span>
                  <span className="text-[10px] text-muted-foreground">Alert Limit: 15.0s</span>
                </div>

                <div className="flex flex-col gap-0.5 rounded-lg border bg-card/60 p-2.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Detection Conf.</span>
                  <span className="font-mono font-bold text-foreground">
                    {Math.round(bannerAlert.confidence * 100)}% Confidence
                  </span>
                  <span className="text-[10px] text-muted-foreground truncate">
                    First seen: {bannerAlert.startTime}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )
      })()}

      {/* Floating Confirmation Toast */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-2xl border border-emerald-500/30 bg-card/95 p-4 shadow-2xl backdrop-blur-md animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white shadow">
            <CheckCircle2 className="size-5" />
          </div>
          <div className="text-xs pr-2">
            <p className="font-bold text-foreground">Alert Acknowledged</p>
            <p className="text-muted-foreground">{toastMessage}</p>
          </div>
          <button
            type="button"
            onClick={() => setToastMessage(null)}
            className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            aria-label="Close notification"
          >
            <X className="size-4" />
          </button>
        </div>
      )}

      {/* 5. ERROR ALERT */}
      {errorMessage && (
        <div className="flex items-center gap-3 rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-xs text-rose-400 sm:text-sm">
          <AlertTriangle className="size-5 shrink-0 text-rose-500" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* 6. MAIN SPLIT VIEW: CAMERA VIEWPORT & DWELL TRACK TIMERS */}
      <div className="grid gap-8 lg:grid-cols-[1.5fr_1fr]">
        {/* Left Column: Live Camera Stream Viewport */}
        <div className="flex flex-col gap-4 rounded-2xl border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between border-b pb-3">
            <div className="flex items-center gap-2">
              <Camera className="size-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-foreground">Camera Viewport</h3>
            </div>

            {streamResolution && (
              <span className="font-mono text-xs text-muted-foreground">
                {streamResolution.width} × {streamResolution.height}
              </span>
            )}
          </div>

          {/* Video & Canvas Overlay Container */}
          <div className="relative aspect-video w-full overflow-hidden rounded-xl border bg-black shadow-inner flex items-center justify-center">
            <video
              ref={videoRef}
              className={cn('size-full object-contain', !cameraActive && 'hidden')}
              playsInline
              autoPlay
              muted
            />
            <canvas
              ref={overlayCanvasRef}
              className={cn(
                'pointer-events-none absolute inset-0 size-full',
                !cameraActive && 'hidden'
              )}
            />

            {cameraActive ? (
              <div className="absolute top-3 left-3 flex items-center gap-2 rounded-md bg-black/80 px-2.5 py-1 font-mono text-[11px] text-white backdrop-blur-md">
                <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>LIVE OVERLAY ACTIVE</span>
              </div>
            ) : (
              <div
                className="flex flex-col items-center justify-center p-8 text-center cursor-pointer"
                onClick={startCamera}
              >
                <div className="mb-3.5 flex size-14 items-center justify-center rounded-2xl bg-muted/60 text-muted-foreground">
                  <Camera className="size-7 text-cyan-400" />
                </div>
                <h4 className="text-sm font-bold text-foreground sm:text-base">
                  Live Camera Feed Offline
                </h4>
                <p className="mt-1 max-w-sm text-xs text-muted-foreground">
                  Click to start your laptop camera and engage real-time subject tracking with
                  15-second stationary alerts.
                </p>
                <Button size="sm" className="mt-4 gap-2 bg-cyan-600 text-xs text-white hover:bg-cyan-500">
                  <Camera className="size-3.5" />
                  <span>Launch Live Camera</span>
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Active Subject Dwell Progress Bars & Event Log */}
        <div className="flex flex-col gap-6">
          {/* Active Subject Dwell Timers */}
          <div className="flex flex-col gap-4 rounded-2xl border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center gap-2">
                <Clock className="size-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-foreground">
                  Active Subject Dwell Timers ({activeTracksList.length})
                </h3>
              </div>
              <span className="font-mono text-xs text-muted-foreground">Target: 15.0s</span>
            </div>

            {activeTracksList.length === 0 ? (
              <p className="rounded-xl border border-dashed p-6 text-center text-xs text-muted-foreground">
                {cameraActive
                  ? 'No subjects currently in camera view'
                  : 'Start camera to begin continuous subject tracking'}
              </p>
            ) : (
              <div className="flex flex-col gap-3 max-h-[260px] overflow-y-auto">
                {activeTracksList.map((track) => {
                  const pct = Math.min(100, Math.round((track.elapsedSec / 15.0) * 100))
                  const is15s = track.elapsedSec >= 15.0

                  return (
                    <div
                      key={track.trackId}
                      className={cn(
                        'flex flex-col gap-2 rounded-xl border p-3 transition-all',
                        is15s
                          ? 'border-rose-500/60 bg-rose-500/10'
                          : 'border-border bg-muted/20'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span
                            className={cn(
                              'rounded px-2 py-0.5 font-mono text-[11px] font-bold text-white',
                              is15s ? 'bg-rose-600' : 'bg-cyan-600'
                            )}
                          >
                            TRACK #{track.trackId}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {track.hasFace ? 'Face Locked' : 'Body Tracked'}
                          </span>
                        </div>

                        <div
                          className={cn(
                            'flex items-center gap-1 font-mono text-xs font-bold',
                            is15s ? 'text-rose-400' : 'text-foreground'
                          )}
                        >
                          <Clock className="size-3" />
                          <span>{track.timerText}</span>
                        </div>
                      </div>

                      {/* 15s Progress Bar */}
                      <div>
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                          <div
                            className={cn(
                              'h-full rounded-full transition-all duration-150',
                              is15s ? 'bg-rose-500' : 'bg-cyan-400'
                            )}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <div className="mt-1 flex justify-between font-mono text-[10px] text-muted-foreground">
                          <span>00:00</span>
                          <span className={cn(is15s && 'font-bold text-rose-400')}>
                            {is15s ? 'CRITICAL PERSISTENCE TRIGGERED' : `${pct}% towards 15s alert`}
                          </span>
                          <span>00:15</span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* 15-Second Alert Event History Log */}
          <div className="flex flex-1 flex-col gap-4 rounded-2xl border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-foreground">
                  15s Security Event Log ({detectionHistory.length})
                </h3>
              </div>
              {detectionHistory.length > 0 && (
                <button
                  type="button"
                  onClick={() => setDetectionHistory([])}
                  className="font-mono text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear Log
                </button>
              )}
            </div>

            {detectionHistory.length === 0 ? (
              <p className="rounded-xl border border-dashed p-6 text-center text-xs text-muted-foreground">
                No 15-second events triggered yet. Once a subject remains visible for 15 continuous
                seconds, an entry will be logged here.
              </p>
            ) : (
              <div className="flex flex-col gap-2 max-h-[220px] overflow-y-auto">
                {detectionHistory.map((evt) => (
                  <div
                    key={evt.id}
                    className="flex flex-col gap-1.5 rounded-xl border border-border bg-muted/20 p-2.5 font-mono text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="flex items-center gap-1 font-bold text-rose-500">
                          <AlertTriangle className="size-3" />
                          TRACK #{evt.trackId}
                        </span>
                        {evt.acknowledged ? (
                          <span className="rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 dark:text-emerald-300">
                            ✓ ACKNOWLEDGED ({evt.acknowledgedAt})
                          </span>
                        ) : (
                          <span className="rounded-full bg-rose-500/15 border border-rose-500/30 px-2 py-0.5 text-[10px] font-semibold text-rose-700 dark:text-rose-300">
                            PENDING ACK
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] text-muted-foreground">{evt.alertTime}</span>
                        {!evt.acknowledged && (
                          <button
                            type="button"
                            onClick={() => handleAcknowledge(evt)}
                            className="rounded px-1.5 py-0.5 text-[10px] font-bold text-rose-600 hover:bg-rose-500/15 border border-rose-500/30 transition-colors"
                          >
                            Ack
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="flex justify-between text-[11px] text-muted-foreground">
                      <span>Dwell: {evt.durationSec}s</span>
                      <span>Conf: {Math.round(evt.confidence * 100)}%</span>
                      <span>
                        Face: {evt.hasFace ? `${Math.round((evt.faceConfidence || 0) * 100)}%` : 'No face'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      {/* Forensic Subject Dossier Modal */}
      {selectedPersonModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="relative w-full max-w-2xl overflow-hidden rounded-2xl border bg-card p-6 shadow-2xl">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b pb-4">
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <User className="size-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-foreground">
                    Forensic Subject Dossier · Track #{selectedPersonModal.trackId}
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    ATM Live Surveillance Camera · Alert Triggered at {selectedPersonModal.alertTime}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedPersonModal(null)}
                className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                aria-label="Close dossier"
              >
                <X className="size-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="mt-5 grid grid-cols-1 md:grid-cols-[1.2fr_1.5fr] gap-6">
              {/* Left Column: Evidence Snapshot */}
              <div className="flex flex-col gap-3">
                <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                  Extracted Visual Crop
                </span>
                <div className="relative aspect-square w-full overflow-hidden rounded-xl border bg-black shadow-inner flex items-center justify-center">
                  {selectedPersonModal.snapshotUrl ? (
                    <img
                      src={selectedPersonModal.snapshotUrl}
                      alt={`Subject #${selectedPersonModal.trackId}`}
                      className="size-full object-contain"
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center p-6 text-center text-muted-foreground">
                      <User className="size-12 mb-2 text-muted-foreground/60" />
                      <p className="text-xs">Live feed crop is rendering</p>
                    </div>
                  )}
                  {selectedPersonModal.hasFace && (
                    <div className="absolute top-2.5 right-2.5 rounded-md bg-black/80 px-2 py-0.5 font-mono text-[10px] text-emerald-400 backdrop-blur-md">
                      YUNET 5-PT VERIFIED
                    </div>
                  )}
                </div>

                {selectedPersonModal.snapshotUrl && (
                  <a
                    href={selectedPersonModal.snapshotUrl}
                    download={`subject_${selectedPersonModal.trackId}_evidence.jpg`}
                    className="inline-flex items-center justify-center gap-2 rounded-lg border bg-muted/30 px-3 py-2 text-xs font-medium hover:bg-muted/60 transition-colors"
                  >
                    <Download className="size-3.5" />
                    Download Evidence Crop
                  </a>
                )}
              </div>

              {/* Right Column: Full Telemetry Breakdown */}
              <div className="flex flex-col gap-3">
                <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                  Telemetry & Security Assessment
                </span>
                <div className="flex flex-col divide-y rounded-xl border bg-muted/20 px-3.5 py-1 text-xs">
                  <div className="flex justify-between py-2">
                    <span className="text-muted-foreground">Subject ID</span>
                    <span className="font-mono font-bold text-foreground">Track #{selectedPersonModal.trackId}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-muted-foreground">Stationary Duration</span>
                    <span className="font-mono font-bold text-rose-500">
                      {selectedPersonModal.durationSec}s Continuous Dwell
                    </span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-muted-foreground">Detection Confidence</span>
                    <span className="font-mono font-bold text-foreground">
                      {Math.round(selectedPersonModal.confidence * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-muted-foreground">Biometric Facial Match</span>
                    <span className="font-bold text-foreground flex items-center gap-1">
                      {selectedPersonModal.hasFace ? (
                        <span className="text-emerald-500">
                          Confirmed ({Math.round((selectedPersonModal.faceConfidence || 0) * 100)}%)
                        </span>
                      ) : (
                        <span className="text-amber-500">Not detected / Occluded</span>
                      )}
                    </span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-muted-foreground">First Appearance</span>
                    <span className="font-mono text-muted-foreground">{selectedPersonModal.startTime}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-muted-foreground">Alert Trigger Time</span>
                    <span className="font-mono text-muted-foreground">{selectedPersonModal.alertTime}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-muted-foreground">Security Status</span>
                    <span className="font-bold text-foreground">
                      {selectedPersonModal.acknowledged ? (
                        <span className="text-emerald-500">
                          ✓ Acknowledged ({selectedPersonModal.acknowledgedAt})
                        </span>
                      ) : (
                        <span className="text-rose-500">Pending Officer Acknowledgment</span>
                      )}
                    </span>
                  </div>
                </div>

                <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-[11px] text-rose-800 dark:text-rose-200">
                  <p className="font-semibold mb-0.5">Automated Risk Advisory:</p>
                  <p className="text-muted-foreground">
                    Subject exceeded 15 seconds continuous stationary presence in the ATM transaction field. Recommend verifying ATM slot and surrounding area for potential tampering or loitering.
                  </p>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="mt-6 flex items-center justify-end gap-2 border-t pt-4">
              {!selectedPersonModal.acknowledged && (
                <Button
                  size="sm"
                  onClick={() => {
                    handleAcknowledge(selectedPersonModal)
                    setSelectedPersonModal((prev) => (prev ? { ...prev, acknowledged: true, acknowledgedAt: new Date().toLocaleTimeString() } : null))
                  }}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs gap-1.5"
                >
                  <CheckCircle2 className="size-3.5" />
                  Acknowledge Incident
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedPersonModal(null)}
                className="text-xs"
              >
                Close Dossier
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
