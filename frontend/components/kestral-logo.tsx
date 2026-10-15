import { cn } from '@/lib/utils'

export function KestralLogo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" role="img" aria-label="Kestral" className={cn('size-8 shrink-0', className)}>
      <rect width="32" height="32" rx="8" className="fill-primary" />
      <path
        className="fill-primary-foreground"
        d="M9 32C8 22 9.5 12 15.5 8.5C19 6.6 22.6 7.2 24.4 9.6L26.6 11.4C27.2 12 27.1 13.2 26.3 14C25.8 13.4 25.1 13.2 24.4 13.4C23 16 22.3 19.4 22.8 23C23.2 26.2 23.8 29.4 24.4 32Z"
      />
      <circle cx="21" cy="11" r="1.6" className="fill-primary" />
      <path className="fill-primary" d="M20 12.4C19.4 15 19.3 17.6 19.9 20C20.8 17.6 21.3 15 21.2 12.6Z" />
      <path className="fill-primary" d="M15.6 12C14.8 14.4 14.8 16.8 15.3 19C16 16.8 16.4 14.4 16.3 12.2Z" />
    </svg>
  )
}
