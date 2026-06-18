"use client";

import { Copy, RefreshCw } from "lucide-react";

export type CaptionData = {
  hook: string;
  caption: string;
  benefits: string[];
  CTA: string;
  hashtags: string[];
  facebook_keywords: string[];
};

type Props = {
  data: CaptionData | null;
  loading: boolean;
  onRegenerate: () => void;
};

async function copyText(text: string) {
  await navigator.clipboard.writeText(text);
}

export default function CaptionResult({ data, loading, onRegenerate }: Props) {
  if (!data && !loading) {
    return (
      <section className="rounded-md border border-ink/10 bg-white p-5 shadow-soft">
        <h2 className="text-lg font-black text-ink">Caption Output</h2>
        <p className="mt-3 text-sm leading-6 text-ink/60">
          Generated captions, hashtags, and Facebook keywords will appear here.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-md border border-ink/10 bg-white p-5 shadow-soft">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-black text-ink">Caption Output</h2>
        <button
          type="button"
          onClick={onRegenerate}
          disabled={loading}
          title="Regenerate caption"
          className="inline-flex h-10 items-center gap-2 rounded-md border border-ink/15 px-3 text-sm font-bold text-ink transition hover:border-mint hover:text-mint disabled:opacity-50"
        >
          <RefreshCw size={16} /> Regenerate
        </button>
      </div>

      {loading ? (
        <div className="mt-5 space-y-3">
          <div className="h-4 w-4/5 animate-pulse rounded bg-ink/10" />
          <div className="h-4 w-full animate-pulse rounded bg-ink/10" />
          <div className="h-4 w-2/3 animate-pulse rounded bg-ink/10" />
        </div>
      ) : data ? (
        <div className="mt-5 space-y-5">
          <div>
            <div className="mb-2 text-xs font-black uppercase tracking-wide text-mint">Hook</div>
            <p className="rounded-md bg-paper p-4 text-sm leading-6 text-ink">{data.hook}</p>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between gap-3">
              <span className="text-xs font-black uppercase tracking-wide text-mint">Caption</span>
              <button
                type="button"
                onClick={() => copyText(data.caption)}
                title="Copy caption"
                className="inline-flex h-9 items-center gap-2 rounded-md bg-ink px-3 text-xs font-black text-white hover:bg-mint"
              >
                <Copy size={15} /> Copy
              </button>
            </div>
            <pre className="whitespace-pre-wrap rounded-md bg-paper p-4 text-sm leading-6 text-ink">
              {data.caption}
            </pre>
          </div>

          <div>
            <div className="mb-2 text-xs font-black uppercase tracking-wide text-mint">Benefits</div>
            <ul className="space-y-2 text-sm text-ink/75">
              {data.benefits.map((item) => (
                <li key={item} className="rounded-md border border-ink/10 px-3 py-2">
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <TagBlock label="Hashtags" items={data.hashtags} />
          <TagBlock label="Facebook Keywords" items={data.facebook_keywords} />
        </div>
      ) : null}
    </section>
  );
}

function TagBlock({ label, items }: { label: string; items: string[] }) {
  const text = items.join(" ");
  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <span className="text-xs font-black uppercase tracking-wide text-mint">{label}</span>
        <button
          type="button"
          onClick={() => copyText(text)}
          title={`Copy ${label.toLowerCase()}`}
          className="inline-flex h-9 items-center gap-2 rounded-md border border-ink/15 px-3 text-xs font-black text-ink hover:border-mint hover:text-mint"
        >
          <Copy size={15} /> Copy
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span key={item} className="rounded-full bg-paper px-3 py-2 text-xs font-bold text-ink/70">
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
