export const PIPELINE_STEPS = [
  'Video Upload',
  'Frame Extraction',
  'Person Detection',
  'Tracking',
  'Face Detection',
  'Face Quality',
  'Best Frame',
] as const

export type InvestigationStatus = 'Completed' | 'Processing' | 'Under Review' | 'Flagged'

export type EvidenceTrack = {
  track_id: number | string
  best_frame_idx: number
  best_timestamp: number
  quality_score: number
  sharpness_score: number
  exposure_score: number
  resolution_score: number
  symmetry_score: number
  crop_url: string
  full_frame_url: string
  face_image_url?: string
  best_score?: number
  has_confirmed_face?: boolean
  has_real_face?: boolean
  duration_seconds?: number
  first_seen_time?: number
  last_seen_time?: number
  total_detections?: number
  person_bbox?: [number, number, number, number]
  face_bbox?: [number, number, number, number]
  quality?: {
    sharpness?: number
    exposure?: number
    crop_width?: number
    crop_height?: number
    grade?: string
    details?: any
  }
}

export type VideoAnalysisResult = {
  task_id: string
  filename: string
  video_url?: string
  summary: {
    total_frames: number
    processed_frames: number
    duration_seconds: number
    unique_persons_tracked: number
    high_quality_evidence_count: number
    average_best_quality: number
  }
  evidence_tracks: EvidenceTrack[]
}

export type Investigation = {
  id: string
  atm: string
  status: InvestigationStatus
  date: string
  faces: number
  result?: VideoAnalysisResult
}

export const RECENT_INVESTIGATIONS: Investigation[] = []

export type FaceDetection = {
  trackId: string
  seconds: number
  quality: number
}

export const VIDEO_DURATION_SECONDS = 0

export const FACE_DETECTIONS: FaceDetection[] = []

export function formatTimestamp(totalSeconds: number) {
  const s = Math.max(0, Math.floor(totalSeconds))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  const pad = (n: number) => n.toString().padStart(2, '0')
  return h > 0 ? `${pad(h)}:${pad(m)}:${pad(sec)}` : `${pad(m)}:${pad(sec)}`
}
