import { ArrowUpRight, FolderSearch, ScanFace, Users, Video } from 'lucide-react'
import { cn } from '@/lib/utils'

const STATS = [
  {
    label: 'Videos Processed',
    value: '0',
    trend: '0%',
    description: '0 analyzed in system',
    icon: Video,
    tone: 'text-primary bg-primary/10',
    stroke: 'stroke-primary',
    fill: 'fill-primary/10',
    points: [0, 0, 0, 0, 0, 0, 0],
  },
  {
    label: 'People Detected',
    value: '0',
    trend: '0%',
    description: '0 tracked',
    icon: Users,
    tone: 'text-chart-4 bg-chart-4/10',
    stroke: 'stroke-chart-4',
    fill: 'fill-chart-4/10',
    points: [0, 0, 0, 0, 0, 0, 0],
  },
  {
    label: 'Faces Selected',
    value: '0',
    trend: '0%',
    description: 'Avg. quality 0.00',
    icon: ScanFace,
    tone: 'text-success bg-success/10',
    stroke: 'stroke-success',
    fill: 'fill-success/10',
    points: [0, 0, 0, 0, 0, 0, 0],
  },
  {
    label: 'Investigations',
    value: '0',
    trend: '0',
    description: '0 active cases',
    icon: FolderSearch,
    tone: 'text-warning bg-warning/15',
    stroke: 'stroke-warning',
    fill: 'fill-warning/15',
    points: [0, 0, 0, 0, 0, 0, 0],
  },
]

function Sparkline({ points, stroke, fill }: { points: number[]; stroke: string; fill: string }) {
  const w = 120
  const h = 36
  const max = Math.max(...points)
  const min = Math.min(...points)
  const coords = points.map((p, i) => {
    const x = (i / (points.length - 1)) * w
    const y = h - ((p - min) / (max - min || 1)) * (h - 4) - 2
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  const line = coords.join(' ')
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-9 w-full" preserveAspectRatio="none" aria-hidden="true">
      <polygon points={`0,${h} ${line} ${w},${h}`} className={cn(fill, 'stroke-none')} />
      <polyline
        points={line}
        className={cn(stroke, 'fill-none')}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  )
}

export type BackendStats = {
  total_videos_analyzed?: number
  total_persons_tracked?: number
  high_quality_evidence_captured?: number
  system_average_fidelity?: number
} | null

export function StatsCards({ stats }: { stats?: BackendStats }) {
  const cards = STATS.map((item, idx) => {
    if (!stats) return item

    if (idx === 0 && stats.total_videos_analyzed !== undefined) {
      return {
        ...item,
        value: stats.total_videos_analyzed.toLocaleString(),
        description: `${stats.total_videos_analyzed} analyzed in system`
      }
    }
    if (idx === 1 && stats.total_persons_tracked !== undefined) {
      return {
        ...item,
        value: stats.total_persons_tracked.toLocaleString(),
        description: 'Unique YOLO person tracks'
      }
    }
    if (idx === 2 && stats.high_quality_evidence_captured !== undefined) {
      return {
        ...item,
        value: stats.high_quality_evidence_captured.toLocaleString(),
        description: `Avg fidelity: ${stats.system_average_fidelity || 0}%`
      }
    }
    if (idx === 3 && stats.total_videos_analyzed !== undefined) {
      return {
        ...item,
        value: stats.total_videos_analyzed.toString(),
        description: 'Surveillance cases completed'
      }
    }
    return item
  })

  return (
    <section aria-label="Statistics" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map(({ label, value, trend, description, icon: Icon, tone, stroke, fill, points }) => (
        <div
          key={label}
          className="group flex flex-col gap-4 rounded-2xl border bg-card p-5 shadow-sm shadow-foreground/[0.03] transition-all hover:-translate-y-0.5 hover:shadow-md"
        >
          <div className="flex items-center justify-between">
            <div className={cn('flex size-9 items-center justify-center rounded-xl', tone)}>
              <Icon className="size-[18px]" aria-hidden="true" />
            </div>
            <span className="inline-flex items-center gap-0.5 rounded-full bg-success/10 px-2 py-0.5 text-xs font-medium text-success">
              <ArrowUpRight className="size-3" aria-hidden="true" />
              {trend}
            </span>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="mt-1 text-3xl font-semibold tracking-tight tabular-nums">{value}</p>
          </div>
          <div className="flex items-end justify-between gap-4">
            <p className="shrink-0 text-xs text-muted-foreground">{description}</p>
            <div className="w-24">
              <Sparkline points={points} stroke={stroke} fill={fill} />
            </div>
          </div>
        </div>
      ))}
    </section>
  )
}
