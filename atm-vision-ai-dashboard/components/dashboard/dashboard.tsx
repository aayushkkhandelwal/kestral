'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import axios from 'axios'
import { API_BASE_URL } from '@/lib/config'
import { cn } from '@/lib/utils'
import {
  PIPELINE_STEPS,
  type EvidenceTrack,
  type VideoAnalysisResult,
  type Investigation,
  RECENT_INVESTIGATIONS,
} from '@/lib/dashboard-data'
import { AnalysisPipeline } from './analysis-pipeline'
import { AppSidebar } from './app-sidebar'
import { BestFace } from './best-face'
import { DetectionTimeline } from './detection-timeline'
import { RecentInvestigations } from './recent-investigations'
import { StatsCards, type BackendStats } from './stats-cards'
import { TopNavbar } from './top-navbar'
import { UploadHero } from './upload-hero'
import { VideoPreview, type UploadedVideo } from './video-preview'
import { InvestigationsView } from './investigations-view'
import { EvidenceLibraryView } from './evidence-library-view'
import { ReportsView } from './reports-view'
import { SettingsView } from './settings-view'
import { VideoAnalysisView } from './video-analysis-view'
import { LiveCameraView } from './live-camera-view'
import { ModelEvaluationView } from './model-evaluation-view'

export function Dashboard({ className }: { className?: string } = {}) {
  const [activeView, setActiveView] = useState<string>('Dashboard')
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [video, setVideo] = useState<UploadedVideo | null>(null)
  const [activeStep, setActiveStep] = useState(0)
  const [processing, setProcessing] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [taskTelemetry, setTaskTelemetry] = useState<{
    taskId: string
    status: string
    progress: number
    currentFrame: number
    totalFrames: number
    tracksCount: number
    fps: number
    error?: string
  } | null>(null)

  // Backend state
  const [backendOnline, setBackendOnline] = useState(false)
  const [backendStats, setBackendStats] = useState<BackendStats>(null)
  const [investigations, setInvestigations] = useState<Investigation[]>([])
  const [activeResult, setActiveResult] = useState<VideoAnalysisResult | null>(null)
  const [selectedTrack, setSelectedTrack] = useState<EvidenceTrack | null>(null)

  const activeTaskIdRef = useRef<string | null>(null)
  const failureCountRef = useRef(0)

  // Fetch telemetry & history from backend
  const refreshBackendData = useCallback(async () => {
    // 1. Health Ping
    try {
      const healthRes = await axios.get(`${API_BASE_URL}/api/health`, { timeout: 6000 })
      if (healthRes.status === 200) {
        failureCountRef.current = 0
        setBackendOnline(true)
      }
    } catch {
      failureCountRef.current += 1
      if (failureCountRef.current >= 2) {
        setBackendOnline(false)
      }
    }

    // 2. Stats & History
    try {
      const [statsRes, histRes] = await Promise.allSettled([
        axios.get(`${API_BASE_URL}/api/stats`, { timeout: 6000 }),
        axios.get(`${API_BASE_URL}/api/history`, { timeout: 6000 }),
      ])

      if (statsRes.status === 'fulfilled' && statsRes.value.data) {
        setBackendStats(statsRes.value.data)
      }

      if (histRes.status === 'fulfilled' && Array.isArray(histRes.value.data)) {
        const mapped: Investigation[] = histRes.value.data.map((h: any) => ({
          id: `INV-${(h.task_id || '').toUpperCase()}`,
          atm: h.filename ? `ATM-CCTV · ${h.filename}` : `Stream ${h.task_id}`,
          status: 'Completed',
          date: h.timestamp
            ? new Date(h.timestamp * 1000).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })
            : 'Recent',
          faces: h.summary?.unique_persons_tracked || h.evidence_tracks?.length || 0,
          result: h,
        }))
        if (mapped.length > 0) {
          setInvestigations(mapped)
        }
      }
    } catch {
      // Ignore background telemetry errors
    }
  }, [])

  useEffect(() => {
    refreshBackendData()
    const timer = setInterval(refreshBackendData, 6000)
    return () => clearInterval(timer)
  }, [refreshBackendData])

  useEffect(() => {
    if (!video) return
    return () => {
      if (video.url.startsWith('blob:')) {
        URL.revokeObjectURL(video.url)
      }
    }
  }, [video])

  // Video Upload & Pipeline Execution
  async function handleFileSelected(file: File) {
    const localBlobUrl = URL.createObjectURL(file)
    setVideo({ name: file.name, url: localBlobUrl, uploadedAt: new Date() })
    setUploading(true)
    setUploadProgress(0)
    setUploadError(null)
    setActiveStep(0)
    setActiveResult(null)
    setSelectedTrack(null)
    setTaskTelemetry(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await axios.post(`${API_BASE_URL}/api/upload-and-process`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (evt) => {
          if (evt.total) {
            setUploadProgress(Math.round((evt.loaded * 100) / evt.total))
          }
        },
      })

      const taskId = res.data?.task_id
      if (!taskId) {
        throw new Error('No task ID returned by server')
      }

      activeTaskIdRef.current = taskId
      setUploading(false)
      setProcessing(true)
      setActiveStep(1) // Step 1: Frame Extraction
      setTaskTelemetry({
        taskId,
        status: 'processing',
        progress: 0,
        currentFrame: 0,
        totalFrames: 0,
        tracksCount: 0,
        fps: 24,
      })

      // Poll task progress
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await axios.get(`${API_BASE_URL}/api/tasks/${taskId}/status`)
          const statusData = statusRes.data

          setTaskTelemetry({
            taskId,
            status: statusData.status || 'processing',
            progress: Math.round(statusData.progress || 0),
            currentFrame: statusData.current_frame || 0,
            totalFrames: statusData.total_frames || 0,
            tracksCount: statusData.tracks_count || 0,
            fps: Math.round(statusData.processing_fps || 24),
            error: statusData.error,
          })

          if (statusData.status === 'processing') {
            const pct = statusData.progress || 0
            if (pct < 15) setActiveStep(1) // Frame Extraction
            else if (pct < 35) setActiveStep(2) // Person Detection
            else if (pct < 55) setActiveStep(3) // Tracking
            else if (pct < 75) setActiveStep(4) // Face Detection
            else if (pct < 95) setActiveStep(5) // Face Quality
            else setActiveStep(6) // Best Frame
          } else if (statusData.status === 'completed') {
            clearInterval(pollInterval)
            setActiveStep(PIPELINE_STEPS.length - 1)
            setProcessing(false)

            const finalResult = statusData.result
            if (finalResult) {
              const rawTracks = finalResult.evidence_tracks || finalResult.tracks || []
              const normalizedTracks: EvidenceTrack[] = rawTracks.map((t: any) => ({
                track_id: t.track_id,
                best_frame_idx: t.best_frame_idx || 0,
                best_timestamp: t.best_timestamp || 0,
                quality_score: t.best_score ? t.best_score / 100 : t.quality_score || 0.8,
                sharpness_score: t.quality?.sharpness || t.sharpness_score || 0,
                exposure_score: t.quality?.exposure || t.exposure_score || 0,
                resolution_score: 0.85,
                symmetry_score: 0.8,
                crop_url: t.face_image_url || t.crop_url || '',
                full_frame_url: t.full_frame_url || '',
                face_image_url: t.face_image_url,
                best_score: t.best_score ?? (t.quality_score ? Math.round(t.quality_score * 100) : 80),
                has_confirmed_face: t.has_real_face ?? t.has_confirmed_face ?? true,
                has_real_face: t.has_real_face ?? t.has_confirmed_face ?? true,
                duration_seconds: t.duration_seconds,
                first_seen_time: t.first_seen_time,
                last_seen_time: t.last_seen_time,
                total_detections: t.total_detections,
                person_bbox: t.person_bbox,
                face_bbox: t.face_bbox,
                quality: t.quality,
              }))

              const normalizedResult: VideoAnalysisResult = {
                ...finalResult,
                evidence_tracks: normalizedTracks,
                summary: {
                  total_frames: finalResult.metadata?.total_frames || finalResult.summary?.total_frames || 0,
                  processed_frames: finalResult.metadata?.frames_processed || finalResult.summary?.processed_frames || 0,
                  duration_seconds: finalResult.metadata?.duration_seconds || finalResult.summary?.duration_seconds || 0,
                  unique_persons_tracked: finalResult.summary?.unique_persons_tracked || normalizedTracks.length,
                  high_quality_evidence_count: finalResult.summary?.high_quality_evidence_count || 0,
                  average_best_quality: finalResult.summary?.average_best_quality || 0,
                },
              }

              setActiveResult(normalizedResult)
              if (normalizedTracks.length > 0) {
                const best = [...normalizedTracks].sort(
                  (a, b) => (b.quality_score || 0) - (a.quality_score || 0)
                )[0]
                setSelectedTrack(best)
              }
            }
            refreshBackendData()
          } else if (statusData.status === 'failed') {
            clearInterval(pollInterval)
            setProcessing(false)
            setUploadError(statusData.error || 'Video analysis encountered an error.')
          }
        } catch (pollErr: any) {
          console.warn('Status poll warning:', pollErr.message)
        }
      }, 1000)
    } catch (err: any) {
      setUploading(false)
      setProcessing(false)
      const detail = err.response?.data?.detail || err.message || 'Failed to upload video.'
      setUploadError(`${detail} (Is backend running on port 8000?)`)
    }
  }

  // Open an investigation from history
  function handleSelectInvestigation(inv: Investigation) {
    if (!inv.result) return
    const res = inv.result
    const rawTracks = res.evidence_tracks || (res as any).tracks || []
    const normalizedTracks: EvidenceTrack[] = rawTracks.map((t: any) => ({
      track_id: t.track_id,
      best_frame_idx: t.best_frame_idx || 0,
      best_timestamp: t.best_timestamp || 0,
      quality_score: t.best_score ? t.best_score / 100 : t.quality_score || 0.8,
      sharpness_score: t.quality?.sharpness || t.sharpness_score || 0,
      exposure_score: t.quality?.exposure || t.exposure_score || 0,
      resolution_score: 0.85,
      symmetry_score: 0.8,
      crop_url: t.face_image_url || t.crop_url || '',
      full_frame_url: t.full_frame_url || '',
      face_image_url: t.face_image_url,
      best_score: t.best_score ?? (t.quality_score ? Math.round(t.quality_score * 100) : 80),
      has_confirmed_face: t.has_real_face ?? t.has_confirmed_face ?? true,
      has_real_face: t.has_real_face ?? t.has_confirmed_face ?? true,
      duration_seconds: t.duration_seconds,
      first_seen_time: t.first_seen_time,
      last_seen_time: t.last_seen_time,
      total_detections: t.total_detections,
      person_bbox: t.person_bbox,
      face_bbox: t.face_bbox,
      quality: t.quality,
    }))

    const normalizedResult: VideoAnalysisResult = {
      ...res,
      evidence_tracks: normalizedTracks,
    }

    setActiveResult(normalizedResult)
    setProcessing(false)
    setActiveStep(PIPELINE_STEPS.length - 1)
    setTaskTelemetry(null)

    if (res.video_url) {
      setVideo({
        name: res.filename || inv.atm,
        url: res.video_url,
        uploadedAt: new Date(res.summary?.duration_seconds ? Date.now() - 3600000 : Date.now()),
      })
    }

    if (normalizedTracks.length > 0) {
      const best = [...normalizedTracks].sort(
        (a, b) => (b.quality_score || 0) - (a.quality_score || 0)
      )[0]
      setSelectedTrack(best)
    }

    window.scrollTo({ top: 380, behavior: 'smooth' })
  }

  return (
    <div className={cn('flex min-h-svh bg-background', className)}>
      <AppSidebar
        mobileOpen={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
        activeView={activeView}
        onSelectView={setActiveView}
      />
      <div className="bg-dot-grid flex min-w-0 flex-1 flex-col">
        <TopNavbar onOpenMenu={() => setMobileNavOpen(true)} backendOnline={backendOnline} />
        <main className="mx-auto flex w-full max-w-[1400px] flex-col gap-10 px-4 py-8 md:px-8 md:py-10">
          {activeView === 'Investigations' ? (
            <InvestigationsView
              investigations={investigations}
              onOpenCase={(inv) => {
                handleSelectInvestigation(inv)
                setActiveView('Video Analysis')
              }}
            />
          ) : activeView === 'Evidence Library' ? (
            <EvidenceLibraryView
              investigations={investigations}
              activeTracks={activeResult?.evidence_tracks}
            />
          ) : activeView === 'Model Evaluation' ? (
            <ModelEvaluationView />
          ) : activeView === 'Reports' ? (
            <ReportsView investigations={investigations} stats={backendStats} />
          ) : activeView === 'Settings' ? (
            <SettingsView backendOnline={backendOnline} />
          ) : activeView === 'Live Camera' ? (
            <LiveCameraView />
          ) : activeView === 'Video Analysis' ? (
            <VideoAnalysisView
              video={video}
              onFileSelected={handleFileSelected}
              uploading={uploading}
              uploadProgress={uploadProgress}
              uploadError={uploadError}
              onDismissError={() => setUploadError(null)}
              processing={processing}
              activeStep={activeStep}
              activeResult={activeResult}
              taskTelemetry={taskTelemetry}
              selectedTrack={selectedTrack}
              onSelectTrack={setSelectedTrack}
              investigations={investigations}
              onSelectInvestigation={handleSelectInvestigation}
            />
          ) : (
            /* Default: Master Executive Dashboard */
            <>
              <UploadHero
                onFileSelected={handleFileSelected}
                uploading={uploading}
                uploadProgress={uploadProgress}
                uploadError={uploadError}
              />
              <StatsCards stats={backendStats} />
              <div className="grid gap-10 xl:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
                <VideoPreview video={video} />
                <BestFace loading={processing || uploading} track={selectedTrack} />
              </div>
              <AnalysisPipeline activeStep={activeStep} processing={processing || uploading} />
              <DetectionTimeline
                loading={processing || uploading}
                tracks={activeResult?.evidence_tracks}
                duration={activeResult?.summary?.duration_seconds}
              />
              <RecentInvestigations
                investigations={investigations}
                onSelectInvestigation={handleSelectInvestigation}
              />
            </>
          )}
        </main>
      </div>
    </div>
  )
}
