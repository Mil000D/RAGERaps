"""
Data cache service for storing and retrieving rapper information and search results.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import asyncio

from pydantic import BaseModel, Field

from app.utils.common import utc_now


class RapperCacheData(BaseModel):
    """Cached data for a rapper."""

    rapper_name: str
    biographical_info: Optional[str] = None
    wikipedia_info: Optional[str] = None
    internet_search_info: Optional[str] = None
    style_info: Optional[Dict[str, str]] = None
    last_updated: datetime = Field(default_factory=utc_now)


class DataCacheService:
    """Service for caching rapper information and search results."""

    def __init__(self, cache_duration_hours: int = 24):
        """
        Initialize the data cache service.

        Args:
            cache_duration_hours: How long to keep cached data (default: 24 hours)
        """
        self.cache_duration_hours = cache_duration_hours
        self._rapper_cache: Dict[str, RapperCacheData] = {}
        self._lock = asyncio.Lock()

    async def get_rapper_data(self, rapper_name: str) -> Optional[RapperCacheData]:
        """
        Get cached data for a rapper.

        Args:
            rapper_name: Name of the rapper

        Returns:
            Optional[RapperCacheData]: Cached data if available and not expired
        """
        async with self._lock:
            cache_key = rapper_name.lower().strip()

            if cache_key not in self._rapper_cache:
                return None

            cached_data = self._rapper_cache[cache_key]

            # Check if data is expired
            expiry_time = cached_data.last_updated + timedelta(
                hours=self.cache_duration_hours
            )
            if utc_now() > expiry_time:
                # Remove expired data
                del self._rapper_cache[cache_key]
                return None

            return cached_data

    async def cache_rapper_data(
        self,
        rapper_name: str,
        biographical_info: Optional[str] = None,
        wikipedia_info: Optional[str] = None,
        internet_search_info: Optional[str] = None,
        style_info: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Cache data for a rapper.

        Args:
            rapper_name: Name of the rapper
            biographical_info: General biographical information
            wikipedia_info: Information from Wikipedia
            internet_search_info: Information from internet search
            style_info: Style-related information
        """
        async with self._lock:
            cache_key = rapper_name.lower().strip()

            # Get existing data or create new
            existing_data = self._rapper_cache.get(cache_key)

            if existing_data:
                # Update existing data
                if biographical_info is not None:
                    existing_data.biographical_info = biographical_info
                if wikipedia_info is not None:
                    existing_data.wikipedia_info = wikipedia_info
                if internet_search_info is not None:
                    existing_data.internet_search_info = internet_search_info
                if style_info is not None:
                    existing_data.style_info = style_info
                existing_data.last_updated = utc_now()
            else:
                # Create new cache entry
                self._rapper_cache[cache_key] = RapperCacheData(
                    rapper_name=rapper_name,
                    biographical_info=biographical_info,
                    wikipedia_info=wikipedia_info,
                    internet_search_info=internet_search_info,
                    style_info=style_info,
                )


# Create a singleton instance of the data cache service
data_cache_service = DataCacheService()
