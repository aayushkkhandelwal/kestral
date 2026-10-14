'use client'

import { useState, useMemo } from 'react'
import {
  FolderSearch,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Flag,
  ArrowRight,
  Download,
  Calendar,
  Video,
  ScanFace,
  ExternalLink,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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
import { cn } from '@/lib/utils'

export function InvestigationsView({
  investigations,
  onOpenCase,
}: {
  investigations: Investigation[]
  onOpenCase: (inv: Investigation) => void
}) {
  const [filter, setFilter] = useState<string>('All')
  const [search, setSearch] = useState('')
  const [flaggedIds, setFlaggedIds] = useState<Set<string>>(new Set(['INV-2045']))

  const allList = useMemo(() => {
    return investigations && investigations.length > 0 ? investigations : RECENT_INVESTIGATIONS
  }, [investigations])

  const filtered = useMemo(() => {
    return allList.filter((inv) => {
      const isFlagged = flaggedIds.has(inv.id)
      const currentStatus = isFlagged ? 'Flagged' : inv.status

      if (filter !== 'All') {
        if (filter === 'Flagged' && !isFlagged) return false
        if (filter !== 'Flagged' && currentStatus !== filter) return false
      }

      if (search.trim()) {
        const q = search.toLowerCase()
        return (
          inv.id.toLowerCase().includes(q) ||
          inv.atm.toLowerCase().includes(q) ||
          currentStatus.toLowerCase().includes(q)
        )
      }
      return true
    })
  }, [allList, filter, search, flaggedIds])

  const toggleFlag = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setFlaggedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const exportManifest = (inv: Investigation, e: React.MouseEvent) => {
    e.stopPropagation()
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(inv, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', dataStr)
    downloadAnchor.setAttribute('download', `case_manifest_${inv.id}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
  }

  const completedCount = allList.filter((i) => i.status === 'Completed').length
  const flaggedCount = flaggedIds.size

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground md:text-3xl">
            Surveillance Investigations
          </h1>
          <p className="text-sm text-muted-foreground">
            Manage biometric forensics cases, ATM terminal feeds, and suspect identification dossiers
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="px-3 py-1 font-mono text-xs">
            {allList.length} Total Cases
          </Badge>
          <Badge variant="outline" className="border-red-500/30 text-red-500">
            {flaggedCount} Flagged
          </Badge>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <p className="text-xs text-muted-foreground">Total Ingested Cases</p>
          <p className="mt-1 text-2xl font-bold tracking-tight">{allList.length}</p>
        </div>
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <p className="text-xs text-muted-foreground">Completed Audits</p>
          <p className="mt-1 text-2xl font-bold tracking-tight text-emerald-500">
            {completedCount}
          </p>
        </div>
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <p className="text-xs text-muted-foreground">Flagged Incidents</p>
          <p className="mt-1 text-2xl font-bold tracking-tight text-red-500">{flaggedCount}</p>
        </div>
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <p className="text-xs text-muted-foreground">Average Biometric Score</p>
          <p className="mt-1 text-2xl font-bold tracking-tight text-primary">88.4%</p>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col gap-3 rounded-xl border bg-card p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-1.5">
          {['All', 'Completed', 'Processing', 'Under Review', 'Flagged'].map((tab) => (
            <Button
              key={tab}
              variant={filter === tab ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setFilter(tab)}
              className="text-xs"
            >
              {tab}
            </Button>
          ))}
        </div>

        <div className="relative w-full max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search cases, ATMs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-9 pl-9 text-xs"
          />
        </div>
      </div>

      {/* Investigations Table */}
      <div className="overflow-hidden rounded-xl border bg-card shadow-sm">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-12 text-center">Flag</TableHead>
              <TableHead className="pl-4">Case ID</TableHead>
              <TableHead>ATM Terminal / Feed</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="hidden sm:table-cell">Date Logged</TableHead>
              <TableHead className="text-center">Subjects</TableHead>
              <TableHead className="pr-5 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="h-32 text-center text-sm text-muted-foreground">
                  No investigations match the current filter.
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((inv) => {
                const isFlagged = flaggedIds.has(inv.id)
                const status = isFlagged ? 'Flagged' : inv.status

                return (
                  <TableRow
                    key={inv.id}
                    className="cursor-pointer transition-colors hover:bg-muted/50"
                    onClick={() => onOpenCase(inv)}
                  >
                    <TableCell className="text-center" onClick={(e) => toggleFlag(inv.id, e)}>
                      <button
                        type="button"
                        aria-label={`Flag case ${inv.id}`}
                        className={cn(
                          'rounded-md p-1 transition-colors',
                          isFlagged ? 'text-red-500 hover:text-red-600' : 'text-muted-foreground/40 hover:text-foreground'
                        )}
                      >
                        <Flag className={cn('size-4', isFlagged && 'fill-current')} />
                      </button>
                    </TableCell>
                    <TableCell className="font-mono text-xs font-semibold pl-4">
                      {inv.id}
                    </TableCell>
                    <TableCell className="max-w-[240px] truncate font-medium">
                      {inv.atm}
                    </TableCell>
                    <TableCell>
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium">
                        <span
                          className={cn(
                            'size-2 rounded-full',
                            status === 'Completed' && 'bg-emerald-500',
                            status === 'Processing' && 'bg-blue-500 animate-pulse',
                            status === 'Under Review' && 'bg-amber-500',
                            status === 'Flagged' && 'bg-red-500'
                          )}
                          aria-hidden="true"
                        />
                        {status}
                      </span>
                    </TableCell>
                    <TableCell className="hidden text-xs text-muted-foreground sm:table-cell">
                      {inv.date}
                    </TableCell>
                    <TableCell className="text-center font-mono text-xs tabular-nums">
                      <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5">
                        <ScanFace className="size-3 text-muted-foreground" />
                        {inv.faces}
                      </span>
                    </TableCell>
                    <TableCell className="pr-5 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          title="Export Case Manifest"
                          onClick={(e) => exportManifest(inv, e)}
                        >
                          <Download className="size-3.5 text-muted-foreground" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-8 gap-1 text-xs"
                          onClick={(e) => {
                            e.stopPropagation()
                            onOpenCase(inv)
                          }}
                        >
                          Open Case
                          <ArrowRight className="size-3" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
