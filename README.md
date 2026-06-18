# Affiliate Post Maker

Lightweight full-stack app for generating Facebook affiliate captions, hashtags, keywords, and 1080x1080 product posters. Paste a product or affiliate link, fetch product details from the page, then generate captions and a clean poster from the best detected product image.

No database is used. No user history is stored. The backend only stores final generated poster images temporarily in `backend/outputs` and deletes images older than 24 hours.

## Features

- Scrapes product title, description, price, category, and best image from the pasted link.
- Uses Open Graph, Twitter cards, JSON-LD product data, and page images where available.
- Lets the user upload their own image or use the detected product image.
- Generates Bangla, English, or Bangla-English affiliate captions.
- Generates a 1080x1080 PNG poster without watermark, AI logo, or Gemini logo.
- Keeps the original product image unchanged inside the poster design.

## Project Structure

```text
affiliate-post-maker/
  backend/
    main.py
    requirements.txt
    poster_generator.py
    gemini_service.py
    scraper_service.py
    outputs/
  frontend/
    app/
      page.tsx
      dashboard/page.tsx
    components/
      GeneratorForm.tsx
      CaptionResult.tsx
      ImagePreview.tsx
    package.json
    tailwind.config.js
    .env.local.example
```

## Local Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key
FRONTEND_ORIGIN=http://localhost:3000
```

Run:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend endpoints:

- `POST /scrape-product`
- `POST /generate-caption`
- `POST /generate-poster`
- `GET /outputs/{filename}`

## Local Frontend Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Run:

```bash
npm run dev
```

Open `http://localhost:3000`.

## GitHub Push Instructions

```bash
git init
git add .
git commit -m "Initial Affiliate Post Maker app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/affiliate-post-maker.git
git push -u origin main
```

## Render Backend Deployment

1. Create a new Web Service on Render.
2. Connect your GitHub repo.
3. Set the root directory to `backend`.
4. Runtime: Python.
5. Build command:

```bash
pip install -r requirements.txt
```

6. Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

7. Add environment variables:

```env
GEMINI_API_KEY=your_gemini_api_key
FRONTEND_ORIGIN=https://your-vercel-frontend-url.vercel.app
```

## Vercel Frontend Deployment

1. Create a new project on Vercel.
2. Connect your GitHub repo.
3. Set the root directory to `frontend`.
4. Add environment variable:

```env
NEXT_PUBLIC_API_URL=https://your-render-backend-url.onrender.com
```

5. Deploy.

After Vercel gives you the frontend URL, add that exact URL to Render as `FRONTEND_ORIGIN`.

# automated-affiliate-link-to-post-generator
