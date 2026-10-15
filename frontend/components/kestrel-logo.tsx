import { cn } from '@/lib/utils'

export function KestrelMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={cn('size-8', className)} aria-hidden="true">
      <rect width="32" height="32" rx="9" className="fill-primary" />
      <path
        className="fill-white"
        d="M6.5 32C6.6 25 7.2 19 8.8 14.5C10.4 9.6 13.6 6.4 17.6 6.4C20.6 6.4 22.6 7.9 23.9 10C26.1 10.4 27.3 12.6 26.9 15.2C26.7 16.6 26.1 17.6 25.2 18.3C25.3 16.8 24.6 15.6 23.2 15.4C22.4 15.4 21.6 15.8 21.2 16.4C21.6 19.6 22.3 23 23.3 26C24 28.2 24.7 30.2 25.3 32Z"
      />
      <path className="fill-primary" d="M15.4 11.9L21.8 10.1L20.5 12.9C18.8 13.4 17 13 15.4 11.9Z" />
    </svg>
  )
}

export function KestrelLogo({ className, withWordmark = true }: { className?: string; withWordmark?: boolean }) {
  return (
    <span className={cn('inline-flex items-center gap-2.5', className)}>
      <KestrelMark />
      {withWordmark && <span className="text-lg font-bold tracking-tight">Kestrel</span>}
    </span>
  )
}
