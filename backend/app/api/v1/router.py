from fastapi import APIRouter

from app.api.v1 import alumni, auth, dashboard, health, scraper, sources, tracking, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(alumni.router)
api_router.include_router(scraper.router)
api_router.include_router(sources.router)
api_router.include_router(tracking.router)
api_router.include_router(dashboard.router)
