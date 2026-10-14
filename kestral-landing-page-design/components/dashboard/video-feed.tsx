import Image from 'next/image'

export function VideoFeed() {
  return (
    <figure
      aria-label="CCTV detection preview"
      className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-black shadow-2xl ring-1 ring-black/10"
    >
      <Image
        src="/images/atm-cctv.png"
        alt="CCTV still of a person in a hoodie using an ATM"
        fill
        sizes="(min-width: 1280px) 40vw, 100vw"
        className="object-cover"
      />

      <div className="absolute border-[1.5px] border-primary" style={{ left: '32%', top: '22%', width: '25%', height: '64%' }}>
        <span className="absolute top-0 left-[-1.5px] -translate-y-full bg-primary px-1.5 py-0.5 font-mono text-[10px] leading-tight font-semibold text-primary-foreground">
          PERSON
          <br />
          0.97
        </span>
      </div>
      <div className="absolute border-[1.5px] border-success" style={{ left: '35%', top: '33%', width: '7.5%', height: '18%' }}>
        <span className="absolute bottom-[-1.5px] left-full ml-0.5 bg-success px-1.5 py-0.5 font-mono text-[10px] leading-tight font-semibold text-black">
          FACE
          <br />
          0.91
        </span>
      </div>

      <div className="absolute top-3 left-3 flex items-center gap-1.5 rounded-md bg-black/60 px-2 py-1 font-mono text-[10px] text-white">
        <span className="size-1.5 rounded-full bg-red-500" />
        {'REC · CAM-07'}
      </div>
      <figcaption className="absolute inset-x-3 bottom-3 flex items-center justify-between rounded-lg bg-black/65 px-3 py-2 font-mono text-[11px] text-white">
        <span>{'ATM #A-0412 · 14:32:08'}</span>
        <span className="font-sans">3 tracks</span>
      </figcaption>
    </figure>
  )
}
