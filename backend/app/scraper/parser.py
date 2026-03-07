from typing import Optional
from loguru import logger


def parse_listing(raw_data: dict) -> Optional[dict]:
    kufar_id = str(raw_data.get("id") or raw_data.get("kufar_id") or "")
    if not kufar_id:
        return None

    # Kufar возвращает цены в копейках/центах (умноженные на 100)
    # Поэтому делим на 100 для получения целой цены
    price_raw = int(raw_data.get("price", 0))
    price = price_raw // 100 if price_raw > 0 else 0

    price_usd_raw = raw_data.get("price_usd") or raw_data.get("price$")
    price_usd = None
    if price_usd_raw:
        price_usd_raw = int(price_usd_raw)
        price_usd = price_usd_raw // 100 if price_usd_raw > 0 else None

    url = raw_data.get("url") or f"https://kufar.by/l/{kufar_id}"
    address = raw_data.get("address") or raw_data.get("location") or "Беларусь"
    title = raw_data.get("title") or raw_data.get("subject") or "Без названия"

    params = raw_data.get("params", {}) or {}
    rooms = (
        int(
            params.get("room_count")
            or params.get("rooms")
            or raw_data.get("rooms")
            or 0
        )
        or None
    )
    area = (
        float(params.get("area") or params.get("square") or raw_data.get("area") or 0)
        or None
    )
    floor = int(params.get("floor") or raw_data.get("floor") or 0) or None

    # Новые поля
    total_floors = (
        int(
            params.get("floors")
            or params.get("total_floors")
            or raw_data.get("total_floors")
            or 0
        )
        or None
    )
    description = (
        raw_data.get("description")
        or raw_data.get("body")
        or raw_data.get("body_short")
        or ""
    )
    district = raw_data.get("district") or params.get("district") or ""
    metro = raw_data.get("metro") or params.get("metro") or ""
    house_year = (
        int(
            params.get("year")
            or params.get("house_year")
            or raw_data.get("house_year")
            or 0
        )
        or None
    )

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
        "total_floors": total_floors,
        "category": raw_data.get("category", ""),
        "description": description,
        "district": district,
        "metro": metro,
        "house_year": house_year,
        "images": images,
        "raw_data": raw_data,
    }
