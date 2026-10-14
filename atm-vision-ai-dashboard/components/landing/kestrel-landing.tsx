'use client'

import { ArrowRight, ChevronDown } from 'lucide-react'
import Image from 'next/image'
import Link from 'next/link'
import { useEffect, useRef } from 'react'
import { Dashboard } from '@/components/dashboard/dashboard'
import { KestrelLogo } from '@/components/kestrel-logo'
import { ThemeToggle } from '@/components/theme-toggle'

// Position of the kestrel's pupil inside /images/kestrel.png (1408 x 768), as fractions of width/height.
const EYE_X = 0.5852
const EYE_Y = 0.3841
const MAX_ZOOM = 70

const clamp = (v: number, min = 0, max = 1) => Math.min(max, Math.max(min, v))
const range = (p: number, start: number, end: number) => clamp((p - start) / (end - start))
const smooth = (t: number) => t * t * (3 - 2 * t)

const WIND = [
  { top: '18%', width: 220, duration: 3.2, delay: 0 },
  { top: '34%', width: 140, duration: 2.4, delay: 1.1 },
  { top: '62%', width: 260, duration: 3.8, delay: 0.6 },
  { top: '76%', width: 120, duration: 2.1, delay: 1.8 },
  { top: '48%', width: 180, duration: 2.9, delay: 2.4 },
]

// The photo is cut into three layers. Wing polygons reach past the shoulder line so the body,
// drawn on top, hides the seam while the wings rotate around their roots.
const LAYERS = [
  {
    id: 'left-wing',
    clip: 'polygon(0% 0%, 52% 0%, 54% 42%, 41% 60%, 14% 64%, 0% 64%)',
    origin: '45% 44%',
    animation: 'animate-flap-left',
  },
  {
    id: 'right-wing',
    clip: 'polygon(63% 45%, 100% 37%, 100% 100%, 43% 100%, 43% 63%)',
    origin: '55% 57%',
    animation: 'animate-flap-right',
  },
  {
    id: 'body',
    clip: 'polygon(49.5% 0%, 100% 0%, 100% 40%, 60% 48%, 47% 66%, 47% 100%, 0% 100%, 0% 62%, 14% 62%, 33% 55%, 49% 36%)',
    origin: '50% 50%',
    animation: '',
  },
]

const SONAR_DELAYS = [0, 2, 4]

