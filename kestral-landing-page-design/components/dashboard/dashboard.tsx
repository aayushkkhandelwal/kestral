import { HeroCard } from '@/components/dashboard/hero-card'
import { MetricCards } from '@/components/dashboard/metric-cards'
import { Sidebar } from '@/components/dashboard/sidebar'
import { Topbar } from '@/components/dashboard/topbar'
import { cn } from '@/lib/utils'

export function Dashboard({ className }: { className?: string }) {
  return (
    <div className={cn('flex min-h-svh bg-background text-foreground', className)}>
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col dot-grid">
        <Topbar />
        <main className="flex flex-col gap-6 px-4 py-6 md:px-8">
          <HeroCard />
          <MetricCards />
        </main>
      </div>
    </div>
  )
}
