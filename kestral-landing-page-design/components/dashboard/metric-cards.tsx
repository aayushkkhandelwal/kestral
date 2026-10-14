import { ArrowUpRight, FolderSearch, ScanFace, Users, Video } from 'lucide-react'

const METRICS = [
  {
    label: 'Videos Processed',
    value: '8',
    hint: '8 analyzed in system',
    delta: '0%',
    icon: Video,
    tone: 'bg-primary/15 text-primary',
    bar: 'bg-primary',
  },
  {
    label: 'People Detected',
    value: '39',
    hint: 'Unique YOLO person tracks',
    delta: '0%',
    icon: Users,
    tone: 'bg-info/15 text-info',
    bar: 'bg-info',
  },
  {
    label: 'Faces Selected',
    value: '23',
    hint: 'Avg fidelity: 62.7%',
    delta: '0%',
    icon: ScanFace,
    tone: 'bg-success/15 text-success',
    bar: 'bg-success',
  },
  {
    label: 'Investigations',
    value: '8',
    hint: 'Surveillance cases completed',
    delta: '0',
    icon: FolderSearch,
    tone: 'bg-warning/15 text-warning',
    bar: 'bg-warning',
  },
]

export function MetricCards() {
  return (
    <section aria-label="Key metrics" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {METRICS.map((metric) => (
        <article key={metric.label} className="flex flex-col rounded-3xl border bg-card p-6">
          <div className="flex items-start justify-between gap-2">
            <span className={`inline-flex size-11 items-center justify-center rounded-full ${metric.tone}`}>
              <metric.icon className="size-5" strokeWidth={1.75} aria-hidden="true" />
            </span>
            <span className="inline-flex items-center gap-0.5 rounded-full bg-success/15 px-2 py-0.5 text-xs font-semibold text-success">
              <ArrowUpRight className="size-3" aria-hidden="true" />
              {metric.delta}
            </span>
          </div>
          <h2 className="mt-5 text-sm text-muted-foreground">{metric.label}</h2>
          <p className="mt-1 text-4xl font-bold tracking-tight">{metric.value}</p>
          <div className="mt-6 flex items-center justify-between gap-4">
            <p className="text-xs text-muted-foreground">{metric.hint}</p>
            <span className={`h-0.5 w-1/3 rounded-full ${metric.bar}`} aria-hidden="true" />
          </div>
        </article>
      ))}
    </section>
  )
}
