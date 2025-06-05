"""
API router configuration.
"""

from fastapi import APIRouter

from app.api.routes import health, battles, artists

# Create the main API router
api_router = APIRouter(prefix="/api")

# Include all route modules
api_router.include_router(health.router)
api_router.include_router(battles.router)
api_router.include_router(artists.router)
