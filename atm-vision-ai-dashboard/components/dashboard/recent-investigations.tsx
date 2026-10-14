import { ArrowUpRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { RECENT_INVESTIGATIONS, type InvestigationStatus, type Investigation } from '@/lib/dashboard-data'
import { cn } from '@/lib/utils'
import { SectionHeader } from './section-header'

const STATUS_STYLES: Record<string, string> = {
  Completed: 'bg-success',
  Processing: 'bg-primary',
  'Under Review': 'bg-warning',
  Flagged: 'bg-destructive',
}

export function RecentInvestigations({
  investigations,
  onSelectInvestigation,
}: {
  investigations?: Investigation[]
  onSelectInvestigation?: (inv: Investigation) => void
}) {
  const list = investigations && investigations.length > 0 ? investigations : RECENT_INVESTIGATIONS

  return (
    <section aria-labelledby="investigations-heading" className="flex flex-col gap-4">
      <div id="investigations-heading">
        <SectionHeader
          title="Recent Investigations"
          description="Latest cases opened across monitored ATMs"
          action={
            <Button variant="ghost" size="sm" className="text-muted-foreground">
              View all
              <ArrowUpRight data-icon="inline-end" />
            </Button>
          }
        />
      </div>

      <div className="overflow-hidden rounded-xl bg-card border">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="h-11 pl-5">ID</TableHead>
              <TableHead>ATM / File</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="hidden sm:table-cell">Date</TableHead>
              <TableHead className="text-right">Faces</TableHead>
              <TableHead className="pr-5 text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {list.map((inv) => (
              <TableRow key={inv.id} className="transition-colors">
                <TableCell className="py-3.5 pl-5 font-mono text-xs">{inv.id}</TableCell>
                <TableCell className="max-w-[200px] truncate">{inv.atm}</TableCell>
                <TableCell>
                  <span className="inline-flex items-center gap-2 text-sm">
                    <span
                      className={cn(
                        'size-1.5 rounded-full',
                        STATUS_STYLES[inv.status] || 'bg-success',
                        inv.status === 'Processing' && 'animate-pulse',
                      )}
                      aria-hidden="true"
                    />
                    {inv.status}
                  </span>
                </TableCell>
                <TableCell className="hidden text-muted-foreground sm:table-cell">{inv.date}</TableCell>
                <TableCell className="text-right tabular-nums">{inv.faces}</TableCell>
                <TableCell className="pr-5 text-right">
                  <Button
                    variant="outline"
                    size="sm"
                    aria-label={`Open investigation ${inv.id}`}
                    onClick={() => onSelectInvestigation?.(inv)}
                  >
                    Open
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </section>
  )
}
