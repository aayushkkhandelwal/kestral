'use client'

import { useState } from 'react'
import {
  Camera,
  ChevronsUpDown,
  FileText,
  FolderSearch,
  LayoutDashboard,
  Settings,
  Video,
  Archive,
  Activity,
  X,
} from 'lucide-react'
import { KestralLogo } from '@/components/kestral-logo'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard },
  { label: 'Live Camera', icon: Camera },
  { label: 'Video Analysis', icon: Video },
  { label: 'Investigations', icon: FolderSearch },
  { label: 'Evidence Library', icon: Archive },
  { label: 'Model Evaluation', icon: Activity },
  { label: 'Reports', icon: FileText },
  { label: 'Settings', icon: Settings },
] as const

type AppSidebarProps = {
  mobileOpen: boolean
  onClose: () => void
  activeView: string
  onSelectView: (view: string) => void
}

export function AppSidebar({ mobileOpen, onClose, activeView, onSelectView }: AppSidebarProps) {
  return (
    <>
      <div
        aria-hidden="true"
        onClick={onClose}
        className={cn(
          'fixed inset-0 z-40 bg-background/70 backdrop-blur-sm transition-opacity lg:hidden',
          mobileOpen ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
      />
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-[250px] flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-transform duration-200 lg:sticky lg:top-0 lg:h-svh lg:translate-x-0',
          mobileOpen ? 'translate-x-0' : '-translate-x-full',
        )}
        aria-label="Primary"
      >
        <div className="flex h-16 items-center justify-between px-5">
          <div className="flex items-center gap-2.5">
            <KestralLogo />
            <div className="leading-tight">
              <p className="text-sm font-semibold tracking-tight">Kestral</p>
              <p className="text-xs text-muted-foreground">Forensics Suite</p>
            </div>
          </div>
          <Button variant="ghost" size="icon-sm" className="lg:hidden" onClick={onClose} aria-label="Close navigation">
            <X />
          </Button>
        </div>

        <nav className="flex-1 px-3 py-4">
          <p className="px-3 pb-2 text-xs font-medium text-muted-foreground">Workspace</p>
          <ul className="flex flex-col gap-0.5">
            {NAV_ITEMS.map(({ label, icon: Icon }) => {
              const isActive = activeView === label
              return (
                <li key={label}>
                  <button
                    type="button"
                    onClick={() => {
                      onSelectView(label)
                      onClose()
                    }}
                    aria-current={isActive ? 'page' : undefined}
                    className={cn(
                      'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring',
                      isActive
                        ? 'bg-sidebar-accent font-medium text-sidebar-accent-foreground'
                        : 'text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-foreground',
                    )}
                  >
                    <Icon className={cn('size-4', isActive && 'text-primary')} aria-hidden="true" />
                    {label}
                  </button>
                </li>
              )
            })}
          </ul>
        </nav>

        <div className="p-3">
          <button
            type="button"
            className="flex w-full items-center gap-3 rounded-xl p-2.5 text-left transition-colors hover:bg-sidebar-accent/60"
          >
            <Avatar className="size-9">
              <AvatarFallback className="bg-primary/15 text-xs font-medium text-primary">SR</AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">Sarah Reyes</p>
              <p className="truncate text-xs text-muted-foreground">Lead Investigator</p>
            </div>
            <ChevronsUpDown className="size-4 text-muted-foreground" aria-hidden="true" />
          </button>
        </div>
      </aside>
    </>
  )
}
