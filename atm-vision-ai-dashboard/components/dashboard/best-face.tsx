import { useState } from 'react'
import Image from 'next/image'
import { Download, Maximize2, ExternalLink, ScanFace } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { API_BASE_URL } from '@/lib/config'
import { formatTimestamp, type EvidenceTrack } from '@/lib/dashboard-data'
import { SectionHeader } from './section-header'

export function BestFace({ loading, track }: { loading: boolean; track?: EvidenceTrack | null }) {
  const [showFullModal, setShowFullModal] = useState(false)

  const imgSrc = track?.crop_url ? `${API_BASE_URL}${track.crop_url}` : ''
  const fullSrc = track?.full_frame_url ? `${API_BASE_URL}${track.full_frame_url}` : imgSrc

  const details = track
    ? [
        { label: 'Timestamp', value: formatTimestamp(track.best_timestamp) },
        { label: 'Track ID', value: `Track #${track.track_id}` },
        { label: 'Quality Score', value: `${(track.quality_score * 100).toFixed(1)}%`, bar: track.quality_score },
        { label: 'Sharpness', value: track.sharpness_score.toFixed(2), bar: Math.min(1.0, track.sharpness_score) },
        { label: 'Exposure', value: track.exposure_score.toFixed(2), bar: Math.min(1.0, track.exposure_score) },
        { label: 'Biometric Status', value: track.has_confirmed_face ? 'Confirmed Facial Match' : 'Visual Profile Match' },
        { label: 'Resolution Density', value: track.resolution_score.toFixed(2), bar: Math.min(1.0, track.resolution_score) },
      ]
    : []

  const trackBadge = track
    ? `T-${track.track_id} · ${(track.quality_score * 100).toFixed(0)}%`
    : ''

  const handleExport = () => {
    const link = document.createElement('a')
    link.href = imgSrc
    link.download = `kestral_evidence_track_${track?.track_id || 'best'}.jpg`
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <section aria-labelledby="best-face-heading" className="flex flex-col gap-4">
      <div id="best-face-heading">
        <SectionHeader title="Best Face" description="Highest quality frame selected across all tracks" />
      </div>

      {!track && !loading ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed bg-card/50 p-8 text-center min-h-[220px]">
          <ScanFace className="size-10 text-muted-foreground/40 mb-2" />
          <h4 className="text-sm font-semibold text-foreground">No Evidence Track Selected</h4>
          <p className="mt-1 text-xs text-muted-foreground max-w-xs">
            Upload and process a surveillance video to isolate optimal biometric face captures.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] xl:grid-cols-1 2xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <div className="relative aspect-square overflow-hidden rounded-xl bg-card border">
            {loading ? (
              <Skeleton className="size-full rounded-none" />
            ) : (
              <>
                {imgSrc && (
                  <Image
                    src={imgSrc}
                    alt={`Best evidence frame: close-up for track ${track?.track_id}`}
                    fill
                    sizes="(min-width: 1280px) 30vw, (min-width: 768px) 50vw, 100vw"
                    className="object-cover"
                    unoptimized
                  />
                )}
                <div className="pointer-events-none absolute inset-[18%] rounded-lg border-2 border-primary/80" aria-hidden="true" />
                <Badge className="absolute top-3 left-3 font-mono">{trackBadge}</Badge>
              </>
            )}
          </div>

          <div className="flex flex-col rounded-xl bg-card p-5 border">
            <dl className="flex flex-1 flex-col divide-y divide-border/60">
              {details.map((item) => (
                <div key={item.label} className="flex items-center justify-between gap-4 py-2.5 first:pt-0">
                  <dt className="text-sm text-muted-foreground">{item.label}</dt>
                  <dd className="flex items-center gap-3">
                    {loading ? (
                      <Skeleton className="h-4 w-16" />
                    ) : (
                      <>
                        {item.bar !== undefined && (
                          <span className="hidden h-1 w-16 overflow-hidden rounded-full bg-muted sm:block" aria-hidden="true">
                            <span className="block h-full rounded-full bg-primary" style={{ width: `${Math.min(100, item.bar * 100)}%` }} />
                          </span>
                        )}
                        <span className="text-sm font-medium tabular-nums">{item.value}</span>
                      </>
                    )}
                  </dd>
                </div>
              ))}
            </dl>
            <div className="mt-5 grid grid-cols-2 gap-2">
              <Button
                variant="outline"
                disabled={loading || !track}
                onClick={() => setShowFullModal(true)}
              >
                <Maximize2 data-icon="inline-start" />
                View Frame
              </Button>
              <Button disabled={loading || !track} onClick={handleExport}>
                <Download data-icon="inline-start" />
                Export Evidence
              </Button>
            </div>
          </div>
        </div>
      )}

      {showFullModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm"
          onClick={() => setShowFullModal(false)}
        >
          <div
            className="relative max-h-[90vh] max-w-4xl overflow-hidden rounded-2xl bg-card border p-4 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-base font-semibold">
                Full Surveillance Frame {track ? `(Track #${track.track_id} · Frame #${track.best_frame_idx})` : ''}
              </h3>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => window.open(fullSrc, '_blank')}>
                  <ExternalLink className="size-4" /> Open Full
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setShowFullModal(false)}>
                  Close
                </Button>
              </div>
            </div>
            <div className="relative aspect-video max-h-[70vh] w-full overflow-hidden rounded-xl bg-black">
              <Image
                src={fullSrc}
                alt="Full frame surveillance evidence"
                fill
                sizes="100vw"
                className="object-contain"
                unoptimized
              />
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
