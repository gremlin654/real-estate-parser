"""
Утилиты для JSON сериализации.

Конвертация Decimal и других специальных типов для сохранения в JSONB.
"""

import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Any
import json
from sqlalchemy.orm import class_mapper


def serialize_value(value: Any) -> Any:
    """
    Конвертирует отдельное значение в JSON-сериализуемый формат.
    
    Args:
        value: Значение для конвертации
        
    Returns:
        JSON-сериализуемое значение
    """
    if isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, uuid.UUID):
        return str(value)
    elif isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [serialize_value(item) for item in value]
    else:
        return value


def listing_to_dict(listing: Any) -> dict:
    """
    Конвертирует SQLAlchemy модель Listing в dict с корректной сериализацией Decimal.
    
    Args:
        listing: Экземпляр модели Listing
        
    Returns:
        Словарь с данными объявления, готовый к JSON сериализации
    """
    result = {}
    
    # Получаем все колонки модели
    for column in class_mapper(listing.__class__).columns:
        key = column.key
        value = getattr(listing, key, None)
        result[key] = serialize_value(value)
    
    return result


def serialize_for_snapshot(data: dict) -> dict:
    """
    Рекурсивно конвертирует все Decimal значения в словаре в float.
    
    Args:
        data: Словарь для конвертации
        
    Returns:
        Словарь с конвертированными значениями
    """
    return serialize_value(data)


class DecimalEncoder(json.JSONEncoder):
    """
    Кастомный JSON encoder для обработки Decimal и других специальных типов.
    
    Использование:
        json.dumps(data, cls=DecimalEncoder)
    """
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)
