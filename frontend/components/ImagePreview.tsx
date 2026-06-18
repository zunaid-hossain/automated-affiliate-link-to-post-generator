"use client";

import { Download, ImageIcon } from "lucide-react";

type Props = {
  imageUrl: string;
  loading: boolean;
};

export default function ImagePreview({ imageUrl, loading }: Props) {
  return (
    <section className="rounded-md border border-ink/10 bg-white p-5 shadow-soft">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-black text-ink">Poster Preview</h2>
        {imageUrl ? (
          <a
            href={imageUrl}
            download
            title="Download image"
            className="inline-flex h-10 items-center gap-2 rounded-md bg-clay px-3 text-sm font-black text-white hover:bg-mint"
          >
            <Download size={16} /> Download
          </a>
        ) : null}
      </div>

      <div className="mt-5 flex aspect-square items-center justify-center rounded-md border border-dashed border-ink/20 bg-paper">
        {loading ? (
          <div className="text-sm font-bold text-ink/60">Generating poster...</div>
        ) : imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={imageUrl} alt="Generated product poster" className="h-full w-full rounded-md object-contain" />
        ) : (
          <div className="flex flex-col items-center gap-3 text-ink/45">
            <ImageIcon size={42} />
            <span className="text-sm font-bold">Generated image appears here</span>
          </div>
        )}
      </div>
    </section>
  );
}
