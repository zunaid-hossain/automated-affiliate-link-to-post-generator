import json
import os
from typing import Any

import google.generativeai as genai


GEMINI_MODEL = "gemini-1.5-flash"


def _configure_gemini() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    genai.configure(api_key=api_key)


def _fallback_caption(
    affiliate_url: str,
    product_title: str,
    price: str,
    offer: str,
    tone: str,
    language: str,
) -> dict[str, Any]:
    title = product_title or "এই দারুণ প্রোডাক্ট"
    price_line = f"মূল্য: {price}" if price else "মূল্য জানতে ইনবক্স করুন"
    offer_line = f"অফার: {offer}" if offer else ""
    caption = (
        f"{title} এখন আরও সহজে অর্ডার করুন।\n\n"
        f"{price_line}\n"
        f"{offer_line}\n\n"
        "প্রয়োজন, বাজেট আর পছন্দ মিলিয়ে দেখে নিতে পারেন। "
        "অর্ডার করতে নিচের লিংকে ক্লিক করুন।\n\n"
        f"{affiliate_url}"
    ).strip()
    return {
        "hook": "আপনার পছন্দের প্রোডাক্ট এখন হাতের নাগালে!",
        "caption": caption,
        "benefits": [
            "সহজে অর্ডার করা যায়",
            "দৈনন্দিন ব্যবহারের জন্য উপযোগী",
            "উপহার হিসেবেও ভালো পছন্দ",
        ],
        "CTA": "অর্ডার করতে লিংকে ক্লিক করুন",
        "hashtags": ["#AffiliateFinds", "#OnlineShopping", "#Bangladesh", "#ShopNow"],
        "facebook_keywords": [
            title,
            tone,
            language,
            "online shopping",
            "affiliate product",
        ],
    }


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def generate_caption(
    affiliate_url: str,
    product_title: str = "",
    price: str = "",
    offer: str = "",
    tone: str = "Friendly",
    language: str = "Bangla",
) -> dict[str, Any]:
    try:
        _configure_gemini()
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = f"""
Generate a high-converting Facebook affiliate product post.

Return only valid JSON with this exact shape:
{{
  "hook": "string",
  "caption": "string",
  "benefits": ["string", "string", "string"],
  "CTA": "string",
  "hashtags": ["#tag"],
  "facebook_keywords": ["keyword"]
}}

Product details:
- affiliate_url: {affiliate_url}
- product_title: {product_title or "Not provided"}
- price: {price or "Not provided"}
- offer: {offer or "Not provided"}
- tone: {tone}
- language: {language}

Rules:
- Do not make fake claims.
- Do not invent discount if not given.
- Do not say guaranteed result.
- Keep it simple and buyer-friendly.
- Add emotional hook.
- Add clear CTA.
- Add affiliate link naturally.
- Generate relevant hashtags.
- Generate Facebook reach keywords.
- Use the selected tone and language.
"""
        response = model.generate_content(prompt)
        data = _extract_json(response.text or "")
        for key in ["hook", "caption", "benefits", "CTA", "hashtags", "facebook_keywords"]:
            data.setdefault(key, [] if key in {"benefits", "hashtags", "facebook_keywords"} else "")
        return data
    except Exception:
        return _fallback_caption(affiliate_url, product_title, price, offer, tone, language)
