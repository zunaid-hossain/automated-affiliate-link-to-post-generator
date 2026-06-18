import os
import time
from pathlib import Path

from dotenv import load_dotenv
import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from gemini_service import generate_caption
from poster_generator import OUTPUT_DIR, generate_poster
from scraper_service import scrape_product


load_dotenv()

app = FastAPI(title="Affiliate Post Maker API")

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
allowed_origins = [frontend_origin, "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")


class CaptionRequest(BaseModel):
    affiliate_url: HttpUrl
    product_title: str = ""
    price: str = ""
    offer: str = ""
    category: str = ""
    tone: str = "Friendly"
    language: str = "Bangla"


class ScrapeRequest(BaseModel):
    affiliate_url: HttpUrl


@app.on_event("startup")
def cleanup_old_outputs() -> None:
    cutoff = time.time() - 24 * 60 * 60
    OUTPUT_DIR.mkdir(exist_ok=True)
    for path in OUTPUT_DIR.glob("*"):
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            if path.stat().st_mtime < cutoff:
                path.unlink(missing_ok=True)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate-caption")
def caption(payload: CaptionRequest) -> dict:
    return generate_caption(
        affiliate_url=str(payload.affiliate_url),
        product_title=payload.product_title,
        price=payload.price,
        offer=payload.offer,
        tone=payload.tone,
        language=payload.language,
        category=payload.category,
    )


@app.post("/scrape-product")
def scrape(payload: ScrapeRequest) -> dict[str, str]:
    try:
        return scrape_product(str(payload.affiliate_url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/generate-poster")
async def poster(
    product_image: UploadFile | None = File(None),
    product_image_url: str = Form(""),
    product_title: str = Form(""),
    price: str = Form(""),
    offer: str = Form(""),
    cta_text: str = Form("Order Now"),
) -> dict[str, str]:
    image_bytes = b""
    if product_image:
        if product_image.content_type not in {"image/png", "image/jpeg", "image/webp"}:
            raise HTTPException(status_code=400, detail="Upload PNG, JPG, JPEG, or WEBP image")
        image_bytes = await product_image.read()
    elif product_image_url:
        try:
            image_response = requests.get(product_image_url, timeout=15)
            image_response.raise_for_status()
            image_bytes = image_response.content
        except requests.RequestException as exc:
            raise HTTPException(status_code=400, detail="Could not download product image") from exc

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Upload an image or fetch one from the product link")

    try:
        filename = generate_poster(
            image_bytes=image_bytes,
            product_title=product_title,
            price=price,
            offer=offer,
            cta_text=cta_text,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not generate poster") from exc

    return {"image_url": f"/outputs/{filename}", "filename": filename}
