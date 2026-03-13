from app.api.v1.listings import router as listings_router
from app.api.v1.history import router as history_router
from app.api.v1.stats import router as stats_router
from app.api.v1.scan import router as scan_router
from app.api.v1.export import router as export_router
from app.api.v1.ws import router as ws_router
from app.api.v1.cache import router as cache_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.deals import router as deals_router
from app.api.v1.price_drop import router as price_drop_router
from app.api.v1.favorites import router as favorites_router

__all__ = [
    "listings_router",
    "history_router",
    "stats_router",
    "scan_router",
    "export_router",
    "ws_router",
    "cache_router",
    "monitoring_router",
    "deals_router",
    "price_drop_router",
    "favorites_router",
]
