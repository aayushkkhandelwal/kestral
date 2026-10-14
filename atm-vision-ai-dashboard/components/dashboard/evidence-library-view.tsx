'use client'

import { useState, useMemo } from 'react'
import Image from 'next/image'
import {
  Archive,
  Search,
  Filter,
  Download,
  Maximize2,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  Layers,
  Eye,
  SlidersHorizontal,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { API_BASE_URL } from '@/lib/config'
import {
  type EvidenceTrack,
  type Investigation,
  formatTimestamp,
} from '@/lib/dashboard-data'
import { cn } from '@/lib/utils'

type EvidenceItem = EvidenceTrack & {
  caseId: string
  atmName: string
  caseDate: string
}

export function EvidenceLibraryView({
  investigations,
  activeTracks,
}: {
  investigations: Investigation[]
  activeTracks?: EvidenceTrack[] | null
}) {
  const [filter, setFilter] = useState<'all' | 'confirmed' | 'high' | 'standard'>('all')
  const [search, setSearch] = useState('')
  const [selectedInspect, setSelectedInspect] = useState<EvidenceItem | null>(null)

  // Aggregate all evidence items across all investigations + active tracks
  const allEvidence = useMemo<EvidenceItem[]>(() => {
    const items: EvidenceItem[] = []

    // 1. From active current analysis
    if (activeTracks && activeTracks.length > 0) {
      activeTracks.forEach((t) => {
        items.push({
          ...t,
          caseId: 'ACTIVE-SESSION',
          atmName: 'Current Surveillance Stream',
          caseDate: 'Just now',
        })
      })
    }

    // 2. From historical investigations
    investigations.forEach((inv) => {
      const tracks = inv.result?.evidence_tracks
      if (tracks && tracks.length > 0) {
        tracks.forEach((t) => {
          items.push({
            ...t,
            caseId: inv.id,
            atmName: inv.atm,
            caseDate: inv.date,
          })
        })
      }
    })

    // If still empty (first run before videos uploaded), provide clean default demonstration cards
    if (items.length === 0) {
      return [
        {
          track_id: 1,
          best_frame_idx: 142,
          best_timestamp: 5.68,
          quality_score: 0.94,
          sharpness_score: 0.92,
          exposure_score: 0.88,
          resolution_score: 0.95,
          symmetry_score: 0.91,
          crop_url: '/images/best-face.png',
          full_frame_url: '/images/atm-cctv.png',
          has_confirmed_face: true,
          caseId: 'INV-2048',
          atmName: 'ATM-114 · Downtown Branch',
          caseDate: 'Oct 14, 2026',
        },
        {
          track_id: 2,
          best_frame_idx: 89,
          best_timestamp: 3.56,
          quality_score: 0.87,
          sharpness_score: 0.85,
          exposure_score: 0.82,
          resolution_score: 0.89,
          symmetry_score: 0.84,
          crop_url: '/images/best-face.png',
          full_frame_url: '/images/atm-cctv.png',
          has_confirmed_face: true,
          caseId: 'INV-2047',
          atmName: 'ATM-087 · Riverside Mall',
          caseDate: 'Oct 13, 2026',
        },
        {
          track_id: 3,
          best_frame_idx: 215,
          best_timestamp: 8.6,
          quality_score: 0.76,
          sharpness_score: 0.74,
          exposure_score: 0.79,
          resolution_score: 0.75,
          symmetry_score: 0.73,
          crop_url: '/images/best-face.png',
          full_frame_url: '/images/atm-cctv.png',
          has_confirmed_face: false,
          caseId: 'INV-2046',
          atmName: 'ATM-203 · Central Station',
          caseDate: 'Oct 12, 2026',
        },
        {
          track_id: 4,
          best_frame_idx: 320,
          best_timestamp: 12.8,
          quality_score: 0.89,
          sharpness_score: 0.91,
          exposure_score: 0.86,
          resolution_score: 0.9,
          symmetry_score: 0.88,
          crop_url: '/images/best-face.png',
          full_frame_url: '/images/atm-cctv.png',
          has_confirmed_face: true,
          caseId: 'INV-2044',
          atmName: 'ATM-131 · West End Plaza',
          caseDate: 'Oct 10, 2026',
        },
      ]
    }

    return items
  }, [investigations, activeTracks])

  const filtered = useMemo(() => {
    return allEvidence.filter((item) => {
      if (filter === 'confirmed' && !item.has_confirmed_face) return false
      if (filter === 'high' && (item.quality_score || 0) < 0.8) return false
      if (filter === 'standard' && (item.quality_score || 0) >= 0.8) return false

      if (search.trim()) {
        const q = search.toLowerCase()
        return (
          item.caseId.toLowerCase().includes(q) ||
          item.atmName.toLowerCase().includes(q) ||
          `track ${item.track_id}`.toLowerCase().includes(q)
        )
      }
      return true
    })
  }, [allEvidence, filter, search])

  const handleDownloadCrop = (item: EvidenceItem, e: React.MouseEvent) => {
    e.stopPropagation()
    const src = item.crop_url.startsWith('http') || item.crop_url.startsWith('/')
      ? item.crop_url.startsWith('http') || item.crop_url.startsWith('/images')
        ? item.crop_url
        : `${API_BASE_URL}${item.crop_url}`
      : `${API_BASE_URL}/${item.crop_url}`

    const link = document.createElement('a')
    link.href = src
    link.download = `kestral_evidence_${item.caseId}_track_${item.track_id}.jpg`
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    link.remove()
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground md:text-3xl">
            Biometric Evidence Vault
          </h1>
          <p className="text-sm text-muted-foreground">
            Optimal facial captures and biometric clarity ratings isolated across all surveillance cases
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="px-3 py-1 font-mono text-xs">
            {allEvidence.length} Evidence Frames Captured
          </Badge>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col gap-3 rounded-xl border bg-card p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-1.5">
          <Button
            variant={filter === 'all' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setFilter('all')}
            className="text-xs"
          >
            All Evidence ({allEvidence.length})
          </Button>
          <Button
            variant={filter === 'confirmed' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setFilter('confirmed')}
            className="text-xs"
          >
            Confirmed Faces
          </Button>
          <Button
            variant={filter === 'high' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setFilter('high')}
            className="text-xs"
          >
            High Quality (80%+)
          </Button>
          <Button
            variant={filter === 'standard' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setFilter('standard')}
            className="text-xs"
          >
            Standard (&lt;80%)
          </Button>
        </div>

        <div className="relative w-full max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by Case or Track..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-9 pl-9 text-xs"
          />
        </div>
      </div>

      {/* Gallery Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filtered.map((item, idx) => {
          const imgSrc = item.crop_url.startsWith('http') || item.crop_url.startsWith('/images')
            ? item.crop_url
            : `${API_BASE_URL}${item.crop_url}`
          const fidelityPct = Math.round((item.quality_score || 0) * 100)

          return (
            <div
              key={`${item.caseId}-${item.track_id}-${idx}`}
              className="group relative flex flex-col overflow-hidden rounded-2xl border bg-card shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg"
              onClick={() => setSelectedInspect(item)}
            >
              {/* Crop Visual */}
              <div className="relative aspect-square w-full bg-muted">
                <Image
                  src={imgSrc}
                  alt={`Evidence crop track ${item.track_id}`}
                  fill
                  sizes="(min-width: 1280px) 25vw, (min-width: 768px) 50vw, 100vw"
                  className="object-cover transition-transform duration-300 group-hover:scale-105"
                  unoptimized
                />
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-80" />

                {/* Badges */}
                <div className="absolute left-3 top-3 flex items-center gap-1.5">
                  <Badge className="bg-black/70 font-mono text-[11px] backdrop-blur-md">
                    Track #{item.track_id}
                  </Badge>
                  {item.has_confirmed_face && (
                    <Badge className="border-emerald-500/50 bg-emerald-950/80 text-[10px] text-emerald-300 backdrop-blur-md">
                      Confirmed Face
                    </Badge>
                  )}
                </div>

                <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-white">
                  <span className="font-mono text-xs font-semibold">
                    {formatTimestamp(item.best_timestamp)}
                  </span>
                  <span
                    className={cn(
                      'rounded-md px-1.5 py-0.5 font-mono text-xs font-bold',
                      fidelityPct >= 80 ? 'bg-emerald-500/90' : 'bg-primary/90'
                    )}
                  >
                    {fidelityPct}% Fidelity
                  </span>
                </div>
              </div>

              {/* Details & Telemetry */}
              <div className="flex flex-1 flex-col justify-between p-4">
                <div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="font-mono">{item.caseId}</span>
                    <span>{item.caseDate}</span>
                  </div>
                  <p className="mt-1 truncate text-sm font-semibold">{item.atmName}</p>
                </div>

                {/* Score bars */}
                <div className="mt-3 flex flex-col gap-1.5 border-t pt-3 text-xs text-muted-foreground">
                  <div className="flex items-center justify-between">
                    <span>Laplacian Sharpness</span>
                    <span className="font-mono font-medium text-foreground">
                      {item.sharpness_score?.toFixed(2) || '0.85'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Exposure Balance</span>
                    <span className="font-mono font-medium text-foreground">
                      {item.exposure_score?.toFixed(2) || '0.80'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Pixel Density</span>
                    <span className="font-mono font-medium text-foreground">
                      {item.resolution_score?.toFixed(2) || '0.90'}
                    </span>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="mt-4 grid grid-cols-2 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 gap-1 text-xs"
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedInspect(item)
                    }}
                  >
                    <Maximize2 className="size-3" />
                    Inspect
                  </Button>
                  <Button
                    size="sm"
                    className="h-8 gap-1 text-xs"
                    onClick={(e) => handleDownloadCrop(item, e)}
                  >
                    <Download className="size-3" />
                    Export
                  </Button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Full Resolution Comparison Modal */}
      {selectedInspect && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4 backdrop-blur-md"
          onClick={() => setSelectedInspect(null)}
        >
          <div
            className="relative flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border bg-card shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b px-6 py-4">
              <div>
                <h3 className="text-lg font-bold">
                  Biometric Evidence Dossier · Track #{selectedInspect.track_id}
                </h3>
                <p className="text-xs text-muted-foreground">
                  {selectedInspect.caseId} · {selectedInspect.atmName} · Captured at Frame #{selectedInspect.best_frame_idx}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={(e) => handleDownloadCrop(selectedInspect, e)}
                >
                  <Download className="size-4" /> Download Crop
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setSelectedInspect(null)}>
                  Close
                </Button>
              </div>
            </div>

            {/* Modal Body: Side-by-Side Comparison */}
            <div className="grid flex-1 gap-6 overflow-y-auto p-6 md:grid-cols-[1.5fr_1fr]">
              {/* Full Frame with bounding box visual */}
              <div className="flex flex-col gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Full 1080p Context Frame
                </span>
                <div className="relative aspect-video w-full overflow-hidden rounded-xl border bg-black">
                  <Image
                    src={
                      selectedInspect.full_frame_url.startsWith('http') || selectedInspect.full_frame_url.startsWith('/images')
                        ? selectedInspect.full_frame_url
                        : `${API_BASE_URL}${selectedInspect.full_frame_url}`
                    }
                    alt="Full context surveillance frame"
                    fill
                    sizes="100vw"
                    className="object-contain"
                    unoptimized
                  />
                </div>
              </div>

              {/* Crop & Metric Telemetry */}
              <div className="flex flex-col gap-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Localized Facial Evidence Crop
                </span>
                <div className="relative aspect-square max-w-[280px] overflow-hidden rounded-xl border bg-black">
                  <Image
                    src={
                      selectedInspect.crop_url.startsWith('http') || selectedInspect.crop_url.startsWith('/images')
                        ? selectedInspect.crop_url
                        : `${API_BASE_URL}${selectedInspect.crop_url}`
                    }
                    alt="Localized evidence crop"
                    fill
                    sizes="300px"
                    className="object-cover"
                    unoptimized
                  />
                  <div className="pointer-events-none absolute inset-[12%] rounded-md border-2 border-primary/80" />
                </div>

                <div className="flex flex-col divide-y rounded-xl border bg-muted/30 p-4 text-xs">
                  <div className="flex justify-between py-1.5">
                    <span className="text-muted-foreground">Overall Fidelity</span>
                    <span className="font-mono font-bold text-primary">
                      {Math.round((selectedInspect.quality_score || 0) * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-muted-foreground">Laplacian Variance</span>
                    <span className="font-mono font-medium">
                      {selectedInspect.sharpness_score?.toFixed(3)}
                    </span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-muted-foreground">Exposure Ratio</span>
                    <span className="font-mono font-medium">
                      {selectedInspect.exposure_score?.toFixed(3)}
                    </span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-muted-foreground">Facial Landmark Match</span>
                    <span className="font-medium text-emerald-500">
                      {selectedInspect.has_confirmed_face ? '5-Point Verified (YuNet)' : 'Estimated Profile'}
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
