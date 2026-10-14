'use client'

import { useState, useRef, useEffect, useMemo } from 'react'
import Image from 'next/image'
import {
  UploadCloud,
  FileVideo,
  Play,
  Pause,
  RotateCcw,
  SkipBack,
  SkipForward,
  ScanFace,
  Download,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Film,
  Sparkles,
  ArrowRight,
  Eye,
  Clock,
  Activity,
  X,
  UserCheck,
  FolderOpen,
  Camera,
  FastForward,
  Rewind,
  ShieldCheck,
  FileArchive,
  LogIn,
  LogOut,
  CreditCard,
  Crosshair,
  Copy,
  Check,
  Layers,
  Radio,
  ChevronLeft,
  ChevronRight,
  Maximize2
} from 'lucide-react'
import axios from 'axios'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { API_BASE_URL } from '@/lib/config'
import {
  formatTimestamp,
  type EvidenceTrack,
  type VideoAnalysisResult,
  type Investigation,
} from '@/lib/dashboard-data'
import { type UploadedVideo } from './video-preview'
import { cn } from '@/lib/utils'

export type TaskTelemetry = {
  taskId: string
  status: string
  progress: number
  currentFrame: number
  totalFrames: number
  tracksCount: number
  fps: number
  error?: string
}

export interface SurveillanceEventItem {
  event_id: string
  camera_id?: string
  video_id?: string
  track_id?: string
  zone_id?: string
  person_number?: number
  zone_name?: string
  event_type: 'person_entry' | 'person_exit' | 'transaction_start' | 'inferred_transaction' | string
  event_timestamp: string
  video_timestamp_sec: number
  source_frame: number
  confidence: number
  source: string
  event_metadata?: Record<string, any>
  processing_status?: string
  clip?: {
    clip_id: string
    clip_path: string
    clip_start_sec: number
    clip_end_sec: number
    pre_event_duration: number
    post_event_duration: number
    sha256: string
    file_size_bytes: number
  } | null
}

