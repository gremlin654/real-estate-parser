from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class ListingBase(BaseModel):
    kufar_id: str
    url: str
    title: str
    price: int
    price_usd: Optional[int] = None
    currency: str = "BYN"
    city: Optional[str] = None
    address: Optional[str] = None
    rooms: Optional[int] = None
    area: Optional[float] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    category: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    raw_data: Optional[dict] = None


class ListingResponse(ListingBase):
    id: UUID
    status: str
    first_seen_at: datetime
    last_seen_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ListingHistoryResponse(BaseModel):
    id: UUID
    listing_id: UUID
    event_type: str
    price_before: Optional[int] = None
    price_after: Optional[int] = None
    changed_fields: Optional[dict] = None
    snapshot: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: List[ListingResponse]
    total: int
    page: int
    size: int
