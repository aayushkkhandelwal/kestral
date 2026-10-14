'use client'

import { Bell, Menu, Moon, Search, Sun, Cpu } from 'lucide-react'
import { useTheme } from 'next-themes'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

export function TopNavbar({ onOpenMenu, backendOnline = false }: { onOpenMenu: () => void; backendOnline?: boolean }) {
  const { resolvedTheme, setTheme } = useTheme()

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border/60 bg-background/80 px-4 backdrop-blur-md md:px-8">
      <Button variant="ghost" size="icon" className="lg:hidden" onClick={onOpenMenu} aria-label="Open navigation">
        <Menu />
      </Button>

      <div className="relative w-full max-w-md">
        <Search
          className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
        <label htmlFor="global-search" className="sr-only">
          Search investigations, ATMs, tracks
        </label>
        <Input
          id="global-search"
          type="search"
          placeholder="Search investigations, ATMs, tracks..."
          className="h-9 rounded-lg border-transparent bg-muted/60 pl-9 shadow-none focus-visible:bg-background"
        />
      </div>

      <div className="ml-auto flex items-center gap-2">
        <div className="hidden sm:flex items-center gap-2 rounded-full border border-border/80 bg-muted/40 px-3 py-1 text-xs">
          <span
            className={cn(
              'size-2 rounded-full transition-colors',
              backendOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
            )}
            aria-hidden="true"
          />
          <span className="font-mono text-[11px] font-medium text-foreground/80">
            {backendOnline ? 'ENGINE ONLINE' : 'ENGINE OFFLINE'}
          </span>
        </div>

        <Button variant="ghost" size="icon" className="relative" aria-label="Notifications, 3 unread">
          <Bell />
          <span className="absolute top-1.5 right-1.5 size-2 rounded-full bg-primary ring-2 ring-background" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Toggle theme"
          onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
        >
          <Sun className="hidden dark:block" />
          <Moon className="dark:hidden" />
        </Button>
        <Avatar className="ml-1.5 size-8">
          <AvatarFallback className="bg-primary/15 text-xs font-medium text-primary">SR</AvatarFallback>
        </Avatar>
      </div>
    </header>
  )
}
