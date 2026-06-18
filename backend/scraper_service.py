import json
import re
from html import unescape
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", unescape(value)).strip()


def _meta(soup: BeautifulSoup, *names: str) -> str:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return _clean_text(tag["content"])
    return ""


def _json_ld_objects(soup: BeautifulSoup) -> list[dict]:
    objects: list[dict] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        text = script.string or script.get_text(strip=True)
        if not text:
            continue
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            graph = parsed.get("@graph")
            if isinstance(graph, list):
                objects.extend(item for item in graph if isinstance(item, dict))
            objects.append(parsed)
        elif isinstance(parsed, list):
            objects.extend(item for item in parsed if isinstance(item, dict))
    return objects


def _first_product_jsonld(objects: list[dict]) -> dict:
    for item in objects:
        item_type = item.get("@type")
        types = item_type if isinstance(item_type, list) else [item_type]
        if any(str(value).lower() == "product" for value in types):
            return item
    return {}


def _jsonld_image(product: dict) -> str:
    image = product.get("image")
    if isinstance(image, str):
        return image
    if isinstance(image, list) and image:
        first = image[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            return first.get("url", "")
    if isinstance(image, dict):
        return image.get("url", "")
    return ""


def _jsonld_price(product: dict) -> str:
    offers = product.get("offers")
    if isinstance(offers, list) and offers:
        offers = offers[0]
    if not isinstance(offers, dict):
        return ""
    price = offers.get("price") or offers.get("lowPrice")
    currency = offers.get("priceCurrency", "")
    if price and currency:
        return f"{currency} {price}"
    return str(price or "")


def _category_from_page(soup: BeautifulSoup, product: dict) -> str:
    category = product.get("category")
    if isinstance(category, str):
        return _clean_text(category)
    candidates = []
    for selector in [
        '[itemprop="category"]',
        '[class*="breadcrumb"] a',
        '[aria-label*="breadcrumb" i] a',
        "nav a",
    ]:
        candidates.extend(_clean_text(tag.get_text(" ")) for tag in soup.select(selector))
    candidates = [item for item in candidates if item and item.lower() not in {"home", "shop"}]
    return candidates[-1] if candidates else ""


def _score_image(src: str, alt: str = "") -> int:
    text = f"{src} {alt}".lower()
    score = 0
    for good in ["product", "main", "large", "zoom", "gallery", "primary", "media"]:
        if good in text:
            score += 3
    for bad in ["logo", "icon", "sprite", "avatar", "banner", "payment", "placeholder"]:
        if bad in text:
            score -= 5
    if re.search(r"(800|1000|1080|1200|1500)", text):
        score += 4
    return score


def _best_page_image(soup: BeautifulSoup, base_url: str) -> str:
    images: list[tuple[int, str]] = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        srcset = img.get("srcset")
        if srcset:
            last = srcset.split(",")[-1].strip().split(" ")[0]
            src = last or src
        if not src or src.startswith("data:"):
            continue
        src = urljoin(base_url, src)
        images.append((_score_image(src, img.get("alt", "")), src))
    if not images:
        return ""
    images.sort(reverse=True, key=lambda item: item[0])
    return images[0][1]


def scrape_product(url: str) -> dict[str, str]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ValueError("Could not fetch the product page. The site may block scraping.") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    objects = _json_ld_objects(soup)
    product = _first_product_jsonld(objects)

    title = (
        _clean_text(str(product.get("name", "")))
        or _meta(soup, "og:title", "twitter:title")
        or _clean_text(soup.title.string if soup.title else "")
    )
    description = (
        _clean_text(str(product.get("description", "")))
        or _meta(soup, "og:description", "twitter:description", "description")
    )
    image_url = (
        _jsonld_image(product)
        or _meta(soup, "og:image", "og:image:secure_url", "twitter:image")
        or _best_page_image(soup, response.url)
    )
    image_url = urljoin(response.url, image_url) if image_url else ""
    price = _jsonld_price(product)
    category = _category_from_page(soup, product)

    return {
        "source_url": response.url,
        "product_title": title,
        "description": description,
        "price": price,
        "category": category,
        "image_url": image_url,
    }
