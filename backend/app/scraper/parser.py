from typing import Optional
from loguru import logger


def parse_listing(raw_data: dict) -> Optional[dict]:
    kufar_id = str(raw_data.get("id") or raw_data.get("kufar_id") or "")
    if not kufar_id:
        return None

    price = int(raw_data.get("price", 0))
    price_usd = raw_data.get("price_usd") or raw_data.get("price$")
    if price_usd:
        price_usd = int(price_usd)

    url = raw_data.get("url") or f"https://kufar.by/l/{kufar_id}"
    address = raw_data.get("address") or raw_data.get("location") or "Беларусь"
    title = raw_data.get("title") or raw_data.get("subject") or "Без названия"

    params = raw_data.get("params", {}) or {}
    rooms = int(params.get("room_count") or params.get("rooms") or raw_data.get("rooms") or 0) or None
    area = float(params.get("area") or params.get("square") or raw_data.get("area") or 0) or None
    floor = int(params.get("floor") or raw_data.get("floor") or 0) or None

    images = raw_data.get("images", []) or []
    if isinstance(images, str):
        images = [images]

    return {
        "kufar_id": kufar_id,
        "url": url,
        "title": title,
        "price": price,
        "price_usd": price_usd,
        "currency": "BYN",
        "city": raw_data.get("city", ""),
        "address": address,
        "rooms": rooms,
        "area": area,
        "floor": floor,
        "category": raw_data.get("category", ""),
        "images": images,
        "raw_data": raw_data,
    }
