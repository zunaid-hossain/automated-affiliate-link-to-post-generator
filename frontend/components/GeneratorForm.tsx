"use client";

import Link from "next/link";
import { FormEvent, ReactNode, useMemo, useState } from "react";
import { ArrowLeft, ImagePlus, Search, Send } from "lucide-react";
import CaptionResult, { CaptionData } from "./CaptionResult";
import ImagePreview from "./ImagePreview";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const tones = ["Friendly", "Funny", "Premium", "Islamic/Halal style", "Urgency sales style"];
const languages = ["Bangla", "English", "Bangla + English"];

type ScrapedProduct = {
  source_url: string;
  product_title: string;
  description: string;
  price: string;
  category: string;
  image_url: string;
};

export default function GeneratorForm() {
  const [affiliateUrl, setAffiliateUrl] = useState("");
  const [productTitle, setProductTitle] = useState("");
  const [price, setPrice] = useState("");
  const [offer, setOffer] = useState("");
  const [category, setCategory] = useState("");
  const [tone, setTone] = useState(tones[0]);
  const [language, setLanguage] = useState(languages[0]);
  const [image, setImage] = useState<File | null>(null);
  const [scrapedProduct, setScrapedProduct] = useState<ScrapedProduct | null>(null);
  const [caption, setCaption] = useState<CaptionData | null>(null);
  const [posterUrl, setPosterUrl] = useState("");
  const [scrapeLoading, setScrapeLoading] = useState(false);
  const [captionLoading, setCaptionLoading] = useState(false);
  const [posterLoading, setPosterLoading] = useState(false);
  const [error, setError] = useState("");

  const localPreview = useMemo(() => (image ? URL.createObjectURL(image) : ""), [image]);
  const scrapedImage = scrapedProduct?.image_url || "";

  async function fetchProductDetails() {
    setError("");
    if (!affiliateUrl) {
      setError("Paste a product link first.");
      return;
    }

    setScrapeLoading(true);
    try {
      const response = await fetch(`${API_URL}/scrape-product`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ affiliate_url: affiliateUrl }),
      });
      if (!response.ok) {
        const data = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(data?.detail || "Could not fetch product details");
      }
      const data = (await response.json()) as ScrapedProduct;
      setScrapedProduct(data);
      if (data.product_title) setProductTitle(data.product_title);
      if (data.price) setPrice(data.price);
      if (data.category) setCategory(data.category);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setScrapeLoading(false);
    }
  }

  async function generateCaption(event?: FormEvent) {
    event?.preventDefault();
    setError("");
    setCaptionLoading(true);
    try {
      const response = await fetch(`${API_URL}/generate-caption`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          affiliate_url: affiliateUrl,
          product_title: productTitle,
          price,
          offer,
          category,
          tone,
          language,
        }),
      });

      if (!response.ok) throw new Error("Caption generation failed");
      const data = (await response.json()) as CaptionData;
      setCaption(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setCaptionLoading(false);
    }
  }

  async function generatePoster() {
    setError("");
    if (!image && !scrapedImage) {
      setError("Upload a product image or fetch one from the product link first.");
      return;
    }

    setPosterLoading(true);
    try {
      const formData = new FormData();
      if (image) {
        formData.append("product_image", image);
      } else if (scrapedImage) {
        formData.append("product_image_url", scrapedImage);
      }
      formData.append("product_title", productTitle);
      formData.append("price", price);
      formData.append("offer", offer);
      formData.append("cta_text", "Order Now");

      const response = await fetch(`${API_URL}/generate-poster`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Poster generation failed");
      const data = (await response.json()) as { image_url: string };
      setPosterUrl(`${API_URL}${data.image_url}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setPosterLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-paper px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <Link href="/" className="mb-2 inline-flex items-center gap-2 text-sm font-bold text-ink/60 hover:text-mint">
              <ArrowLeft size={16} /> Home
            </Link>
            <h1 className="text-3xl font-black text-ink">Affiliate Post Maker</h1>
          </div>
          <div className="rounded-md border border-ink/10 bg-white px-4 py-3 text-sm font-bold text-ink/65">
            No database. Temporary poster image only.
          </div>
        </header>

        {error ? (
          <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">
            {error}
          </div>
        ) : null}

        <div className="grid gap-5 xl:grid-cols-[420px_1fr_420px]">
          <form onSubmit={generateCaption} className="rounded-md border border-ink/10 bg-white p-5 shadow-soft">
            <h2 className="text-lg font-black text-ink">Product Details</h2>

            <div className="mt-5 space-y-4">
              <Field label="Affiliate link">
                <div className="flex gap-2">
                  <input
                    required
                    type="url"
                    value={affiliateUrl}
                    onChange={(event) => setAffiliateUrl(event.target.value)}
                    placeholder="https://example.com/product"
                    className="h-12 min-w-0 flex-1 rounded-md border border-ink/15 px-3 text-sm outline-none focus:border-mint"
                  />
                  <button
                    type="button"
                    onClick={fetchProductDetails}
                    disabled={scrapeLoading}
                    title="Fetch product details"
                    className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-mint px-3 text-sm font-black text-white transition hover:bg-ink disabled:opacity-60"
                  >
                    <Search size={17} />
                    <span className="hidden sm:inline">{scrapeLoading ? "Fetching" : "Fetch"}</span>
                  </button>
                </div>
              </Field>

              <Field label="Product image">
                <label className="flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-ink/20 bg-paper p-4 text-center text-sm font-bold text-ink/60 hover:border-mint">
                  <ImagePlus className="mb-2 text-mint" size={30} />
                  {image ? image.name : "Upload PNG, JPG, JPEG, or WEBP"}
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    className="hidden"
                    onChange={(event) => setImage(event.target.files?.[0] || null)}
                  />
                </label>
                {localPreview ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={localPreview} alt="Product preview" className="mt-3 max-h-56 w-full rounded-md object-contain" />
                ) : scrapedImage ? (
                  <div className="mt-3 rounded-md border border-ink/10 bg-white p-3">
                    <div className="mb-2 text-xs font-black uppercase tracking-wide text-mint">Best image from product page</div>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={scrapedImage} alt="Scraped product preview" className="max-h-56 w-full rounded-md object-contain" />
                  </div>
                ) : null}
              </Field>

              <Field label="Product title">
                <input
                  value={productTitle}
                  onChange={(event) => setProductTitle(event.target.value)}
                  placeholder="Wireless earbuds"
                  className="h-12 w-full rounded-md border border-ink/15 px-3 text-sm outline-none focus:border-mint"
                />
              </Field>

              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Price">
                  <input
                    value={price}
                    onChange={(event) => setPrice(event.target.value)}
                    placeholder="৳1,490"
                    className="h-12 w-full rounded-md border border-ink/15 px-3 text-sm outline-none focus:border-mint"
                  />
                </Field>
                <Field label="Offer">
                  <input
                    value={offer}
                    onChange={(event) => setOffer(event.target.value)}
                    placeholder="10% off"
                    className="h-12 w-full rounded-md border border-ink/15 px-3 text-sm outline-none focus:border-mint"
                  />
                </Field>
              </div>

              <Field label="Detected category">
                <input
                  value={category}
                  onChange={(event) => setCategory(event.target.value)}
                  placeholder="Auto detected from product page"
                  className="h-12 w-full rounded-md border border-ink/15 px-3 text-sm outline-none focus:border-mint"
                />
              </Field>

              {scrapedProduct?.description ? (
                <div className="rounded-md border border-ink/10 bg-paper p-3 text-sm leading-6 text-ink/70">
                  {scrapedProduct.description}
                </div>
              ) : null}

              <Field label="Tone">
                <select
                  value={tone}
                  onChange={(event) => setTone(event.target.value)}
                  className="h-12 w-full rounded-md border border-ink/15 px-3 text-sm outline-none focus:border-mint"
                >
                  {tones.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </Field>

              <Field label="Language">
                <select
                  value={language}
                  onChange={(event) => setLanguage(event.target.value)}
                  className="h-12 w-full rounded-md border border-ink/15 px-3 text-sm outline-none focus:border-mint"
                >
                  {languages.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </Field>

              <div className="grid gap-3 sm:grid-cols-2">
                <button
                  type="submit"
                  disabled={captionLoading || scrapeLoading}
                  className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-black text-white transition hover:bg-mint disabled:opacity-60"
                >
                  <Send size={17} /> Generate Post
                </button>
                <button
                  type="button"
                  onClick={generatePoster}
                  disabled={posterLoading || scrapeLoading}
                  className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-clay px-4 text-sm font-black text-white transition hover:bg-mint disabled:opacity-60"
                >
                  <ImagePlus size={17} /> Generate Poster
                </button>
              </div>
            </div>
          </form>

          <CaptionResult data={caption} loading={captionLoading} onRegenerate={() => generateCaption()} />
          <ImagePreview imageUrl={posterUrl} loading={posterLoading} />
        </div>
      </div>
    </main>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-black text-ink">{label}</span>
      {children}
    </label>
  );
}
