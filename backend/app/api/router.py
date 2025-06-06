"""
API router configuration.
"""

from fastapi import APIRouter

from app.api.routes import health, battles

api_router = APIRouter(prefix="/api")

api_router.include_router(health.router)
api_router.include_router(battles.router)
