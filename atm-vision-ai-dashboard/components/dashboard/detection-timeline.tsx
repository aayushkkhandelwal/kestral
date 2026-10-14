import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { FACE_DETECTIONS, formatTimestamp, VIDEO_DURATION_SECONDS, type EvidenceTrack } from '@/lib/dashboard-data'
import { cn } from '@/lib/utils'
import { SectionHeader } from './section-header'

const TICKS = [0, 0.25, 0.5, 0.75, 1]

export function DetectionTimeline({
  loading,
  tracks,
  duration,
}: {
  loading: boolean
  tracks?: EvidenceTrack[] | null
  duration?: number
}) {
  const hasRealTracks = tracks && tracks.length > 0
  const maxTime = duration || (hasRealTracks ? Math.max(...tracks.map((t) => t.best_timestamp), 10) : VIDEO_DURATION_SECONDS)
  const totalDuration = Math.max(1, maxTime)

  const detections = hasRealTracks
    ? tracks.map((t) => ({
        trackId: `T-${t.track_id}`,
        seconds: t.best_timestamp,
        quality: t.quality_score,
        isBest: false,
      }))
    : FACE_DETECTIONS.map((d) => ({ ...d, isBest: d.seconds === 104 }))

  // Find best quality item
  let highestQuality = -1
  let bestIdx = -1
  detections.forEach((d, idx) => {
    if (d.quality > highestQuality) {
      highestQuality = d.quality
      bestIdx = idx
    }
  })
  if (bestIdx >= 0) {
    detections[bestIdx].isBest = true
  }

  const tracksCount = hasRealTracks ? tracks.length : 4

  return (
    <section aria-labelledby="timeline-heading" className="flex flex-col gap-4">
      <div id="timeline-heading">
        <SectionHeader
          title="Timeline"
          description={`${detections.length} face detections across ${tracksCount} tracks`}
          action={
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <span className="size-2 rounded-full bg-primary/60" aria-hidden="true" />
                Face detected
              </span>
              <span className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full bg-primary ring-2 ring-primary/30" aria-hidden="true" />
                Best frame
              </span>
            </div>
          }
        />
      </div>

      <div className="rounded-xl bg-card px-6 pt-8 pb-5 border">
        {loading ? (
          <div className="flex flex-col gap-4">
            <Skeleton className="h-2 w-full" />
            <div className="flex justify-between">
              {TICKS.map((t) => (
                <Skeleton key={t} className="h-3 w-10" />
              ))}
            </div>
          </div>
        ) : (
          <>
            <div className="relative h-2 rounded-full bg-muted">
              <ul aria-label="Face detections">
                {detections.map((d, index) => {
                  const leftPct = Math.min(100, Math.max(0, (d.seconds / totalDuration) * 100))
                  return (
                    <li
                      key={`${d.trackId}-${d.seconds}-${index}`}
                      className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
                      style={{ left: `${leftPct}%` }}
                    >
                      <Tooltip>
                        <TooltipTrigger
                          render={
                            <button
                              type="button"
                              aria-label={`${d.trackId} at ${formatTimestamp(d.seconds)}, quality ${d.quality.toFixed(2)}${d.isBest ? ', best frame' : ''}`}
                              className={cn(
                                'block rounded-full bg-primary transition-transform outline-none hover:scale-125 focus-visible:ring-2 focus-visible:ring-ring',
                                d.isBest ? 'size-4 ring-4 ring-primary/25' : 'size-2.5 opacity-70 hover:opacity-100',
                              )}
                            />
                          }
                        />
                        <TooltipContent>
                          <span className="font-mono">
                            {d.trackId} · {formatTimestamp(d.seconds)} · Q {(d.quality * 100).toFixed(0)}%
                            {d.isBest ? ' (Best Frame)' : ''}
                          </span>
                        </TooltipContent>
                      </Tooltip>
                    </li>
                  )
                })}
              </ul>
            </div>
            <div className="mt-4 flex justify-between font-mono text-[11px] text-muted-foreground tabular-nums">
              {TICKS.map((t) => (
                <span key={t}>{formatTimestamp(totalDuration * t)}</span>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  )
}
