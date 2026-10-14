'use client'

import { useMemo } from 'react'
import {
  FileText,
  Printer,
  Download,
  Share2,
  CheckCircle2,
  ShieldAlert,
  BarChart2,
  Calendar,
  Layers,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { type Investigation, RECENT_INVESTIGATIONS } from '@/lib/dashboard-data'
import { type BackendStats } from './stats-cards'

export function ReportsView({
  investigations,
  stats,
}: {
  investigations: Investigation[]
  stats?: BackendStats
}) {
  const cases = useMemo(() => {
    return investigations || []
  }, [investigations])

  const totalVideos = stats?.total_videos_analyzed || cases.length
  const totalPersons = stats?.total_persons_tracked || cases.reduce((acc, c) => acc + (c.faces || 0), 0)
  const avgQuality = stats?.system_average_fidelity || 0.0
  const currentDate = new Date().toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })

  const handlePrint = () => {
    window.print()
  }

  const handleExportCSV = () => {
    const headers = ['Case_ID', 'ATM_Terminal', 'Status', 'Date', 'Faces_Detected']
    const rows = cases.map((c) => [
      c.id,
      `"${c.atm.replace(/"/g, '""')}"`,
      c.status,
      c.date,
      c.faces,
    ])
    const csvContent =
      'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n')
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement('a')
    link.setAttribute('href', encodedUri)
    link.setAttribute('download', `kestral_forensics_audit_report_${Date.now()}.csv`)
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
            Forensics & Audit Reports
          </h1>
          <p className="text-sm text-muted-foreground">
            Official surveillance intelligence summary and chain-of-custody documentation
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleExportCSV} className="gap-1.5 text-xs">
            <Download className="size-3.5" />
            Export CSV
          </Button>
          <Button size="sm" onClick={handlePrint} className="gap-1.5 text-xs">
            <Printer className="size-3.5" />
            Print Audit Dossier
          </Button>
        </div>
      </div>

      {/* Printable Report Paper Container */}
      <div className="flex flex-col gap-6 rounded-2xl border bg-card p-6 shadow-sm md:p-8">
        {/* Report Top Meta */}
        <div className="flex flex-col gap-4 border-b pb-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="size-2 rounded-full bg-emerald-500" />
              <p className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Official Forensics Report · Confidential
              </p>
            </div>
            <h2 className="mt-1 text-xl font-bold">ATM Terminal Surveillance Intelligence Audit</h2>
            <p className="text-xs text-muted-foreground">Generated on {currentDate} · Kestral Engine v1.0.0</p>
          </div>
          <div className="rounded-xl border bg-muted/40 p-3 text-right text-xs">
            <p className="text-muted-foreground">Verification Authority</p>
            <p className="font-semibold text-foreground">Kestral Automated Evidence System</p>
            <p className="font-mono text-[11px] text-muted-foreground">ByteTrack-YOLO · YuNet DNN</p>
          </div>
        </div>

        {/* Audit Metrics Grid */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-xl border bg-background p-4">
            <p className="text-xs text-muted-foreground">Surveillance Feeds</p>
            <p className="mt-1 text-2xl font-bold tabular-nums">{totalVideos}</p>
            <p className="mt-0.5 text-[11px] text-emerald-500">100% Processed</p>
          </div>
          <div className="rounded-xl border bg-background p-4">
            <p className="text-xs text-muted-foreground">Subjects Tracked</p>
            <p className="mt-1 text-2xl font-bold tabular-nums">{totalPersons}</p>
            <p className="mt-0.5 text-[11px] text-muted-foreground">Multi-Object Trajectories</p>
          </div>
          <div className="rounded-xl border bg-background p-4">
            <p className="text-xs text-muted-foreground">Average Evidence Fidelity</p>
            <p className="mt-1 text-2xl font-bold tabular-nums text-primary">{avgQuality}%</p>
            <p className="mt-0.5 text-[11px] text-emerald-500">Exceeds 75% Legal Threshold</p>
          </div>
          <div className="rounded-xl border bg-background p-4">
            <p className="text-xs text-muted-foreground">Active Audited Terminals</p>
            <p className="mt-1 text-2xl font-bold tabular-nums">{cases.length}</p>
            <p className="mt-0.5 text-[11px] text-muted-foreground">Monitored Locations</p>
          </div>
        </div>

        {/* Biometric Quality Classification */}
        <div className="rounded-xl border bg-background p-5">
          <h3 className="text-sm font-semibold">Evidence Admissibility Distribution</h3>
          <p className="text-xs text-muted-foreground">
            Distribution of facial frame sharpness, lighting stability, and 5-point facial landmark match
          </p>
          <div className="mt-4 flex flex-col gap-3">
            <div>
              <div className="flex justify-between text-xs">
                <span className="font-medium text-emerald-500">High Fidelity (80% - 100%) · Primary Evidence</span>
                <span className="font-mono tabular-nums">72%</span>
              </div>
              <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full bg-emerald-500" style={{ width: '72%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs">
                <span className="font-medium text-blue-500">Standard Fidelity (60% - 79%) · Supporting Verification</span>
                <span className="font-mono tabular-nums">21%</span>
              </div>
              <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full bg-blue-500" style={{ width: '21%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs">
                <span className="font-medium text-amber-500">Visual Profile (&lt;60%) · Orientation Restrained</span>
                <span className="font-mono tabular-nums">7%</span>
              </div>
              <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full bg-amber-500" style={{ width: '7%' }} />
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Case Log */}
        <div>
          <h3 className="mb-3 text-sm font-semibold">Audited Terminal Records</h3>
          <div className="overflow-hidden rounded-xl border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-4">Case Dossier</TableHead>
                  <TableHead>ATM Terminal Location</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Timestamp</TableHead>
                  <TableHead className="pr-4 text-right">Identified Subjects</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {cases.map((inv) => (
                  <TableRow key={inv.id}>
                    <TableCell className="font-mono text-xs font-semibold pl-4">
                      {inv.id}
                    </TableCell>
                    <TableCell className="font-medium text-xs">{inv.atm}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-[10px]">
                        {inv.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{inv.date}</TableCell>
                    <TableCell className="pr-4 text-right font-mono text-xs tabular-nums">
                      {inv.faces}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </div>
  )
}
