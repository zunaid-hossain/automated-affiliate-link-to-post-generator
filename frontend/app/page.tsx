import Link from "next/link";
import { ArrowRight, BadgePercent, ImageIcon, MessageSquareText } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-paper">
      <section className="mx-auto flex min-h-screen max-w-6xl flex-col justify-between px-5 py-5 sm:px-8">
        <nav className="flex items-center justify-between">
          <div className="text-xl font-black text-ink">Affiliate Post Maker</div>
          <Link
            href="/dashboard"
            className="inline-flex h-11 items-center gap-2 rounded-md bg-ink px-4 text-sm font-bold text-white transition hover:bg-mint"
          >
            Dashboard <ArrowRight size={17} />
          </Link>
        </nav>

        <div className="grid gap-10 py-12 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div>
            <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-ink/15 px-4 py-2 text-sm font-bold text-mint">
              <BadgePercent size={16} /> Facebook affiliate content toolkit
            </p>
            <h1 className="max-w-3xl text-5xl font-black leading-tight text-ink sm:text-6xl">
              Affiliate Post Maker
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-ink/70">
              Paste a product link, upload the product image, and create ready-to-post captions,
              hashtags, keywords, and a clean square product poster.
            </p>
            <Link
              href="/dashboard"
              className="mt-8 inline-flex h-12 items-center gap-3 rounded-md bg-clay px-6 text-base font-black text-white shadow-soft transition hover:bg-mint"
            >
              Start making posts <ArrowRight size={20} />
            </Link>
          </div>

          <div className="relative overflow-hidden rounded-md border border-ink/10 bg-white p-5 shadow-soft">
            <div className="aspect-square rounded-md bg-[radial-gradient(circle_at_30%_20%,#e8f2e9,transparent_36%),radial-gradient(circle_at_80%_10%,#f6e2cd,transparent_32%),#ffffff] p-8">
              <div className="flex h-full flex-col justify-between rounded-md border border-ink/10 bg-white/70 p-6">
                <div className="flex justify-between">
                  <MessageSquareText className="text-mint" size={42} />
                  <ImageIcon className="text-clay" size={42} />
                </div>
                <div>
                  <div className="mb-3 h-4 w-3/4 rounded bg-ink/20" />
                  <div className="mb-3 h-4 w-5/6 rounded bg-ink/12" />
                  <div className="h-4 w-1/2 rounded bg-ink/12" />
                </div>
                <div className="rounded-md bg-ink px-5 py-4 text-center font-black text-white">
                  Order Now
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-3 pb-4 text-sm text-ink/65 sm:grid-cols-3">
          <div>No database</div>
          <div>No saved history</div>
          <div>Temporary poster output only</div>
        </div>
      </section>
    </main>
  );
}
