'use client'

import React, { useState, useEffect, useRef, useMemo } from 'react'
import axios from 'axios'
import {
  Play,
  Pause,
  RotateCcw,
  FastForward,
  Rewind,
  Camera,
  Download,
  Shield,
  ShieldCheck,
  AlertTriangle,
  Clock,
  MapPin,
  User,
  ArrowRight,
  ArrowLeft,
  ChevronRight,
  ChevronLeft,
  Search,
  Filter,
  CheckCircle2,
  Copy,
  ExternalLink,
  Layers,
  Video,
  Radio,
  FileArchive,
  Image as ImageIcon,
  Crosshair,
  LogIn,
  LogOut,
  CreditCard,
  Maximize2,
  Volume2,
  VolumeX,
  RefreshCw,
  Plus,
  X
} from 'lucide-react'

import { API_BASE_URL } from '@/lib/config'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

export interface EvidenceClipData {
  clip_id: string
  event_id: string
  video_id: string
  clip_path: string
  clip_start_sec: number
  clip_end_sec: number
  pre_event_duration: number
  post_event_duration: number
  sha256: string
  file_size_bytes: number
  export_status: string
  created_at?: string
}

export interface ScreenshotData {
  screenshot_id: string
  event_id: string
  video_id: string
  camera_id?: string
  storage_path: string
  video_timestamp_sec: number
  source_frame: number
  sha256: string
  image_width: number
  image_height: number
  created_at: string
}

export interface SurveillanceEventData {
  event_id: string
  camera_id: string
  video_id: string
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
  event_metadata: Record<string, any>
  processing_status: string
  created_at: string
  clip?: EvidenceClipData | null
  camera_name?: string
}

export interface MonitoredZoneData {
  zone_id: string
  camera_id: string
  name: string
  zone_type: string
  coordinates: number[][]
  boundary_line?: number[][]
  is_active: boolean
  camera_name?: string
}