export function KestrelLanding() {
  const sectionRef = useRef<HTMLElement>(null)
  const headerRef = useRef<HTMLElement>(null)
  const zoomRef = useRef<HTMLDivElement>(null)
  const glideRef = useRef<HTMLDivElement>(null)
  const introRef = useRef<HTMLDivElement>(null)
  const hudRef = useRef<HTMLDivElement>(null)
  const windRef = useRef<HTMLDivElement>(null)
  const revealRef = useRef<HTMLDivElement>(null)
  const dashRef = useRef<HTMLDivElement>(null)
  const ctaRef = useRef<HTMLDivElement>(null)
  const progressRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let frame = 0

    const update = () => {
      frame = 0
      const section = sectionRef.current
      const zoom = zoomRef.current
      if (!section || !zoom) return

      const total = section.offsetHeight - window.innerHeight
      const p = clamp(-section.getBoundingClientRect().top / total)

      const move = smooth(range(p, 0.04, 0.42))
      const zoomT = range(p, 0.08, 0.8)
      const scale = Math.pow(MAX_ZOOM, zoomT * zoomT * (1.4 - 0.4 * zoomT))
      const dx = (0.5 - EYE_X) * zoom.offsetWidth * move
      const dy = (0.5 - EYE_Y) * zoom.offsetHeight * move
      zoom.style.transform = `translate3d(${dx}px, ${dy}px, 0) scale(${scale})`

      glideRef.current?.style.setProperty('--bob', String(1 - range(p, 0, 0.2)))
      glideRef.current?.style.setProperty('--flap', String(1 - range(p, 0, 0.14)))

      if (headerRef.current) {
        const headerOut = smooth(range(p, 0.2, 0.5))
        headerRef.current.style.opacity = String(1 - headerOut)
        headerRef.current.style.transform = `translateY(${headerOut * -24}px)`
        headerRef.current.style.pointerEvents = headerOut > 0.5 ? 'none' : 'auto'
      }

      if (introRef.current) {
        const out = range(p, 0.01, 0.12)
        introRef.current.style.opacity = String(1 - out)
        introRef.current.style.transform = `translateY(${out * -40}px)`
      }
      if (windRef.current) windRef.current.style.opacity = String(1 - range(p, 0.02, 0.2))

      if (hudRef.current) {
        const hud = range(p, 0.26, 0.4) * (1 - range(p, 0.6, 0.7))
        hudRef.current.style.opacity = String(hud)
        hudRef.current.style.transform = `translate(-50%, -50%) scale(${1.4 - 0.4 * smooth(range(p, 0.26, 0.42))})`
      }

      const reveal = smooth(range(p, 0.62, 0.88))
      if (revealRef.current) {
        revealRef.current.style.clipPath = `circle(${reveal * 75}% at 50% 50%)`
        revealRef.current.style.visibility = reveal > 0 ? 'visible' : 'hidden'
      }
      if (dashRef.current) dashRef.current.style.transform = `scale(${1.25 - 0.25 * reveal})`

      if (ctaRef.current) {
        const cta = range(p, 0.88, 0.96)
        ctaRef.current.style.opacity = String(cta)
        ctaRef.current.style.transform = `translate(-50%, ${(1 - cta) * 24}px)`
        ctaRef.current.style.pointerEvents = cta > 0.5 ? 'auto' : 'none'
      }
      if (progressRef.current) progressRef.current.style.transform = `scaleX(${p})`
    }

    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update)
    }

    update()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
    }
  }, [])

  return (
    <section ref={sectionRef} aria-label="Kestrel introduction" className="relative h-[480svh] bg-background">
      <div className="sticky top-0 h-svh p-2 sm:p-3">
        <div className="relative h-full overflow-hidden rounded-[2rem] bg-sky text-sky-foreground">
          <div ref={windRef} className="pointer-events-none absolute inset-0" aria-hidden="true">
            {SONAR_DELAYS.map((delay) => (
              <span
                key={delay}
                className="animate-sonar absolute top-1/2 left-1/2 aspect-square w-[140vmax] rounded-full border border-primary/40 opacity-0"
                style={{ animationDelay: `${delay}s` }}
              />
            ))}
            {WIND.map((w) => (
              <span
                key={w.top}
                className="animate-wind absolute left-0 h-px bg-gradient-to-r from-transparent via-current/25 to-transparent"
                style={{ top: w.top, width: w.width, animationDuration: `${w.duration}s`, animationDelay: `${w.delay}s` }}
              />
            ))}
          </div>

          <div className="absolute inset-0 flex items-center justify-center">
            <div
              ref={zoomRef}
              className="relative aspect-[1408/768] w-[min(88vw,125svh)] will-change-transform"
              style={{ transformOrigin: `${EYE_X * 100}% ${EYE_Y * 100}%` }}
            >
              <div ref={glideRef} className="animate-glide edge-fade absolute inset-0">
                {LAYERS.map((layer) => (
                  <div
                    key={layer.id}
                    className={`absolute inset-0 ${layer.animation}`}
                    style={{ clipPath: layer.clip, transformOrigin: layer.origin }}
                  >
                    <Image
                      src="/images/kestrel.png"
                      alt={layer.id === 'body' ? 'A kestrel in flight beating its wings, its sharp eye looking ahead' : ''}
                      aria-hidden={layer.id === 'body' ? undefined : true}
                      fill
                      priority
                      sizes="(min-width: 1024px) 92vw, 100vw"
                      className="object-contain select-none"
                      draggable={false}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div
            ref={hudRef}
            className="pointer-events-none absolute top-1/2 left-1/2 size-56 opacity-0 sm:size-72"
            aria-hidden="true"
          >
            <div className="absolute inset-0 rounded-full border border-primary/70" />
            <div className="absolute inset-6 animate-spin rounded-full border border-dashed border-primary [animation-duration:8s]" />
            {['top-0 left-0 border-t-2 border-l-2', 'top-0 right-0 border-t-2 border-r-2', 'bottom-0 left-0 border-b-2 border-l-2', 'bottom-0 right-0 border-b-2 border-r-2'].map(
              (pos) => (
                <span key={pos} className={`absolute size-6 border-primary ${pos}`} />
              ),
            )}
            <span className="absolute -top-8 left-1/2 -translate-x-1/2 rounded-full bg-primary px-3 py-1 font-mono text-[10px] font-semibold tracking-widest whitespace-nowrap text-primary-foreground">
              TARGET LOCKED
            </span>
            <span className="absolute -bottom-8 left-1/2 -translate-x-1/2 font-mono text-[10px] tracking-widest whitespace-nowrap">
              FOCUS 0.99 · BEST FRAME
            </span>
          </div>

          <header
            ref={headerRef}
            className="absolute inset-x-0 top-0 z-20 flex items-center justify-between p-5 transition-transform duration-75 sm:p-7"
          >
            <KestrelLogo />
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-full bg-sky-foreground px-4 py-2.5 text-sm font-semibold text-sky transition-opacity hover:opacity-90"
              >
                Launch Dashboard
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </div>
          </header>

          <div
            ref={introRef}
            className="pointer-events-none absolute inset-x-0 bottom-0 flex flex-col gap-6 p-5 sm:p-7 md:flex-row md:items-end md:justify-between"
          >
            <div>
              <p className="flex items-center gap-2 font-mono text-xs tracking-widest">
                <span className="size-1.5 rounded-full bg-primary" />
                ATM CCTV INTELLIGENCE
              </p>
              <h1 className="mt-3 text-6xl leading-none font-bold tracking-tighter sm:text-8xl lg:text-9xl">Kestrel</h1>
            </div>
            <div className="max-w-sm">
              <p className="text-sm leading-relaxed text-pretty opacity-75 sm:text-base">
                A kestrel spots a mouse from fifty metres up. We built the same eye for surveillance footage: recognise
                every person, then pull the single sharpest frame of their face.
              </p>
              <p className="mt-4 inline-flex items-center gap-1.5 font-mono text-xs tracking-widest">
                SCROLL TO LOOK THROUGH ITS EYE
                <ChevronDown className="size-3.5 animate-bounce" aria-hidden="true" />
              </p>
            </div>
          </div>

          <div
            ref={revealRef}
            className="absolute inset-0 z-10 overflow-hidden"
            style={{ clipPath: 'circle(0% at 50% 50%)', visibility: 'hidden' }}
            aria-hidden="true"
            inert
          >
            <div ref={dashRef} className="h-full origin-center overflow-hidden">
              <Dashboard className="h-full min-h-0" />
            </div>
          </div>

          <div
            ref={ctaRef}
            className="absolute bottom-6 left-1/2 z-30 opacity-0"
            style={{ pointerEvents: 'none', transform: 'translate(-50%, 24px)' }}
          >
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3.5 text-sm font-semibold text-primary-foreground shadow-2xl shadow-primary/30 transition-opacity hover:opacity-90"
            >
              Launch Dashboard
              <ArrowRight className="size-4" aria-hidden="true" />
            </Link>
          </div>

          <div className="absolute inset-x-0 bottom-0 z-30 h-0.5 bg-current/5" aria-hidden="true">
            <div ref={progressRef} className="h-full origin-left scale-x-0 bg-primary" />
          </div>
        </div>
      </div>
    </section>
  )
}
