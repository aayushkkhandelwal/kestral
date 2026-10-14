'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Play } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { API_BASE_URL } from '@/lib/config'
import { formatTimestamp, VIDEO_DURATION_SECONDS } from '@/lib/dashboard-data'
import { SectionHeader } from './section-header'

export type UploadedVideo = {
  name: string
  url: string
  uploadedAt: Date
}

type Metadata = { duration: string; resolution: string; fps: string; uploadTime: string }

const SAMPLE_METADATA: Metadata = {
  duration: formatTimestamp(VIDEO_DURATION_SECONDS),
  resolution: '1920 × 1080',
  fps: '25 fps',
  uploadTime: 'Oct 14, 09:42',
}

function formatUploadTime(date: Date) {
  return date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false })
}

export function VideoPreview({ video }: { video: UploadedVideo | null }) {
  const [loadedMeta, setLoadedMeta] = useState<{ url: string; duration: string; resolution: string } | null>(null)

  const metadata: Metadata = video
    ? {
        duration: loadedMeta?.url === video.url ? loadedMeta.duration : '—',
        resolution: loadedMeta?.url === video.url ? loadedMeta.resolution : '—',
        fps: '25 fps',
        uploadTime: formatUploadTime(video.uploadedAt),
      }
    : SAMPLE_METADATA

  const items = [
    { label: 'Duration', value: metadata.duration },
    { label: 'Resolution', value: metadata.resolution },
    { label: 'FPS', value: metadata.fps },
    { label: 'Upload Time', value: metadata.uploadTime },
  ]

  return (
    <section aria-labelledby="preview-heading" className="flex flex-col gap-4">
      <div id="preview-heading">
        <SectionHeader
          title="Video Preview"
          description={video ? video.name : 'CAM-02_ATM-114_2026-10-14.mp4'}
          action={
            <Badge variant="secondary" className="gap-1.5">
              <span className="size-1.5 rounded-full bg-success" aria-hidden="true" />
              Source verified
            </Badge>
          }
        />
      </div>

      <div className="overflow-hidden rounded-xl bg-card border">
        <div className="relative aspect-video w-full bg-black">
          {video ? (
            <video
              key={video.url}
              src={video.url.startsWith('http') || video.url.startsWith('blob:') ? video.url : `${API_BASE_URL}${video.url}`}
              controls
              className="size-full object-contain"
              onLoadedMetadata={(e) => {
                const el = e.currentTarget
                setLoadedMeta({
                  url: video.url,
                  duration: formatTimestamp(el.duration),
                  resolution: el.videoWidth ? `${el.videoWidth} × ${el.videoHeight}` : '—',
                })
              }}
            >
              <track kind="captions" />
            </video>
          ) : (
            <>
              <Image
                src="/images/atm-cctv.png"
                alt="CCTV footage of a person using an ATM at night"
                fill
                priority
                sizes="(min-width: 1280px) 60vw, 100vw"
                className="object-cover"
              />
              <div className="absolute top-3 left-3 flex items-center gap-2 rounded-md bg-black/60 px-2 py-1 font-mono text-[11px] text-white/90 backdrop-blur-sm">
                <span className="size-1.5 rounded-full bg-red-500" aria-hidden="true" />
                CAM-02 · 2026-10-14 02:13:44
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="flex size-14 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm">
                  <Play className="ml-0.5 size-6 fill-current" aria-hidden="true" />
                  <span className="sr-only">Sample footage preview</span>
                </span>
              </div>
            </>
          )}
        </div>

        <dl className="grid grid-cols-2 gap-px bg-border/60 md:grid-cols-4">
          {items.map((item) => (
            <div key={item.label} className="bg-card px-5 py-4">
              <dt className="text-xs text-muted-foreground">{item.label}</dt>
              <dd className="mt-1 text-sm font-medium tabular-nums">{item.value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  )
}