export function EventReviewView() {
  const [events, setEvents] = useState<SurveillanceEventData[]>([])
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [screenshots, setScreenshots] = useState<ScreenshotData[]>([])
  const [loadingScreenshots, setLoadingScreenshots] = useState<boolean>(false)

  // Filtering & search
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc')

  // Video playback controls
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const [currentTime, setCurrentTime] = useState<number>(0)
  const [duration, setDuration] = useState<number>(0)
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1)
  const [isMuted, setIsMuted] = useState<boolean>(true)
  const [capturingScreenshot, setCapturingScreenshot] = useState<boolean>(false)
  const [exportingPackage, setExportingPackage] = useState<boolean>(false)
  const [copiedHash, setCopiedHash] = useState<boolean>(false)

  // Zones & live controls modal state
  const [showZonesModal, setShowZonesModal] = useState<boolean>(false)
  const [showLiveModal, setShowLiveModal] = useState<boolean>(false)
  const [zones, setZones] = useState<MonitoredZoneData[]>([])
  const [liveStreamPaused, setLiveStreamPaused] = useState<boolean>(false)
  const [liveCapturePaused, setLiveCapturePaused] = useState<boolean>(false)

  // Fetch events on mount
  const fetchEvents = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await axios.get(`${API_BASE_URL}/api/v1/events?limit=100`)
      const items: SurveillanceEventData[] = res.data.items || []
      setEvents(items)
      if (items.length > 0 && !selectedEventId) {
        setSelectedEventId(items[0].event_id)
      }
    } catch (err: any) {
      console.error('Failed to load surveillance events:', err)
      setError(err?.response?.data?.detail || 'Failed to connect to Surveillance Event API')
    } finally {
      setLoading(false)
    }
  }

  // Fetch zones
  const fetchZones = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/v1/zones`)
      setZones(res.data || [])
    } catch (err) {
      console.warn('Failed to fetch zones:', err)
    }
  }

  useEffect(() => {
    fetchEvents()
    fetchZones()
  }, [])

  // Selected event object
  const currentEvent = useMemo(() => {
    return events.find((e) => e.event_id === selectedEventId) || null
  }, [events, selectedEventId])

  // Fetch screenshots whenever selected event changes
  useEffect(() => {
    if (!currentEvent) {
      setScreenshots([])
      return
    }
    const fetchScreenshots = async () => {
      try {
        setLoadingScreenshots(true)
        const res = await axios.get(`${API_BASE_URL}/api/v1/events/${currentEvent.event_id}/screenshots`)
        setScreenshots(res.data || [])
      } catch (err) {
        console.warn('Failed to load screenshots:', err)
      } finally {
        setLoadingScreenshots(false)
      }
    }
    fetchScreenshots()
  }, [currentEvent])

  // Reset video state when selected event changes
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.pause()
      setIsPlaying(false)
      setCurrentTime(0)
      videoRef.current.playbackRate = playbackSpeed
    }
  }, [selectedEventId, playbackSpeed])

  // Video event handlers
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime)
    }
  }

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration)
      // Auto-jump to exact event instant if pre_event_duration is known
      if (currentEvent?.clip?.pre_event_duration) {
        videoRef.current.currentTime = currentEvent.clip.pre_event_duration
        setCurrentTime(currentEvent.clip.pre_event_duration)
      }
    }
  }

  const togglePlay = () => {
    if (!videoRef.current) return
    if (isPlaying) {
      videoRef.current.pause()
      setIsPlaying(false)
    } else {
      videoRef.current.play()
      setIsPlaying(true)
    }
  }

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed)
    if (videoRef.current) {
      videoRef.current.playbackRate = speed
    }
  }

  const jumpToEvent = () => {
    if (!videoRef.current || !currentEvent?.clip) return
    const eventTime = currentEvent.clip.pre_event_duration
    videoRef.current.currentTime = eventTime
    setCurrentTime(eventTime)
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value)
    if (videoRef.current) {
      videoRef.current.currentTime = val
      setCurrentTime(val)
    }
  }

  const handleStepFrame = (forward: boolean) => {
    if (!videoRef.current) return
    const step = forward ? 0.04 : -0.04 // ~1 frame at 25fps
    videoRef.current.currentTime = Math.max(0, Math.min(duration, videoRef.current.currentTime + step))
  }

  const handleSkip = (seconds: number) => {
    if (!videoRef.current) return
    videoRef.current.currentTime = Math.max(0, Math.min(duration, videoRef.current.currentTime + seconds))
  }

  // Navigation between events
  const currentIndex = useMemo(() => {
    return events.findIndex((e) => e.event_id === selectedEventId)
  }, [events, selectedEventId])

  const handlePrevEvent = () => {
    if (currentIndex > 0) {
      setSelectedEventId(events[currentIndex - 1].event_id)
    }
  }

  const handleNextEvent = () => {
    if (currentIndex < events.length - 1) {
      setSelectedEventId(events[currentIndex + 1].event_id)
    }
  }

  // Capture Screenshot at current playhead
  const handleCaptureScreenshot = async () => {
    if (!currentEvent) return
    try {
      setCapturingScreenshot(true)
      const res = await axios.post(`${API_BASE_URL}/api/v1/events/${currentEvent.event_id}/screenshots`, {
        clip_timestamp_sec: currentTime
      })
      setScreenshots((prev) => [res.data, ...prev])
    } catch (err: any) {
      alert(`Screenshot capture failed: ${err?.response?.data?.detail || err.message}`)
    } finally {
      setCapturingScreenshot(false)
    }
  }

  // Export Forensic Package
  const handleExportPackage = async () => {
    if (!currentEvent) return
    try {
      setExportingPackage(true)
      const res = await axios.post(`${API_BASE_URL}/api/v1/events/export`, {
        event_ids: [currentEvent.event_id],
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
      alert(`Export package generation failed: ${err?.response?.data?.detail || err.message}`)
    } finally {
      setExportingPackage(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedHash(true)
    setTimeout(() => setCopiedHash(false), 2000)
  }

  // Filtered and sorted events
  const filteredEvents = useMemo(() => {
    let result = [...events]
    if (typeFilter !== 'all') {
      result = result.filter((e) => e.event_type === typeFilter)
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      result = result.filter(
        (e) =>
          (e.person_number && `subject #${e.person_number}`.toLowerCase().includes(q)) ||
          e.event_type.toLowerCase().includes(q) ||
          (e.zone_name && e.zone_name.toLowerCase().includes(q)) ||
          (e.event_metadata?.description && e.event_metadata.description.toLowerCase().includes(q))
      )
    }
    result.sort((a, b) => {
      const timeA = new Date(a.event_timestamp).getTime()
      const timeB = new Date(b.event_timestamp).getTime()
      return sortOrder === 'desc' ? timeB - timeA : timeA - timeB
    })
    return result
  }, [events, typeFilter, searchQuery, sortOrder])

  // Helper for event type styling
  const getEventTypeMeta = (type: string) => {
    switch (type) {
      case 'person_entry':
        return {
          label: 'Person Entry',
          icon: LogIn,
          badgeClass: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
          dotClass: 'bg-emerald-500'
        }
      case 'person_exit':
        return {
          label: 'Person Exit',
          icon: LogOut,
          badgeClass: 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30',
          dotClass: 'bg-rose-500'
        }
      case 'transaction_start':
        return {
          label: 'Transaction Start',
          icon: CreditCard,
          badgeClass: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30',
          dotClass: 'bg-amber-500'
        }
      case 'inferred_transaction':
        return {
          label: 'Inferred Session',
          icon: Clock,
          badgeClass: 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30',
          dotClass: 'bg-blue-500'
        }
      default:
        return {
          label: type.replace('_', ' '),
          icon: Shield,
          badgeClass: 'bg-muted text-muted-foreground border-border',
          dotClass: 'bg-gray-400'
        }
    }
  }

  // Resolve clip URL
  const clipSrc = useMemo(() => {
    if (!currentEvent?.clip?.clip_path) return ''
    const p = currentEvent.clip.clip_path
    return p.startsWith('http') ? p : `${API_BASE_URL}${p}`
  }, [currentEvent])

  const eventPositionRatio = useMemo(() => {
    if (!currentEvent?.clip || !duration) return 0.5
    return (currentEvent.clip.pre_event_duration / duration) * 100
  }, [currentEvent, duration])

  return (
    <div className="flex flex-col gap-6">
      {/* Top Header Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">Event Evidence Review</h1>
            <Badge variant="outline" className="gap-1.5 border-primary/30 bg-primary/5 text-primary text-xs">
              <span className="size-1.5 rounded-full bg-primary animate-pulse" />
              Automated 20s Ring Buffers
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Forensic video surveillance timeline with 10s pre-event & 10s post-event context verification
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowZonesModal(true)}
            className="gap-2 border-border/80"
          >
            <Layers className="size-4 text-primary" />
            Monitored Zones ({zones.length})
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowLiveModal(true)}
            className="gap-2 border-border/80"
          >
            <Radio className={cn('size-4', liveCapturePaused ? 'text-amber-500' : 'text-emerald-500 animate-pulse')} />
            Camera Controls
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={fetchEvents}
            disabled={loading}
            className="gap-2"
          >
            <RefreshCw className={cn('size-4', loading && 'animate-spin')} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Main 3-Column Review Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* LEFT PANEL: Event Timeline & Filters (col-span-3) */}
        <div className="lg:col-span-3 flex flex-col gap-3">
          <Card className="p-4 border-border/70 flex flex-col gap-3 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Surveillance Timeline
              </span>
              <span className="text-xs font-medium bg-muted px-2 py-0.5 rounded-full text-foreground">
                {filteredEvents.length} Events
              </span>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 size-3.5 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search subject, zone..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 h-8 text-xs bg-muted/40"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-2 text-muted-foreground hover:text-foreground"
                >
                  <X className="size-3.5" />
                </button>
              )}
            </div>

            {/* Filter Pills */}
            <div className="flex flex-wrap gap-1">
              {[
                { id: 'all', label: 'All' },
                { id: 'person_entry', label: 'Entry' },
                { id: 'person_exit', label: 'Exit' },
                { id: 'transaction_start', label: 'Tx Start' }
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setTypeFilter(f.id)}
                  className={cn(
                    'px-2 py-1 text-xs rounded-md font-medium transition-colors',
                    typeFilter === f.id
                      ? 'bg-primary text-primary-foreground shadow-xs'
                      : 'bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground'
                  )}
                >
                  {f.label}
                </button>
              ))}
            </div>

            {/* Sort Toggle */}
            <div className="flex items-center justify-between pt-1 border-t border-border/50 text-[11px] text-muted-foreground">
              <span>Ordering</span>
              <button
                onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
                className="hover:text-foreground font-medium flex items-center gap-1"
              >
                {sortOrder === 'desc' ? 'Newest First' : 'Oldest First'}
              </button>
            </div>
          </Card>

          {/* Timeline Event List */}
          <div className="flex flex-col gap-2 max-h-[720px] overflow-y-auto pr-1">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-16 gap-3 text-muted-foreground">
                <RefreshCw className="size-6 animate-spin text-primary" />
                <span className="text-xs">Loading surveillance events...</span>
              </div>
            ) : filteredEvents.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border p-8 text-center text-muted-foreground">
                <Shield className="size-8 mx-auto mb-2 opacity-40" />
                <p className="text-xs font-medium">No events found matching criteria</p>
                <p className="text-[11px] mt-1 opacity-70">Adjust search or filter parameters</p>
              </div>
            ) : (
              filteredEvents.map((ev) => {
                const meta = getEventTypeMeta(ev.event_type)
                const Icon = meta.icon
                const isSelected = ev.event_id === selectedEventId
                const clipDuration = ev.clip
                  ? (ev.clip.pre_event_duration + ev.clip.post_event_duration).toFixed(1)
                  : null

                return (
                  <div
                    key={ev.event_id}
                    onClick={() => setSelectedEventId(ev.event_id)}
                    className={cn(
                      'group relative flex flex-col gap-2 p-3.5 rounded-xl border transition-all cursor-pointer text-left',
                      isSelected
                        ? 'border-primary/60 bg-primary/5 shadow-xs ring-1 ring-primary/40'
                        : 'border-border/60 bg-card hover:border-border hover:bg-accent/40'
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <Badge variant="outline" className={cn('gap-1 text-[11px] font-semibold py-0.5', meta.badgeClass)}>
                        <Icon className="size-3" />
                        {meta.label}
                      </Badge>
                      <span className="font-mono text-[11px] text-muted-foreground">
                        {ev.video_timestamp_sec.toFixed(1)}s
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs font-medium">
                      <span className="text-foreground flex items-center gap-1.5">
                        <User className="size-3.5 text-primary" />
                        {ev.person_number ? `Subject #${ev.person_number}` : 'Unidentified Person'}
                      </span>
                      <span className="text-[11px] text-muted-foreground">
                        {(ev.confidence * 100).toFixed(0)}% conf
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-muted-foreground border-t border-border/40 pt-1.5 mt-0.5">
                      <span className="truncate max-w-[140px]">{ev.zone_name || 'Monitored Area'}</span>
                      {clipDuration && (
                        <span className="font-mono bg-muted/80 px-1.5 py-0.5 rounded text-[10px] text-foreground">
                          {clipDuration}s clip
                        </span>
                      )}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* CENTER PANEL: Video Player with Event Markers & Forensic Scrubbing (col-span-6) */}
        <div className="lg:col-span-6 flex flex-col gap-3">
          <Card className="overflow-hidden border-border/80 shadow-md bg-black/90 text-white flex flex-col">
            {/* Player Header */}
            <div className="flex items-center justify-between px-4 py-2.5 bg-zinc-950/90 border-b border-zinc-800 text-xs">
              <div className="flex items-center gap-2">
                <Video className="size-4 text-primary" />
                <span className="font-semibold text-zinc-100">
                  {currentEvent?.camera_name || 'ATM-04 Main Vestibule'}
                </span>
                <span className="text-zinc-500">|</span>
                <span className="font-mono text-zinc-400">
                  {currentEvent?.event_type.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-800 text-emerald-400 text-[10px] font-mono">
                  <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  EVIDENCE CLIP
                </span>
              </div>
            </div>

            {/* Video Viewport */}
            <div className="relative aspect-video bg-black flex items-center justify-center group">
              {clipSrc ? (
                <video
                  ref={videoRef}
                  src={clipSrc}
                  className="w-full h-full object-contain"
                  playsInline
                  muted={isMuted}
                  onTimeUpdate={handleTimeUpdate}
                  onLoadedMetadata={handleLoadedMetadata}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onClick={togglePlay}
                />
              ) : (
                <div className="flex flex-col items-center justify-center p-8 text-zinc-500 gap-2">
                  <Video className="size-10 opacity-30" />
                  <p className="text-xs">No clip available for current event</p>
                </div>
              )}

              {/* On-Screen Watermark & Forensic Data HUD */}
              <div className="absolute top-3 left-3 pointer-events-none flex flex-col gap-1 text-[11px] font-mono drop-shadow-md">
                <div className="bg-black/60 backdrop-blur-xs px-2 py-0.5 rounded text-white flex items-center gap-1.5">
                  <span className="size-2 rounded-full bg-red-500 animate-pulse" />
                  REC: {currentEvent?.camera_name || 'ATM-04'}
                </div>
                <div className="bg-black/60 backdrop-blur-xs px-2 py-0.5 rounded text-zinc-300">
                  FRAME: {currentEvent ? Math.round(currentTime * 25) : 0} | T: {currentTime.toFixed(2)}s
                </div>
              </div>

              {/* Event Marker Overlay Tag on video screen */}
              {currentEvent?.clip && (
                <div className="absolute top-3 right-3 pointer-events-none bg-primary/90 text-primary-foreground font-mono text-[10px] px-2 py-0.5 rounded-full shadow-md flex items-center gap-1">
                  <Crosshair className="size-3" />
                  EVENT AT {currentEvent.clip.pre_event_duration.toFixed(1)}s
                </div>
              )}

              {/* Big Play Button Overlay on Hover/Pause */}
              {!isPlaying && clipSrc && (
                <button
                  onClick={togglePlay}
                  className="absolute inset-0 m-auto size-14 rounded-full bg-primary/90 text-primary-foreground flex items-center justify-center shadow-lg transition-transform hover:scale-110 active:scale-95"
                >
                  <Play className="size-6 ml-0.5" />
                </button>
              )}
            </div>

            {/* Custom Forensic Playback Timeline & Scrubber */}
            <div className="p-4 bg-zinc-950 flex flex-col gap-3 border-t border-zinc-800">
              {/* Scrub bar with pre/post event zones and event marker */}
              <div className="relative flex flex-col gap-1">
                {/* Visual Context Badges above scrubber */}
                <div className="flex items-center justify-between text-[10px] font-mono text-zinc-400">
                  <span className="flex items-center gap-1 text-emerald-400">
                    ◀ 10s Pre-Event Context ({currentEvent?.clip?.pre_event_duration.toFixed(1)}s)
                  </span>
                  <span className="flex items-center gap-1 text-sky-400">
                    10s Post-Event Context ({currentEvent?.clip?.post_event_duration.toFixed(1)}s) ▶
                  </span>
                </div>

                <div className="relative w-full h-3 flex items-center">
                  {/* Event Marker Flag */}
                  {currentEvent?.clip && duration > 0 && (
                    <div
                      className="absolute z-20 -top-2 flex flex-col items-center pointer-events-none transform -translate-x-1/2"
                      style={{ left: `${eventPositionRatio}%` }}
                    >
                      <div className="size-2 rounded-full bg-amber-400 ring-2 ring-black" />
                      <div className="w-0.5 h-6 bg-amber-400/80" />
                    </div>
                  )}

                  {/* Range Slider */}
                  <input
                    type="range"
                    min={0}
                    max={duration || 100}
                    step={0.01}
                    value={currentTime}
                    onChange={handleSeek}
                    className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-primary focus:outline-hidden"
                  />
                </div>

                {/* Timestamps */}
                <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                  <span>{currentTime.toFixed(2)}s</span>
                  <button
                    onClick={jumpToEvent}
                    className="text-[11px] font-sans font-medium text-amber-400 hover:text-amber-300 underline underline-offset-2 flex items-center gap-1"
                  >
                    <Crosshair className="size-3" />
                    Jump to Event Instant ({currentEvent?.clip?.pre_event_duration.toFixed(1)}s)
                  </button>
                  <span>{duration.toFixed(2)}s</span>
                </div>
              </div>

              {/* Controls Toolbar */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                {/* Playback & Frame Seeking */}
                <div className="flex items-center gap-1.5">
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={handlePrevEvent}
                    disabled={currentIndex <= 0}
                    title="Previous Detected Event"
                    className="text-zinc-300 hover:text-white hover:bg-zinc-800"
                  >
                    <ArrowLeft className="size-4" />
                  </Button>

                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => handleSkip(-5)}
                    title="Rewind 5s"
                    className="text-zinc-300 hover:text-white hover:bg-zinc-800"
                  >
                    <Rewind className="size-4" />
                  </Button>

                  <Button
                    variant="default"
                    size="icon-sm"
                    onClick={togglePlay}
                    className="rounded-full bg-primary hover:bg-primary/90 text-primary-foreground size-8"
                  >
                    {isPlaying ? <Pause className="size-4" /> : <Play className="size-4 ml-0.5" />}
                  </Button>

                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => handleSkip(5)}
                    title="Fast Forward 5s"
                    className="text-zinc-300 hover:text-white hover:bg-zinc-800"
                  >
                    <FastForward className="size-4" />
                  </Button>

                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={handleNextEvent}
                    disabled={currentIndex >= events.length - 1}
                    title="Next Detected Event"
                    className="text-zinc-300 hover:text-white hover:bg-zinc-800"
                  >
                    <ArrowRight className="size-4" />
                  </Button>
                </div>

                {/* Speed Controls: 0.5x, 1x, 2x */}
                <div className="flex items-center gap-1 bg-zinc-900 p-1 rounded-lg border border-zinc-800">
                  {[0.5, 1, 2].map((s) => (
                    <button
                      key={s}
                      onClick={() => handleSpeedChange(s)}
                      className={cn(
                        'px-2 py-0.5 text-xs font-mono rounded transition-colors',
                        playbackSpeed === s
                          ? 'bg-primary text-primary-foreground font-semibold'
                          : 'text-zinc-400 hover:text-zinc-200'
                      )}
                    >
                      {s}×
                    </button>
                  ))}
                </div>

                {/* Right side controls: Audio toggle & Screenshot */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => setIsMuted(!isMuted)}
                    className="text-zinc-300 hover:text-white hover:bg-zinc-800"
                    title={isMuted ? 'Unmute' : 'Mute'}
                  >
                    {isMuted ? <VolumeX className="size-4" /> : <Volume2 className="size-4" />}
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCaptureScreenshot}
                    disabled={capturingScreenshot || !currentEvent}
                    className="gap-1.5 bg-zinc-900 border-zinc-700 text-zinc-100 hover:bg-zinc-800 text-xs"
                  >
                    <Camera className={cn('size-3.5', capturingScreenshot && 'animate-spin')} />
                    Capture Frame
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          {/* Screenshot Evidence Gallery */}
          <Card className="p-4 border-border/80 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <ImageIcon className="size-4 text-primary" />
                Captured Evidence Frames ({screenshots.length})
              </span>
              <span className="text-[11px] text-muted-foreground">SHA-256 Verified</span>
            </div>

            {loadingScreenshots ? (
              <div className="py-6 text-center text-xs text-muted-foreground">Loading screenshots...</div>
            ) : screenshots.length === 0 ? (
              <div className="rounded-lg border border-dashed border-border/80 p-4 text-center text-muted-foreground text-xs">
                No forensic frames captured for this event yet.
                <Button
                  variant="link"
                  size="sm"
                  onClick={handleCaptureScreenshot}
                  className="block mx-auto mt-1 text-primary text-xs h-auto p-0"
                >
                  Capture current video frame
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {screenshots.map((shot) => {
                  const shotUrl = shot.storage_path.startsWith('http')
                    ? shot.storage_path
                    : `${API_BASE_URL}${shot.storage_path}`
                  return (
                    <div
                      key={shot.screenshot_id}
                      className="group relative flex flex-col rounded-lg border border-border/70 overflow-hidden bg-card hover:border-primary/50 transition-all"
                    >
                      <div className="relative aspect-video bg-muted overflow-hidden">
                        <img
                          src={shotUrl}
                          alt="Screenshot"
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                        />
                        <a
                          href={shotUrl}
                          download
                          target="_blank"
                          rel="noreferrer"
                          className="absolute bottom-1 right-1 bg-black/70 hover:bg-black p-1 rounded text-white"
                          title="Download Frame"
                        >
                          <Download className="size-3" />
                        </a>
                      </div>
                      <div className="p-1.5 text-[10px] font-mono text-muted-foreground flex flex-col gap-0.5">
                        <div className="flex justify-between text-foreground font-medium">
                          <span>Frame #{shot.source_frame}</span>
                          <span>{shot.video_timestamp_sec.toFixed(2)}s</span>
                        </div>
                        <span className="truncate text-[9px] text-muted-foreground font-mono">
                          {shot.sha256.substring(0, 16)}...
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </Card>
        </div>

        {/* RIGHT PANEL: Forensic Details, SHA-256 Digest & Evidence Export (col-span-3) */}
        <div className="lg:col-span-3 flex flex-col gap-4">
          {currentEvent ? (
            <>
              {/* Event Metadata Card */}
              <Card className="p-4 border-border/80 flex flex-col gap-3 shadow-xs">
                <div className="flex items-center justify-between pb-2 border-b border-border/60">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Event Metadata
                  </span>
                  <Badge variant="outline" className="gap-1 border-primary/30 text-[11px] text-primary">
                    <CheckCircle2 className="size-3 text-emerald-500" />
                    Verified
                  </Badge>
                </div>

                <div className="flex flex-col gap-2.5 text-xs">
                  <div>
                    <span className="text-[11px] text-muted-foreground block">Event Classification</span>
                    <span className="font-semibold text-foreground text-sm">
                      {getEventTypeMeta(currentEvent.event_type).label}
                    </span>
                  </div>

                  <div>
                    <span className="text-[11px] text-muted-foreground block">Detection Source</span>
                    <span className="font-mono text-xs text-foreground bg-muted/60 px-1.5 py-0.5 rounded">
                      {currentEvent.source}
                    </span>
                  </div>

                  <div>
                    <span className="text-[11px] text-muted-foreground block">Camera Location</span>
                    <span className="font-medium text-foreground flex items-center gap-1 mt-0.5">
                      <MapPin className="size-3 text-primary shrink-0" />
                      {currentEvent.camera_name || 'ATM-04 Main Vestibule'}
                    </span>
                  </div>

                  <div>
                    <span className="text-[11px] text-muted-foreground block">Monitored Zone</span>
                    <span className="font-medium text-foreground">
                      {currentEvent.zone_name || 'ATM Interaction Zone'}
                    </span>
                  </div>

                  <div>
                    <span className="text-[11px] text-muted-foreground block">Subject Track Reference</span>
                    <span className="font-medium text-foreground flex items-center gap-1 mt-0.5">
                      <User className="size-3 text-primary shrink-0" />
                      {currentEvent.person_number ? `Subject #${currentEvent.person_number}` : 'N/A'}
                    </span>
                  </div>

                  <div>
                    <span className="text-[11px] text-muted-foreground block">Source Video Position</span>
                    <span className="font-mono text-xs text-foreground">
                      {currentEvent.video_timestamp_sec.toFixed(2)}s (Frame #{currentEvent.source_frame})
                    </span>
                  </div>

                  <div>
                    <span className="text-[11px] text-muted-foreground block">Recorded UTC Timestamp</span>
                    <span className="font-mono text-[11px] text-muted-foreground">
                      {new Date(currentEvent.event_timestamp).toUTCString()}
                    </span>
                  </div>
                </div>
              </Card>

              {/* Forensic Hash & Clip Integrity Card */}
              <Card className="p-4 border-border/80 flex flex-col gap-3 shadow-xs">
                <div className="flex items-center justify-between pb-2 border-b border-border/60">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                    <ShieldCheck className="size-4 text-emerald-500" />
                    Forensic Hash & Chain of Custody
                  </span>
                </div>

                {currentEvent.clip ? (
                  <div className="flex flex-col gap-2.5 text-xs">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] text-muted-foreground">SHA-256 Clip Digest</span>
                        <button
                          onClick={() => copyToClipboard(currentEvent.clip!.sha256)}
                          className="text-[10px] text-primary hover:underline flex items-center gap-1"
                        >
                          {copiedHash ? 'Copied!' : <Copy className="size-3" />}
                        </button>
                      </div>
                      <div className="mt-1 font-mono text-[10px] break-all bg-muted/70 p-2 rounded border border-border/50 text-foreground">
                        {currentEvent.clip.sha256}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 pt-1">
                      <div className="bg-muted/40 p-2 rounded">
                        <span className="text-[10px] text-muted-foreground block">Context Window</span>
                        <span className="font-mono font-medium text-xs">
                          {(currentEvent.clip.pre_event_duration + currentEvent.clip.post_event_duration).toFixed(1)}s
                        </span>
                      </div>

                      <div className="bg-muted/40 p-2 rounded">
                        <span className="text-[10px] text-muted-foreground block">File Size</span>
                        <span className="font-mono font-medium text-xs">
                          {(currentEvent.clip.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                        </span>
                      </div>
                    </div>

                    <div className="pt-2 flex flex-col gap-2">
                      <a
                        href={clipSrc}
                        download={`evidence_${currentEvent.event_id}.mp4`}
                        className="w-full"
                      >
                        <Button variant="outline" size="sm" className="w-full gap-2 text-xs">
                          <Download className="size-3.5" />
                          Download MP4 Clip
                        </Button>
                      </a>

                      <Button
                        variant="default"
                        size="sm"
                        onClick={handleExportPackage}
                        disabled={exportingPackage}
                        className="w-full gap-2 text-xs bg-primary text-primary-foreground shadow-sm"
                      >
                        <FileArchive className={cn('size-3.5', exportingPackage && 'animate-spin')} />
                        {exportingPackage ? 'Packaging Dossier...' : 'Export Forensic Package (.ZIP)'}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-muted-foreground py-4 text-center">
                    No clip buffer registered.
                  </div>
                )}
              </Card>
            </>
          ) : (
            <div className="rounded-xl border border-dashed border-border p-8 text-center text-muted-foreground text-xs">
              Select an event from the timeline to review forensic details.
            </div>
          )}
        </div>
      </div>

      {/* MODAL 1: Monitored Zones Configuration */}
      {showZonesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <Card className="w-full max-w-xl p-6 border-border shadow-2xl bg-card flex flex-col gap-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Layers className="size-5 text-primary" />
                <h2 className="text-base font-bold">Monitored Zones & Tripwires</h2>
              </div>
              <button
                onClick={() => setShowZonesModal(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="size-5" />
              </button>
            </div>

            <div className="flex flex-col gap-3 max-h-[400px] overflow-y-auto">
              {zones.length === 0 ? (
                <div className="text-xs text-muted-foreground py-6 text-center">
                  No zones configured. Default full-view zone active.
                </div>
              ) : (
                zones.map((z) => (
                  <div
                    key={z.zone_id}
                    className="p-3.5 rounded-lg border border-border/80 bg-muted/30 flex flex-col gap-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm">{z.name}</span>
                      <Badge variant="outline" className={cn(z.is_active ? 'bg-emerald-500/15 text-emerald-500' : 'bg-muted')}>
                        {z.is_active ? 'ACTIVE' : 'DISABLED'}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground flex flex-col gap-1">
                      <span>Type: <strong className="text-foreground uppercase">{z.zone_type}</strong></span>
                      <span>Camera: <strong className="text-foreground">{z.camera_name || 'ATM-04 Main Vestibule'}</strong></span>
                      <span className="font-mono text-[11px] truncate">
                        Polygon: {JSON.stringify(z.coordinates)}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="flex justify-end pt-3 border-t border-border">
              <Button size="sm" onClick={() => setShowZonesModal(false)}>
                Close
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* MODAL 2: Live Camera Controls */}
      {showLiveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <Card className="w-full max-w-lg p-6 border-border shadow-2xl bg-card flex flex-col gap-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Radio className="size-5 text-emerald-500 animate-pulse" />
                <h2 className="text-base font-bold">Live Camera & Capture Controls</h2>
              </div>
              <button
                onClick={() => setShowLiveModal(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="size-5" />
              </button>
            </div>

            <div className="flex flex-col gap-4 text-xs">
              <div className="p-3 bg-muted/40 rounded-lg flex items-center justify-between">
                <div>
                  <span className="font-semibold block text-sm">ATM-04 Main Vestibule</span>
                  <span className="text-muted-foreground">RTSP Stream: Concourse B</span>
                </div>
                <Badge variant="outline" className="bg-emerald-500/15 text-emerald-500 border-emerald-500/30">
                  CONNECTED
                </Badge>
              </div>

              {liveCapturePaused && (
                <div className="p-3 bg-amber-500/15 border border-amber-500/30 text-amber-600 dark:text-amber-400 rounded-lg flex items-start gap-2">
                  <AlertTriangle className="size-4 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold block">Evidence Capture is Paused!</span>
                    <span>New surveillance events and ring buffers will NOT be recorded while capture is paused.</span>
                  </div>
                </div>
              )}

              <div className="flex flex-col gap-2 pt-2">
                <div className="flex items-center justify-between p-2.5 rounded border border-border">
                  <div>
                    <span className="font-semibold block">Live Preview Display</span>
                    <span className="text-muted-foreground text-[11px]">
                      Pausing preview does NOT stop background evidence recording.
                    </span>
                  </div>
                  <Button
                    variant={liveStreamPaused ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setLiveStreamPaused(!liveStreamPaused)}
                  >
                    {liveStreamPaused ? 'Resume Preview' : 'Pause Preview'}
                  </Button>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded border border-border">
                  <div>
                    <span className="font-semibold block">Underlying Evidence Capture</span>
                    <span className="text-muted-foreground text-[11px]">
                      Stops buffering new frames for event triggers.
                    </span>
                  </div>
                  <Button
                    variant={liveCapturePaused ? 'default' : 'destructive'}
                    size="sm"
                    onClick={() => setLiveCapturePaused(!liveCapturePaused)}
                  >
                    {liveCapturePaused ? 'Resume Capture' : 'Pause Capture'}
                  </Button>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-border">
              <Button size="sm" onClick={() => setShowLiveModal(false)}>
                Done
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
