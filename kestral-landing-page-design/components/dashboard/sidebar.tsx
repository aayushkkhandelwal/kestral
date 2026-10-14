import { Activity, Archive, Camera, FileText, FolderSearch, LayoutDashboard, Settings, Video } from 'lucide-react'
import Link from 'next/link'
import { KestrelMark } from '@/components/kestrel-logo'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, active: true },
  { label: 'Live Camera', icon: Camera },
  { label: 'Video Analysis', icon: Video },
  { label: 'Investigations', icon: FolderSearch },
  { label: 'Evidence Library', icon: Archive },
  { label: 'Model Evaluation', icon: Activity },
  { label: 'Reports', icon: FileText },
  { label: 'Settings', icon: Settings },
]

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r bg-sidebar px-3 py-5 text-sidebar-foreground md:flex">
      <Link href="/" className="flex items-center gap-3 px-2" aria-label="Kestrel home">
        <KestrelMark className="size-9" />
        <span className="leading-tight">
          <span className="block font-semibold">Kestrel</span>
          <span className="block text-xs text-muted-foreground">Forensics Suite</span>
        </span>
      </Link>

      <nav aria-label="Workspace" className="mt-8 flex flex-col gap-1">
        <p className="px-3 pb-2 text-xs font-medium text-muted-foreground">Workspace</p>
        {NAV_ITEMS.map((item) => (
          <a
            key={item.label}
            href="#"
            aria-current={item.active ? 'page' : undefined}
            className={cn(
              'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors',
              item.active
                ? 'bg-sidebar-accent font-semibold text-sidebar-accent-foreground'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground',
            )}
          >
            <item.icon
              className={cn('size-4.5', item.active && 'text-sidebar-primary')}
              strokeWidth={1.75}
              aria-hidden="true"
            />
            {item.label}
          </a>
        ))}
      </nav>
    </aside>
  )
}
