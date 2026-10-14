'use client'

import { FileVideo, FolderOpen, ShieldCheck, UploadCloud, Zap } from 'lucide-react'
import { useId, useState } from 'react'
import { VideoFeed } from '@/components/dashboard/video-feed'

export function HeroCard() {
  const inputId = useId()
  const [fileName, setFileName] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)

  return (
    <section className="relative grid gap-8 overflow-hidden rounded-3xl bg-hero p-6 text-hero-foreground md:p-9 xl:grid-cols-[1.15fr_1fr] xl:items-center">
      <div
        className="pointer-events-none absolute -top-1/3 -left-1/4 size-[70%] rounded-full bg-hero-glow blur-3xl"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute inset-0 line-grid opacity-[0.05] dark:hidden"
        aria-hidden="true"
      />

      <div className="relative">
        <p className="inline-flex items-center gap-2 rounded-full border border-current/15 px-3 py-1 text-xs font-medium">
          <span className="size-1.5 rounded-full bg-primary" />
          AI evidence extraction
        </p>
        <h1 className="mt-5 text-3xl leading-tight font-bold tracking-tight text-balance md:text-5xl">
          Analyze ATM surveillance footage
        </h1>
        <p className="mt-4 max-w-xl text-sm leading-relaxed text-pretty opacity-70 md:text-base">
          Upload a CCTV recording and Kestrel detects people, tracks faces across frames, and surfaces the clearest
          evidence shot in seconds.
        </p>

        <div
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragging(false)
            const file = e.dataTransfer.files[0]
            if (file) setFileName(file.name)
          }}
          data-dragging={dragging}
          className="mt-7 flex flex-wrap items-center gap-3 rounded-2xl border border-dashed border-current/20 bg-current/[0.03] p-3 transition-colors data-[dragging=true]:border-primary data-[dragging=true]:bg-primary/10"
        >
          <span className="inline-flex size-11 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            {fileName ? (
              <FileVideo className="size-5" aria-hidden="true" />
            ) : (
              <UploadCloud className="size-5" aria-hidden="true" />
            )}
          </span>
          <span className="min-w-0 flex-1 text-sm">
            <span className="block truncate font-medium">{fileName ?? 'Drop a video here'}</span>
            <span className="block text-xs opacity-60">MP4, AVI or MOV</span>
          </span>
          <label
            htmlFor={inputId}
            className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
          >
            <UploadCloud className="size-4" aria-hidden="true" />
            Upload Video
          </label>
          <label
            htmlFor={inputId}
            className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-current/15 px-3.5 py-2 text-sm font-semibold transition-colors hover:bg-current/5"
          >
            <FolderOpen className="size-4" aria-hidden="true" />
            Browse
          </label>
          <input
            id={inputId}
            type="file"
            accept="video/*"
            className="sr-only"
            onChange={(e) => setFileName(e.target.files?.[0]?.name ?? null)}
          />
        </div>

        <ul className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-xs opacity-70">
          <li className="flex items-center gap-1.5">
            <Zap className="size-3.5 text-primary" aria-hidden="true" />
            Avg. 42s per hour of footage
          </li>
          <li className="flex items-center gap-1.5">
            <ShieldCheck className="size-3.5 text-primary" aria-hidden="true" />
            Chain-of-custody logging
          </li>
        </ul>
      </div>

      <VideoFeed />
    </section>
  )
}
