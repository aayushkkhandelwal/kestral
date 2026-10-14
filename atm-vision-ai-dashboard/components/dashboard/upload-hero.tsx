'use client'

import { useRef, useState } from 'react'
import Image from 'next/image'
import { FolderOpen, ShieldCheck, UploadCloud, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

import { Loader2 } from 'lucide-react'

const ACCEPTED_EXTENSIONS = ['mp4', 'avi', 'mov', 'mkv', 'webm']
const ACCEPT_ATTR = '.mp4,.avi,.mov,.mkv,.webm,video/mp4,video/x-msvideo,video/quicktime,video/webm'

export function UploadHero({
  onFileSelected,
  uploading = false,
  uploadProgress = 0,
  uploadError = null,
}: {
  onFileSelected: (file: File) => void
  uploading?: boolean
  uploadProgress?: number
  uploadError?: string | null
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  function handleFiles(files: FileList | null) {
    const file = files?.[0]
    if (!file) return
    const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      setLocalError('Unsupported format. Please upload an MP4, AVI, MOV, MKV, or WEBM file.')
      return
    }
    setLocalError(null)
    onFileSelected(file)
  }

  const activeError = uploadError || localError

  return (
    <section
      aria-labelledby="upload-heading"
      className="relative overflow-hidden rounded-2xl bg-foreground text-background"
    >
      <div className="bg-grid-lines pointer-events-none absolute inset-0" aria-hidden="true" />
      <div
        className="pointer-events-none absolute -left-24 -top-32 size-96 rounded-full bg-primary/40 blur-3xl"
        aria-hidden="true"
      />

      <div className="relative grid gap-8 p-6 md:p-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)] lg:items-center">
        <div className="flex flex-col gap-6">
          <span className="inline-flex w-fit items-center gap-2 rounded-full border border-background/15 bg-background/5 px-3 py-1 text-xs text-background/80">
            <span className="size-1.5 rounded-full bg-primary" aria-hidden="true" />
            AI evidence extraction
          </span>
          <div>
            <h1
              id="upload-heading"
              className="text-3xl font-semibold tracking-tight text-balance md:text-4xl lg:text-[2.75rem] lg:leading-[1.1]"
            >
              Analyze ATM surveillance footage
            </h1>
            <p className="mt-3 max-w-md text-sm leading-relaxed text-background/65 text-pretty md:text-base">
              Upload a CCTV recording and Kestral detects people, tracks faces across frames, and surfaces the
              clearest evidence shot in seconds.
            </p>
          </div>

          <div
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault()
              setIsDragging(false)
              handleFiles(e.dataTransfer.files)
            }}
            className={cn(
              'flex flex-wrap items-center gap-4 rounded-xl border border-dashed p-4 transition-colors',
              isDragging ? 'border-primary bg-primary/15' : 'border-background/20 bg-background/5',
            )}
          >
            <div className="flex min-w-48 flex-1 items-center gap-3">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <UploadCloud className="size-5" aria-hidden="true" />
              </div>
              <div className="text-sm">
                <p className="font-medium">Drop a video here</p>
                <p className="text-xs text-background/55">MP4, AVI or MOV</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => inputRef.current?.click()} disabled={uploading}>
                {uploading ? (
                  <>
                    <Loader2 className="size-4 animate-spin" />
                    Uploading ({uploadProgress}%)
                  </>
                ) : (
                  <>
                    <UploadCloud data-icon="inline-start" />
                    Upload Video
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                className="border-background/20 bg-transparent text-background hover:bg-background/10 hover:text-background"
                onClick={() => inputRef.current?.click()}
                disabled={uploading}
              >
                <FolderOpen data-icon="inline-start" />
                Browse
              </Button>
            </div>
          </div>

          {activeError && (
            <p role="alert" className="text-sm text-red-300">
              {activeError}
            </p>
          )}

          <ul className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-background/60">
            <li className="flex items-center gap-1.5">
              <Zap className="size-3.5 text-primary" aria-hidden="true" />
              Avg. 42s per hour of footage
            </li>
            <li className="flex items-center gap-1.5">
              <ShieldCheck className="size-3.5 text-primary" aria-hidden="true" />
              Chain-of-custody logging
            </li>
          </ul>

          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT_ATTR}
            className="sr-only"
            tabIndex={-1}
            aria-label="Choose a video file"
            onChange={(e) => {
              handleFiles(e.target.files)
              e.target.value = ''
            }}
          />
        </div>

        <figure className="relative aspect-[4/3] overflow-hidden rounded-xl border border-background/10 shadow-2xl">
          <Image
            src="/images/atm-cctv.png"
            alt="CCTV frame of a person at an ATM with detection boxes"
            fill
            sizes="(min-width: 1024px) 600px, 100vw"
            className="object-cover"
            priority
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20" />
          <div className="absolute inset-x-0 top-0 h-1/4 animate-scan bg-gradient-to-b from-transparent via-primary/25 to-transparent" />

         {/* Detection Overlay */}
<div
  className="absolute rounded-sm border-2 border-primary"
  style={{
    left: "61%",
    top: "29%",
    width: "14%",
    height: "58%",
  }}
>
  <span className="absolute -top-6 left-2 rounded bg-primary px-1.5 py-0.5 font-mono text-[10px] font-semibold text-primary-foreground shadow-sm">
    PERSON 0.97
  </span>

  <div
    className="absolute rounded-sm border-2 border-emerald-400"
    style={{
      left: "60%",
      top: "6%",
      width: "50%",
      height: "14%",
    }}
  >
    <span className="absolute -bottom-5 left-1 rounded bg-emerald-500 px-1 py-0.5 font-mono text-[9px] font-semibold text-white shadow-sm">
      FACE 0.91
    </span>
  </div>
</div>

          <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-md bg-black/55 px-2 py-1 font-mono text-[10px] text-white backdrop-blur">
            <span className="size-1.5 animate-pulse rounded-full bg-red-500" aria-hidden="true" />
            REC · CAM-07
          </div>
          <figcaption className="absolute inset-x-3 bottom-3 flex items-center justify-between rounded-lg bg-black/55 px-3 py-2 text-[11px] text-white backdrop-blur">
            <span className="font-mono">ATM #A-0412 · 14:32:08</span>
            <span className="text-white/70">3 tracks</span>
          </figcaption>
        </figure>
      </div>
    </section>
  )
}