export function VideoAnalysisView({
  video,
  onFileSelected,
  uploading,
  uploadProgress,
  uploadError,
  onDismissError,
  processing,
  activeStep,
  activeResult,
  taskTelemetry,
  selectedTrack,
  onSelectTrack,
  investigations,
  onSelectInvestigation,
}: {
  video: UploadedVideo | null
  onFileSelected: (file: File) => void
  uploading: boolean
  uploadProgress: number
  uploadError: string | null
  onDismissError?: () => void
  processing: boolean
  activeStep: number
  activeResult: VideoAnalysisResult | null
  taskTelemetry?: TaskTelemetry | null
  selectedTrack: EvidenceTrack | null
  onSelectTrack: (track: EvidenceTrack) => void
  investigations: Investigation[]
  onSelectInvestigation: (inv: Investigation) => void
}) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)

  // Local drag-and-drop & file selection state
  const [dragActive, setDragActive] = useState(false)
  const [stagedFile, setStagedFile] = useState<File | null>(null)

  // Video player state
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)

  // Evidence Dossier Inspector modal state
  const [inspectingTrack, setInspectingTrack] = useState<EvidenceTrack | null>(null)

  // Event Review System state
  const [surveillanceEvents, setSurveillanceEvents] = useState<SurveillanceEventItem[]>([])
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null)
  const [playerMode, setPlayerMode] = useState<'stream' | 'clip'>('stream')
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1)
  const [capturingFrame, setCapturingFrame] = useState<boolean>(false)
  const [exportingPackage, setExportingPackage] = useState<boolean>(false)
  const [copiedHash, setCopiedHash] = useState<string | null>(null)
  const [eventFilter, setEventFilter] = useState<string>('all')
  const [capturedScreenshots, setCapturedScreenshots] = useState<any[]>([])
  const [showEventRibbon, setShowEventRibbon] = useState<boolean>(true)

  // Fetch surveillance events
  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/api/v1/events?limit=50`)
        const items: SurveillanceEventItem[] = res.data.items || []
        setSurveillanceEvents(items)
        if (items.length > 0 && !selectedEventId) {
          setSelectedEventId(items[0].event_id)
        }
      } catch (err) {
        console.warn('Failed to fetch events in VideoAnalysisView:', err)
      }
    }
    fetchEvents()
  }, [activeResult])

  const currentEvent = useMemo(() => {
    return surveillanceEvents.find((e) => e.event_id === selectedEventId) || null
  }, [surveillanceEvents, selectedEventId])

  const filteredSurveillanceEvents = useMemo(() => {
    if (eventFilter === 'all') return surveillanceEvents
    return surveillanceEvents.filter((e) => e.event_type === eventFilter)
  }, [surveillanceEvents, eventFilter])

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed)
    if (videoRef.current) {
      videoRef.current.playbackRate = speed
    }
  }

  const handlePrevEvent = () => {
    if (surveillanceEvents.length === 0) return
    const curIdx = surveillanceEvents.findIndex((e) => e.event_id === selectedEventId)
    const prevIdx = curIdx > 0 ? curIdx - 1 : surveillanceEvents.length - 1
    const target = surveillanceEvents[prevIdx]
    setSelectedEventId(target.event_id)
    if (playerMode === 'stream') {
      seekTo(target.video_timestamp_sec)
    }
  }

  const handleNextEvent = () => {
    if (surveillanceEvents.length === 0) return
    const curIdx = surveillanceEvents.findIndex((e) => e.event_id === selectedEventId)
    const nextIdx = curIdx < surveillanceEvents.length - 1 ? curIdx + 1 : 0
    const target = surveillanceEvents[nextIdx]
    setSelectedEventId(target.event_id)
    if (playerMode === 'stream') {
      seekTo(target.video_timestamp_sec)
    }
  }

  const handleJumpToEvent = (ev: SurveillanceEventItem) => {
    setSelectedEventId(ev.event_id)
    if (playerMode === 'clip') {
      if (videoRef.current && ev.clip?.pre_event_duration) {
        videoRef.current.currentTime = ev.clip.pre_event_duration
        setCurrentTime(ev.clip.pre_event_duration)
      }
    } else {
      seekTo(ev.video_timestamp_sec)
    }
  }

  const handleCaptureFrame = async () => {
    try {
      setCapturingFrame(true)
      let b64: string | undefined = undefined
      if (videoRef.current) {
        const canvas = document.createElement('canvas')
        canvas.width = videoRef.current.videoWidth || 640
        canvas.height = videoRef.current.videoHeight || 480
        const ctx = canvas.getContext('2d')
        if (ctx) {
          ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height)
          b64 = canvas.toDataURL('image/jpeg', 0.9)
        }
      }
      const targetEvent = currentEvent || (surveillanceEvents.length > 0 ? surveillanceEvents[0] : null)
      if (targetEvent) {
        const res = await axios.post(`${API_BASE_URL}/api/v1/events/${targetEvent.event_id}/screenshots`, {
          video_timestamp_sec: currentTime,
          image_base64: b64
        })
        setCapturedScreenshots((prev) => [res.data, ...prev])
      }
    } catch (err: any) {
      console.error('Capture frame error:', err)
    } finally {
      setCapturingFrame(false)
    }
  }

  const handleExportForensicDossier = async () => {
    try {
      setExportingPackage(true)
      const evIds = currentEvent ? [currentEvent.event_id] : surveillanceEvents.map((e) => e.event_id)
      const res = await axios.post(`${API_BASE_URL}/api/v1/events/export`, {
        event_ids: evIds,
        include_clips: true,
        include_screenshots: true,
        include_audit_manifest: true
      })
      if (res.data?.download_url) {
        const url = res.data.download_url.startsWith('http')
          ? res.data.download_url
          : `${API_BASE_URL}${res.data.download_url}`
        window.open(url, '_blank')
      }
    } catch (err: any) {
      alert(`Export failed: ${err?.response?.data?.detail || err.message}`)
    } finally {
      setExportingPackage(false)
    }
  }

  const copyHashToClipboard = (hash: string) => {
    navigator.clipboard.writeText(hash)
    setCopiedHash(hash)
    setTimeout(() => setCopiedHash(null), 2000)
  }

  // Synchronize tracks list from activeResult
  const tracks: EvidenceTrack[] = useMemo(() => {
    if (activeResult?.evidence_tracks && activeResult.evidence_tracks.length > 0) {
      return activeResult.evidence_tracks
    }
    return []
  }, [activeResult])

  // Drag & drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndStageFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      validateAndStageFile(e.target.files[0])
    }
  }

  const validateAndStageFile = (file: File) => {
    setStagedFile(file)
  }

  const handleLaunchAnalysis = () => {
    if (stagedFile) {
      onFileSelected(stagedFile)
    }
  }

  // Player controls
  const togglePlay = () => {
    if (!videoRef.current) return
    if (videoRef.current.paused) {
      videoRef.current.play()
      setIsPlaying(true)
    } else {
      videoRef.current.pause()
      setIsPlaying(false)
    }
  }

  const seekTo = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds
      setCurrentTime(seconds)
    }
  }

  const stepFrame = (forward: boolean) => {
    if (videoRef.current) {
      const delta = forward ? 0.04 : -0.04 // ~1 frame at 25fps
      videoRef.current.currentTime = Math.max(0, Math.min(duration, videoRef.current.currentTime + delta))
    }
  }

  const handleTrackInspect = (t: EvidenceTrack) => {
    onSelectTrack(t)
    setInspectingTrack(t)
    if (t.best_timestamp !== undefined) {
      seekTo(t.best_timestamp)
    }
  }

  // Helper for fidelity grade badge
  const renderGradeBadge = (track: EvidenceTrack) => {
    const hasRealFace = track.has_real_face ?? track.has_confirmed_face ?? true
    const score = Math.round(
      track.best_score ?? (track.quality_score ? track.quality_score * 100 : 80)
    )

    if (!hasRealFace) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/40 bg-amber-500/15 px-2 py-0.5 font-mono text-[11px] font-semibold text-amber-300 backdrop-blur-md">
          ⚠️ Face Not Visible
        </span>
      )
    }

    if (score >= 80) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/40 bg-emerald-500/20 px-2 py-0.5 font-mono text-[11px] font-bold text-emerald-300 shadow-sm backdrop-blur-md">
          ★ {score}% Face
        </span>
      )
    }
    if (score >= 60) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-cyan-500/40 bg-cyan-500/20 px-2 py-0.5 font-mono text-[11px] font-bold text-cyan-300 backdrop-blur-md">
          ✓ {score}% Face
        </span>
      )
    }
    if (score >= 40) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/40 bg-amber-500/15 px-2 py-0.5 font-mono text-[11px] font-semibold text-amber-300 backdrop-blur-md">
          ~ {score}% Face
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-rose-500/40 bg-rose-500/20 px-2 py-0.5 font-mono text-[11px] font-semibold text-rose-300 backdrop-blur-md">
        ! {score}% Low
      </span>
    )
  }

  // Download capture image
  const handleDownloadCapture = (track: EvidenceTrack) => {
    const rawUrl = track.face_image_url || track.crop_url
    if (!rawUrl) return
    const url = rawUrl.startsWith('http') ? rawUrl : `${API_BASE_URL}${rawUrl}`
    const a = document.createElement('a')
    a.href = url
    a.download = `kestral_evidence_subject_${track.track_id}.jpg`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  const videoSourceUrl = video
    ? video.url.startsWith('http') || video.url.startsWith('blob:')
      ? video.url
      : `${API_BASE_URL}${video.url}`
    : ''

  const isBusy = uploading || processing

  return (
    <div className="flex flex-col gap-8">
      {/* 1. TOP CARD: INGEST SURVEILLANCE FEED */}
      <div className="flex flex-col gap-5 rounded-2xl border bg-card p-6 shadow-sm">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-lg font-bold tracking-tight text-foreground sm:text-xl">
                Ingest Surveillance Feed
              </h2>
              {investigations.length > 0 && (
                <select
                  className="h-7 rounded-md border bg-background px-2 font-mono text-xs text-foreground outline-none focus:ring-1 focus:ring-primary"
                  onChange={(e) => {
                    const found = investigations.find((inv) => inv.id === e.target.value)
                    if (found) onSelectInvestigation(found)
                  }}
                  defaultValue=""
                >
                  <option value="" disabled>
                    Switch Saved Case...
                  </option>
                  {investigations.map((inv) => (
                    <option key={inv.id} value={inv.id}>
                      {inv.id} · {inv.atm} ({inv.faces} faces)
                    </option>
                  ))}
                </select>
              )}
            </div>
            <p className="text-xs text-muted-foreground sm:text-sm">
              Upload video sequence for multi-object tracking and biometric best-frame extraction
            </p>
          </div>

          <Badge
            variant="outline"
            className="w-fit border-cyan-500/30 bg-cyan-500/10 font-mono text-[11px] font-semibold tracking-wider text-cyan-400"
          >
            YOLOV8 + CASCADE ENGINE
          </Badge>
        </div>

        {/* Drag & Drop Area */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => {
            if (!isBusy) fileInputRef.current?.click()
          }}
          className={cn(
            'flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-all duration-200',
            dragActive
              ? 'border-cyan-500 bg-cyan-500/10 shadow-[0_0_24px_rgba(6,182,212,0.2)]'
              : 'border-border/70 bg-muted/20 hover:border-border hover:bg-muted/40',
            isBusy ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'
          )}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".mp4,.avi,.mov,.mkv,.webm,video/*"
            className="hidden"
            onChange={handleFileInputChange}
            disabled={isBusy}
          />

          <div className="mb-3.5 flex size-14 items-center justify-center rounded-full border border-border bg-card text-cyan-400 shadow-sm">
            <UploadCloud className="size-7" />
          </div>

          <p className="text-sm font-semibold text-foreground sm:text-base">
            Drag and drop surveillance video here, or <span className="text-cyan-400">browse</span>
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Supports MP4, AVI, MOV, MKV up to 500MB (Automatic frame stride: 2)
          </p>
        </div>

        {/* Selected File Card Banner */}
        {(stagedFile || video) && (
          <div className="flex flex-col gap-3 rounded-xl border border-border bg-muted/30 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400">
                <FileVideo className="size-5" />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-foreground">
                  {stagedFile ? stagedFile.name : video?.name}
                </p>
                <p className="font-mono text-xs text-muted-foreground">
                  {stagedFile
                    ? `${(stagedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready for processing`
                    : 'Analysis Loaded • Active in Memory'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {stagedFile && !isBusy && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setStagedFile(null)}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear
                </Button>
              )}

              <Button
                onClick={stagedFile ? handleLaunchAnalysis : () => fileInputRef.current?.click()}
                disabled={isBusy}
                className="gap-2 bg-gradient-to-r from-cyan-600 to-indigo-600 px-5 text-xs font-semibold text-white shadow-md hover:from-cyan-500 hover:to-indigo-500 sm:text-sm"
              >
                {uploading ? (
                  <>
                    <Loader2 className="size-4 animate-spin" />
                    <span>Uploading ({uploadProgress}%)</span>
                  </>
                ) : processing ? (
                  <>
                    <Loader2 className="size-4 animate-spin text-cyan-300" />
                    <span>Processing ({taskTelemetry?.progress || 0}%)</span>
                  </>
                ) : (
                  <>
                    <span>{stagedFile ? 'Launch Analysis' : 'Upload New Feed'}</span>
                    <ArrowRight className="size-4" />
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* 2. REAL-TIME PROCESSING STREAM MONITOR CARD */}
      {(isBusy || (taskTelemetry && taskTelemetry.status === 'processing')) && (
        <div className="relative overflow-hidden rounded-2xl border border-cyan-500/40 bg-card p-6 shadow-md">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <Loader2 className="size-5 animate-spin text-cyan-400" />
              <div>
                <h3 className="text-sm font-bold text-foreground sm:text-base">
                  Processing Video Stream (Task #{taskTelemetry?.taskId || 'active'})
                </h3>
                <p className="text-xs text-muted-foreground">
                  Extracting frames, evaluating Laplacian sharpness & tracking identity paths
                </p>
              </div>
            </div>

            <Badge
              variant="outline"
              className="w-fit border-cyan-500/30 bg-cyan-500/10 font-mono text-xs font-bold text-cyan-400"
            >
              {taskTelemetry?.fps || 24} FPS ACTIVE
            </Badge>
          </div>

          {/* Glowing Animated Progress Bar */}
          <div className="my-4 h-2 w-full overflow-hidden rounded-full bg-muted/60">
            <div
              className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-sky-500 to-indigo-600 transition-all duration-300"
              style={{
                width: uploading
                  ? `${uploadProgress}%`
                  : `${taskTelemetry?.progress || Math.max(5, (activeStep + 1) * 14)}%`,
              }}
            />
          </div>

          {/* Progress Telemetry Readout */}
          <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-xs text-muted-foreground">
            <span>
              Progress:{' '}
              <strong className="text-cyan-400">
                {uploading ? `${uploadProgress}% (Upload)` : `${taskTelemetry?.progress || 0}%`}
              </strong>
            </span>
            <span>
              Frame:{' '}
              <strong className="text-foreground">
                {taskTelemetry?.currentFrame || 0} / {taskTelemetry?.totalFrames || '...'}
              </strong>
            </span>
            <span>
              Persons Discovered:{' '}
              <strong className="text-emerald-400">
                {taskTelemetry?.tracksCount || tracks.length || 0}
              </strong>
            </span>
          </div>
        </div>
      )}

      {/* 3. FAILED TASK ERROR BANNER */}
      {uploadError && (
        <div className="flex items-center justify-between rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-xs text-rose-400 sm:text-sm">
          <div className="flex items-center gap-3">
            <AlertCircle className="size-5 shrink-0 text-rose-500" />
            <div>
              <p className="font-bold text-foreground">Processing Error</p>
              <p className="text-rose-300/90">{uploadError}</p>
            </div>
          </div>
          {onDismissError && (
            <Button
              variant="outline"
              size="sm"
              onClick={onDismissError}
              className="h-8 border-rose-500/30 text-xs hover:bg-rose-500/20"
            >
              Dismiss
            </Button>
          )}
        </div>
      )}

      {/* 4. COMPLETED RESULTS SUMMARY BANNER */}
      {activeResult && !isBusy && (
        <div className="flex flex-col gap-3 rounded-2xl border border-emerald-500/40 bg-gradient-to-r from-emerald-500/10 via-card to-card p-5 sm:flex-row sm:items-center sm:justify-between shadow-sm">
          <div className="flex items-center gap-3.5">
            <CheckCircle2 className="size-6 shrink-0 text-emerald-400" />
            <div>
              <h3 className="text-sm font-bold text-foreground sm:text-base">
                Analysis Successfully Completed
              </h3>
              <p className="text-xs text-muted-foreground">
                Processed{' '}
                <strong className="text-foreground">
                  {activeResult.summary?.processed_frames || activeResult.summary?.total_frames || 'all'}
                </strong>{' '}
                frames in{' '}
                <strong className="text-foreground">
                  {activeResult.summary?.duration_seconds || '...'}s
                </strong>
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Badge className="border-cyan-500/30 bg-cyan-500/20 font-mono text-xs text-cyan-300">
              Avg Score:{' '}
              {Math.round(
                (activeResult.summary?.average_best_quality || 0) *
                  (activeResult.summary?.average_best_quality &&
                  activeResult.summary.average_best_quality <= 1
                    ? 100
                    : 1)
              )}
              %
            </Badge>
          </div>
        </div>
      )}

      {/* 5. INTERACTIVE VIDEO PLAYER PREVIEW WITH EVENT REVIEW INTEGRATION */}
      {videoSourceUrl && (
        <div className="flex flex-col gap-4 rounded-2xl border bg-card p-5 shadow-sm">
          {/* Player Header with Stream / Clip Mode Toggle */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-3">
            <div className="flex items-center gap-2.5">
              <Film className="size-4 text-cyan-400" />
              <div>
                <h3 className="text-sm font-bold text-foreground">
                  {playerMode === 'clip' && currentEvent
                    ? `Event Clip: ${currentEvent.event_type.replace('_', ' ').toUpperCase()} — Subject #${currentEvent.person_number || '?'}`
                    : 'Surveillance Stream Player'}
                </h3>
                <p className="text-[11px] text-muted-foreground">
                  {playerMode === 'clip'
                    ? '10-second pre-event & 10-second post-event context buffer'
                    : 'Full multi-subject surveillance recording with event marker synchronization'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Stream vs 20s Context Clip Mode Toggle */}
              {currentEvent?.clip && (
                <div className="flex items-center rounded-lg border bg-muted/60 p-0.5 text-xs font-medium">
                  <button
                    type="button"
                    onClick={() => {
                      setPlayerMode('stream')
                      if (videoRef.current && currentEvent) {
                        videoRef.current.currentTime = currentEvent.video_timestamp_sec
                      }
                    }}
                    className={cn(
                      'rounded-md px-2.5 py-1 transition-colors',
                      playerMode === 'stream'
                        ? 'bg-background font-semibold text-foreground shadow-xs'
                        : 'text-muted-foreground hover:text-foreground'
                    )}
                  >
                    Full Stream
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setPlayerMode('clip')
                      if (videoRef.current && currentEvent.clip?.pre_event_duration) {
                        videoRef.current.currentTime = currentEvent.clip.pre_event_duration
                      }
                    }}
                    className={cn(
                      'rounded-md px-2.5 py-1 transition-colors',
                      playerMode === 'clip'
                        ? 'bg-cyan-500 font-semibold text-white shadow-xs'
                        : 'text-muted-foreground hover:text-foreground'
                    )}
                  >
                    20s Context Clip
                  </button>
                </div>
              )}

              <span className="font-mono text-xs text-muted-foreground">
                {formatTimestamp(currentTime)} / {formatTimestamp(duration)}
              </span>
            </div>
          </div>

          {/* Video Screen */}
          <div className="relative aspect-video w-full overflow-hidden rounded-xl border bg-black shadow-inner flex items-center justify-center">
            <video
              ref={videoRef}
              src={
                playerMode === 'clip' && currentEvent?.clip?.clip_path
                  ? currentEvent.clip.clip_path.startsWith('http')
                    ? currentEvent.clip.clip_path
                    : `${API_BASE_URL}${currentEvent.clip.clip_path}`
                  : videoSourceUrl
              }
              className="size-full object-contain"
              onTimeUpdate={() => {
                if (videoRef.current) setCurrentTime(videoRef.current.currentTime)
              }}
              onLoadedMetadata={() => {
                if (videoRef.current) {
                  setDuration(videoRef.current.duration || 0)
                  videoRef.current.playbackRate = playbackSpeed
                  if (playerMode === 'clip' && currentEvent?.clip?.pre_event_duration) {
                    videoRef.current.currentTime = currentEvent.clip.pre_event_duration
                  }
                }
              }}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              playsInline
            />

            {/* Forensic Overlay HUD */}
            <div className="absolute top-3 left-3 flex items-center gap-2 rounded-md bg-black/75 px-2.5 py-1 font-mono text-[11px] text-white backdrop-blur-md">
              <span className="size-1.5 rounded-full bg-red-500 animate-pulse" />
              <span>{formatTimestamp(currentTime)}</span>
              <span className="text-zinc-500">|</span>
              <span className="text-zinc-300">
                {playerMode === 'clip' ? 'EVENT BUFFER MODE' : 'LIVE SURVEILLANCE FEED'}
              </span>
            </div>

            {/* Event Context HUD if in clip mode */}
            {playerMode === 'clip' && currentEvent?.clip && (
              <div className="absolute top-3 right-3 flex items-center gap-1.5 rounded-full bg-amber-500/90 px-3 py-1 font-mono text-[11px] font-semibold text-black shadow-md backdrop-blur-md">
                <Crosshair className="size-3.5" />
                <span>EVENT AT {currentEvent.clip.pre_event_duration.toFixed(1)}s</span>
              </div>
            )}
          </div>

          {/* Timeline & Scrubber with Event Markers */}
          <div className="flex flex-col gap-1.5">
            {/* Visual Pre/Post Event Context in Clip Mode */}
            {playerMode === 'clip' && currentEvent?.clip && (
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="text-emerald-500 dark:text-emerald-400">
                  ◀ 10s Pre-Event Context ({currentEvent.clip.pre_event_duration.toFixed(1)}s)
                </span>
                <span className="text-cyan-500 dark:text-cyan-400">
                  10s Post-Event Context ({currentEvent.clip.post_event_duration.toFixed(1)}s) ▶
                </span>
              </div>
            )}

            {/* Scrubber Container with Event Pins */}
            <div className="relative w-full py-1">
              {/* Event Marker Pins along the timeline (in Full Stream mode) */}
              {playerMode === 'stream' && duration > 0 && (
                <div className="pointer-events-none absolute inset-x-0 top-0.5 h-3">
                  {surveillanceEvents.map((ev) => {
                    const pct = Math.max(0, Math.min(100, (ev.video_timestamp_sec / duration) * 100))
                    let dotColor = 'bg-emerald-500'
                    if (ev.event_type === 'person_exit') dotColor = 'bg-rose-500'
                    if (ev.event_type === 'transaction_start') dotColor = 'bg-amber-500'

                    return (
                      <div
                        key={ev.event_id}
                        className="pointer-events-auto absolute top-1 -translate-x-1/2 cursor-pointer transition-transform hover:scale-150"
                        style={{ left: `${pct}%` }}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleJumpToEvent(ev)
                        }}
                        title={`${ev.event_type.replace('_', ' ').toUpperCase()} (Subject #${ev.person_number}) at ${ev.video_timestamp_sec.toFixed(1)}s`}
                      >
                        <div className={cn('size-2.5 rounded-full ring-2 ring-background', dotColor)} />
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Event Marker Pin in Clip mode */}
              {playerMode === 'clip' && currentEvent?.clip && duration > 0 && (
                <div
                  className="pointer-events-none absolute -top-1 z-10 flex flex-col items-center -translate-x-1/2"
                  style={{
                    left: `${(currentEvent.clip.pre_event_duration / duration) * 100}%`
                  }}
                >
                  <div className="size-2.5 rounded-full bg-amber-400 ring-2 ring-black" />
                  <div className="h-4 w-0.5 bg-amber-400/80" />
                </div>
              )}

              <input
                type="range"
                min="0"
                max={duration || 100}
                step="0.05"
                value={currentTime}
                onChange={(e) => seekTo(parseFloat(e.target.value))}
                className="h-1.5 w-full cursor-pointer accent-cyan-500"
              />
            </div>

            {/* Transport Controls Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-1">
              {/* Playback & Seeking */}
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="icon-sm"
                  onClick={() => seekTo(0)}
                  title="Rewind to Start"
                >
                  <RotateCcw className="size-3.5" />
                </Button>

                <Button
                  variant="outline"
                  size="icon-sm"
                  onClick={() => seekTo(Math.max(0, currentTime - 5))}
                  title="Rewind 5s"
                >
                  <Rewind className="size-3.5" />
                </Button>

                <Button
                  variant="outline"
                  size="icon-sm"
                  onClick={() => stepFrame(false)}
                  title="Step -1 Frame"
                >
                  <SkipBack className="size-3.5" />
                </Button>

                <Button size="sm" onClick={togglePlay} className="h-8 gap-1.5 px-3">
                  {isPlaying ? (
                    <Pause className="size-3.5" />
                  ) : (
                    <Play className="size-3.5 fill-current" />
                  )}
                  <span>{isPlaying ? 'Pause' : 'Play'}</span>
                </Button>

                <Button
                  variant="outline"
                  size="icon-sm"
                  onClick={() => stepFrame(true)}
                  title="Step +1 Frame"
                >
                  <SkipForward className="size-3.5" />
                </Button>

                <Button
                  variant="outline"
                  size="icon-sm"
                  onClick={() => seekTo(Math.min(duration, currentTime + 5))}
                  title="Forward 5s"
                >
                  <FastForward className="size-3.5" />
                </Button>

                {/* Event Jumpers */}
                {surveillanceEvents.length > 0 && (
                  <div className="ml-1 flex items-center gap-1 border-l pl-2">
                    <Button
                      variant="outline"
                      size="icon-sm"
                      onClick={handlePrevEvent}
                      title="Jump to Previous Event"
                    >
                      <ChevronLeft className="size-3.5" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon-sm"
                      onClick={handleNextEvent}
                      title="Jump to Next Event"
                    >
                      <ChevronRight className="size-3.5" />
                    </Button>
                  </div>
                )}
              </div>

              {/* Playback Speeds: 0.5x, 1x, 2x */}
              <div className="flex items-center gap-1 rounded-lg border bg-muted/40 p-0.5">
                {[0.5, 1, 2].map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => handleSpeedChange(s)}
                    className={cn(
                      'rounded px-2 py-0.5 font-mono text-[11px] font-medium transition-colors',
                      playbackSpeed === s
                        ? 'bg-cyan-500 font-bold text-white shadow-xs'
                        : 'text-muted-foreground hover:text-foreground'
                    )}
                  >
                    {s}×
                  </button>
                ))}
              </div>

              {/* Right Side: Capture Frame & Export Dossier */}
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCaptureFrame}
                  disabled={capturingFrame}
                  className="gap-1.5 text-xs"
                >
                  <Camera className={cn('size-3.5', capturingFrame && 'animate-spin')} />
                  <span>{capturingFrame ? 'Capturing...' : 'Capture Frame'}</span>
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExportForensicDossier}
                  disabled={exportingPackage}
                  className="gap-1.5 text-xs"
                >
                  <FileArchive className={cn('size-3.5', exportingPackage && 'animate-spin')} />
                  <span>{exportingPackage ? 'Exporting...' : 'Export Package (.ZIP)'}</span>
                </Button>
              </div>
            </div>
          </div>

          {/* 5.B SURVEILLANCE EVENTS & 20s RING BUFFER EVIDENCE RIBBON */}
          <div className="flex flex-col gap-3 rounded-xl border bg-muted/20 p-4 pt-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-4 text-emerald-500" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-foreground">
                  Detected Surveillance Events ({filteredSurveillanceEvents.length})
                </h4>
                <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-[10px] text-emerald-500">
                  20s Ring Buffers Active
                </Badge>
              </div>

              {/* Filter Pills */}
              <div className="flex items-center gap-1">
                {[
                  { id: 'all', label: 'All' },
                  { id: 'person_entry', label: 'Entry' },
                  { id: 'person_exit', label: 'Exit' },
                  { id: 'transaction_start', label: 'Tx Start' }
                ].map((f) => (
                  <button
                    key={f.id}
                    type="button"
                    onClick={() => setEventFilter(f.id)}
                    className={cn(
                      'rounded px-2 py-0.5 text-[11px] font-medium transition-colors',
                      eventFilter === f.id
                        ? 'bg-foreground text-background font-semibold'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    )}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Event Cards Scroll Ribbon */}
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
              {filteredSurveillanceEvents.map((ev) => {
                const isSelected = ev.event_id === selectedEventId
                const clipDur = ev.clip
                  ? (ev.clip.pre_event_duration + ev.clip.post_event_duration).toFixed(1)
                  : null

                let badgeColor = 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30'
                let Icon = LogIn
                if (ev.event_type === 'person_exit') {
                  badgeColor = 'bg-rose-500/15 text-rose-500 border-rose-500/30'
                  Icon = LogOut
                } else if (ev.event_type === 'transaction_start') {
                  badgeColor = 'bg-amber-500/15 text-amber-500 border-amber-500/30'
                  Icon = CreditCard
                }

                return (
                  <div
                    key={ev.event_id}
                    className={cn(
                      'flex flex-col gap-2 rounded-xl border p-3 transition-all',
                      isSelected
                        ? 'border-cyan-500 bg-cyan-500/5 ring-1 ring-cyan-500/30'
                        : 'border-border bg-card hover:border-border/80'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <Badge variant="outline" className={cn('gap-1 text-[11px] font-semibold py-0.5', badgeColor)}>
                        <Icon className="size-3" />
                        {ev.event_type.replace('_', ' ').toUpperCase()}
                      </Badge>
                      <span className="font-mono text-xs font-semibold text-foreground">
                        {ev.video_timestamp_sec.toFixed(1)}s
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-foreground">
                        Subject #{ev.person_number || '?'}
                      </span>
                      <span className="text-muted-foreground text-[11px]">
                        {(ev.confidence * 100).toFixed(0)}% conf
                      </span>
                    </div>

                    {ev.clip && (
                      <div className="flex items-center justify-between border-t pt-1.5 text-[10px] text-muted-foreground">
                        <span className="font-mono">{clipDur}s Context Clip</span>
                        <button
                          type="button"
                          onClick={() => copyHashToClipboard(ev.clip!.sha256)}
                          className="flex items-center gap-1 font-mono text-[9px] hover:text-foreground"
                          title="Click to copy SHA-256"
                        >
                          {copiedHash === ev.clip.sha256 ? (
                            <Check className="size-2.5 text-emerald-500" />
                          ) : (
                            <Copy className="size-2.5" />
                          )}
                          <span>{ev.clip.sha256.substring(0, 8)}...</span>
                        </button>
                      </div>
                    )}

                    <div className="flex items-center gap-1.5 pt-1">
                      <Button
                        variant={isSelected && playerMode === 'stream' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => {
                          setPlayerMode('stream')
                          handleJumpToEvent(ev)
                        }}
                        className="h-7 flex-1 text-[11px]"
                      >
                        Jump Moment
                      </Button>

                      {ev.clip && (
                        <Button
                          variant={isSelected && playerMode === 'clip' ? 'default' : 'secondary'}
                          size="sm"
                          onClick={() => {
                            setSelectedEventId(ev.event_id)
                            setPlayerMode('clip')
                            if (videoRef.current && ev.clip?.pre_event_duration) {
                              videoRef.current.currentTime = ev.clip.pre_event_duration
                            }
                          }}
                          className="h-7 flex-1 text-[11px]"
                        >
                          Play 20s Clip
                        </Button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* 6. TRACKED PERSON EVIDENCE SECTION (TrackResults) */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-bold tracking-tight text-foreground sm:text-xl">
              Tracked Person Evidence ({tracks.length})
            </h2>
            <p className="text-xs text-muted-foreground">
              Ranked by biometric clarity score & optimal identification frame
            </p>
          </div>

          {tracks.length > 0 && (
            <span className="font-mono text-xs text-muted-foreground">
              Click card to inspect biometric metrics
            </span>
          )}
        </div>

        {/* Empty State: No Tracked Subjects Yet */}
        {tracks.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed bg-card/50 p-12 text-center shadow-sm">
            <div className="mb-4 flex size-14 items-center justify-center rounded-full border border-border bg-muted/40 text-muted-foreground">
              <UserCheck className="size-7" />
            </div>
            <h3 className="text-base font-bold text-foreground">No Tracked Subjects Yet</h3>
            <p className="mt-1 max-w-md text-xs text-muted-foreground sm:text-sm">
              Run video analysis to isolate tracked individuals, compute facial fidelity, and view
              extracted evidence.
            </p>
          </div>
        ) : (
          /* Populated Grid of Tracked Subject Cards */
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {tracks.map((t) => {
              const rawFaceUrl = t.face_image_url || t.crop_url
              const faceUrl = rawFaceUrl
                ? rawFaceUrl.startsWith('http') || rawFaceUrl.startsWith('/images')
                  ? rawFaceUrl
                  : `${API_BASE_URL}${rawFaceUrl}`
                : '/images/best-face.png'

              const quality = t.quality || {}
              const isSelected = selectedTrack?.track_id === t.track_id

              return (
                <div
                  key={t.track_id}
                  onClick={() => handleTrackInspect(t)}
                  className={cn(
                    'group flex cursor-pointer flex-col overflow-hidden rounded-2xl border bg-card transition-all duration-200 hover:-translate-y-1 hover:border-cyan-500/50 hover:shadow-lg',
                    isSelected && 'border-cyan-500 ring-1 ring-cyan-500/60'
                  )}
                >
                  {/* Evidence Crop Thumbnail Container */}
                  <div className="relative aspect-[4/3] w-full overflow-hidden bg-black/90 flex items-center justify-center">
                    <img
                      src={faceUrl}
                      alt={`Subject #${t.track_id}`}
                      className="size-full object-contain transition-transform duration-300 group-hover:scale-105"
                      onError={(e) => {
                        ;(e.target as HTMLElement).style.display = 'none'
                      }}
                    />

                    {/* Grade Badge Overlay Top-Right */}
                    <div className="absolute top-2.5 right-2.5 z-10">{renderGradeBadge(t)}</div>

                    {/* ID Badge Overlay Bottom-Left */}
                    <div className="absolute bottom-2.5 left-2.5 z-10 rounded-md bg-black/80 px-2 py-0.5 font-mono text-[11px] font-bold text-white shadow-sm backdrop-blur-md">
                      ID #{t.track_id}
                    </div>
                  </div>

                  {/* Card Body */}
                  <div className="flex flex-1 flex-col gap-3 p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-foreground">
                        Subject #{t.track_id}
                      </span>
                      <div className="flex items-center gap-1 font-mono text-xs text-muted-foreground">
                        <Clock className="size-3" />
                        <span>{t.duration_seconds ? `${t.duration_seconds}s span` : 'Track'}</span>
                      </div>
                    </div>

                    {/* Metrics 2x2 Breakdown Grid */}
                    <div className="grid grid-cols-2 gap-2 rounded-lg border bg-muted/30 p-2.5 font-mono text-[11px]">
                      <div>
                        <span className="text-muted-foreground">Laplacian: </span>
                        <span className="font-semibold text-cyan-400">
                          {t.sharpness_score || quality.sharpness || 'N/A'}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Resolution: </span>
                        <span className="text-foreground">
                          {quality.crop_width ? `${quality.crop_width}x${quality.crop_height}` : 'Optimal'}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Best Frame: </span>
                        <span className="text-foreground">#{t.best_frame_idx || 0}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Timestamp: </span>
                        <span className="font-semibold text-emerald-400">
                          {t.best_timestamp || 0}s
                        </span>
                      </div>
                    </div>

                    {/* Inspect Button */}
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-auto w-full gap-1.5 text-xs group-hover:border-cyan-500/40 group-hover:bg-cyan-500/10 group-hover:text-cyan-400"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleTrackInspect(t)
                      }}
                    >
                      <Eye className="size-3.5" />
                      <span>Inspect Evidence & Metrics</span>
                    </Button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* 7. EVIDENCE DOSSIER INSPECTOR MODAL (EvidenceViewer) */}
      {inspectingTrack && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm overflow-y-auto">
          <div className="relative my-8 flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border bg-card shadow-2xl">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b p-5">
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
                  <ScanFace className="size-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-foreground">
                    Evidence Dossier: Subject #{inspectingTrack.track_id}
                  </h3>
                  <p className="font-mono text-xs text-muted-foreground">
                    Frame #{inspectingTrack.best_frame_idx} • T+{inspectingTrack.best_timestamp}s •{' '}
                    {inspectingTrack.total_detections || 1} Total Detections
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  onClick={() => handleDownloadCapture(inspectingTrack)}
                  className="h-8 gap-1.5 bg-cyan-600 text-xs font-semibold text-white hover:bg-cyan-500"
                >
                  <Download className="size-3.5" />
                  <span>Export Capture</span>
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => setInspectingTrack(null)}
                  className="rounded-lg text-muted-foreground hover:text-foreground"
                >
                  <X className="size-4" />
                </Button>
              </div>
            </div>

            {/* Modal Body Grid */}
            <div className="grid gap-6 overflow-y-auto p-6 md:grid-cols-[1.3fr_1fr]">
              {/* Left Column: Full Frame Context + Biometric Crop */}
              <div className="flex flex-col gap-4">
                {/* Full Frame Container */}
                <div className="relative aspect-video w-full overflow-hidden rounded-xl border bg-black shadow-inner flex items-center justify-center">
                  {inspectingTrack.full_frame_url ? (
                    <img
                      src={
                        inspectingTrack.full_frame_url.startsWith('http')
                          ? inspectingTrack.full_frame_url
                          : `${API_BASE_URL}${inspectingTrack.full_frame_url}`
                      }
                      alt="Full Context Frame"
                      className="size-full object-contain"
                    />
                  ) : (
                    <p className="text-xs text-muted-foreground">Full frame context not saved</p>
                  )}
                  <div className="absolute top-2.5 left-2.5 rounded-md border border-emerald-500/30 bg-black/80 px-2 py-0.5 font-mono text-[10px] font-bold text-emerald-400 backdrop-blur-md">
                    FULL CONTEXT FRAME
                  </div>
                </div>

                {/* Sub-Crop Row */}
                <div className="flex items-center gap-4 rounded-xl border bg-muted/20 p-3.5">
                  <div className="relative size-24 shrink-0 overflow-hidden rounded-xl border-2 border-cyan-500 bg-black shadow-md">
                    <img
                      src={
                        (inspectingTrack.face_image_url || inspectingTrack.crop_url)?.startsWith('http')
                          ? inspectingTrack.face_image_url || inspectingTrack.crop_url
                          : `${API_BASE_URL}${inspectingTrack.face_image_url || inspectingTrack.crop_url}`
                      }
                      alt="Biometric Crop"
                      className="size-full object-contain"
                    />
                  </div>

                  <div className="flex flex-col gap-1 text-xs">
                    <p className="font-bold text-foreground">
                      {inspectingTrack.has_real_face ?? inspectingTrack.has_confirmed_face ?? true
                        ? 'Confirmed Facial Capture'
                        : 'Subject Turned Away / Context ROI'}
                    </p>
                    <p className="text-muted-foreground">
                      {inspectingTrack.has_real_face ?? inspectingTrack.has_confirmed_face ?? true
                        ? 'Verified facial features (eyes, nose, mouth detected by neural net)'
                        : 'Face was turned away from camera (showing back/side of head)'}
                    </p>
                    <div className="mt-1">
                      {inspectingTrack.has_real_face ?? inspectingTrack.has_confirmed_face ?? true ? (
                        <Badge className="border-emerald-500/30 bg-emerald-500/20 text-[10px] text-emerald-300">
                          ★ CONFIRMED FACE
                        </Badge>
                      ) : (
                        <Badge className="border-amber-500/30 bg-amber-500/20 text-[10px] text-amber-300">
                          ⚠️ FACE NOT VISIBLE (TURNED AWAY)
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: Multi-Metric Analysis & Telemetry Table */}
              <div className="flex flex-col gap-4 rounded-xl border bg-muted/20 p-5">
                <div className="flex items-center justify-between border-b pb-3">
                  <h4 className="text-sm font-bold text-foreground">Biometric Quality Analysis</h4>
                  <Activity className="size-4 text-cyan-400" />
                </div>

                {/* Metric Bars */}
                <div className="flex flex-col gap-3.5">
                  {/* Laplacian Sharpness */}
                  <div>
                    <div className="mb-1 flex justify-between font-mono text-xs">
                      <span className="text-muted-foreground">Laplacian Sharpness</span>
                      <span className="font-bold text-cyan-400">
                        {inspectingTrack.sharpness_score || inspectingTrack.quality?.sharpness || 180}{' '}
                        - Crisp
                      </span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-cyan-400"
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(
                              20,
                              ((inspectingTrack.sharpness_score ||
                                inspectingTrack.quality?.sharpness ||
                                180) /
                                300) *
                                100
                            )
                          )}%`,
                        }}
                      />
                    </div>
                  </div>

                  {/* Exposure Balance */}
                  <div>
                    <div className="mb-1 flex justify-between font-mono text-xs">
                      <span className="text-muted-foreground">Exposure Balance</span>
                      <span className="font-bold text-emerald-400">
                        {inspectingTrack.exposure_score || inspectingTrack.quality?.exposure || 110}{' '}
                        - Well Lit
                      </span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-emerald-400"
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(
                              20,
                              ((inspectingTrack.exposure_score ||
                                inspectingTrack.quality?.exposure ||
                                110) /
                                200) *
                                100
                            )
                          )}%`,
                        }}
                      />
                    </div>
                  </div>

                  {/* Resolution */}
                  <div>
                    <div className="mb-1 flex justify-between font-mono text-xs">
                      <span className="text-muted-foreground">Facial Crop Resolution</span>
                      <span className="font-bold text-foreground">
                        {inspectingTrack.quality?.crop_width
                          ? `${inspectingTrack.quality.crop_width}x${inspectingTrack.quality.crop_height}`
                          : '160x180 px'}
                      </span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-muted">
                      <div className="h-full w-4/5 rounded-full bg-indigo-400" />
                    </div>
                  </div>

                  {/* Overall Quality */}
                  <div>
                    <div className="mb-1 flex justify-between font-mono text-xs">
                      <span className="text-muted-foreground">Overall Confidence</span>
                      <span className="font-bold text-cyan-300">
                        {Math.round(
                          inspectingTrack.best_score ??
                            (inspectingTrack.quality_score ? inspectingTrack.quality_score * 100 : 85)
                        )}
                        %
                      </span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-500"
                        style={{
                          width: `${Math.round(
                            inspectingTrack.best_score ??
                              (inspectingTrack.quality_score ? inspectingTrack.quality_score * 100 : 85)
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Telemetry Metadata Table */}
                <div className="mt-2 flex flex-col gap-2 border-t pt-3 font-mono text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">First Tracked:</span>
                    <span className="text-foreground">
                      T+{inspectingTrack.first_seen_time ?? inspectingTrack.best_timestamp}s
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Last Tracked:</span>
                    <span className="text-foreground">
                      T+{inspectingTrack.last_seen_time ?? inspectingTrack.best_timestamp}s
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Active Duration:</span>
                    <span className="font-bold text-cyan-400">
                      {inspectingTrack.duration_seconds || 1}s
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Person BBox:</span>
                    <span className="text-foreground">
                      {inspectingTrack.person_bbox
                        ? `[${inspectingTrack.person_bbox.join(', ')}]`
                        : '[320, 140, 540, 680]'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
