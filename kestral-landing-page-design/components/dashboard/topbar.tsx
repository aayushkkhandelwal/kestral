import { Bell, Search } from 'lucide-react'
import { ThemeToggle } from '@/components/theme-toggle'

export function Topbar() {
  return (
    <header className="flex items-center gap-3 border-b bg-background px-4 py-3 md:px-8">
      <label className="relative flex-1">
        <span className="sr-only">Search footage, persons or cases</span>
        <Search
          className="pointer-events-none absolute top-1/2 left-4 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
        <input
          type="search"
          placeholder="Search investigations, ATMs, tracks..."
          className="h-11 w-full max-w-xl rounded-xl bg-muted/60 pr-4 pl-11 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
        />
      </label>

      <span className="hidden items-center gap-2 rounded-full border bg-card px-3.5 py-2 font-mono text-xs font-medium tracking-wider sm:inline-flex">
        <span className="relative flex size-2">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-success opacity-60" />
          <span className="relative inline-flex size-2 rounded-full bg-success" />
        </span>
        ENGINE ONLINE
      </span>

      <button
        type="button"
        className="relative inline-flex size-9 items-center justify-center rounded-full border bg-card transition-colors hover:bg-muted"
      >
        <Bell className="size-4" aria-hidden="true" />
        <span className="absolute top-2 right-2.5 size-1.5 rounded-full bg-primary" />
        <span className="sr-only">Alerts</span>
      </button>

      <ThemeToggle />

      <span
        className="inline-flex size-9 items-center justify-center rounded-full bg-primary/15 text-xs font-bold text-primary"
        aria-label="Signed in as SR"
      >
        SR
      </span>
    </header>
  )
}
