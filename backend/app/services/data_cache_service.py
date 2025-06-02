"""
Data cache service for storing and retrieving rapper information and search results.
"""
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, field


@dataclass
class CachedData:
    """Container for cached data with timestamp."""
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if the cached data has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


@dataclass
class RapperCacheData:
    """Cached data for a rapper."""
    rapper_name: str
    biographical_info: Optional[str] = None
    wikipedia_info: Optional[str] = None
    internet_search_info: Optional[str] = None
    style_info: Optional[Dict[str, str]] = None
    last_updated: datetime = field(default_factory=datetime.now)


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
        self._search_cache: Dict[str, CachedData] = {}
        self._style_cache: Dict[str, CachedData] = {}
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
            expiry_time = cached_data.last_updated + timedelta(hours=self.cache_duration_hours)
            if datetime.now() > expiry_time:
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
        style_info: Optional[Dict[str, str]] = None
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
                existing_data.last_updated = datetime.now()
            else:
                # Create new cache entry
                self._rapper_cache[cache_key] = RapperCacheData(
                    rapper_name=rapper_name,
                    biographical_info=biographical_info,
                    wikipedia_info=wikipedia_info,
                    internet_search_info=internet_search_info,
                    style_info=style_info
                )

    async def get_search_result(self, query: str) -> Optional[str]:
        """
        Get cached search result.
        
        Args:
            query: Search query
            
        Returns:
            Optional[str]: Cached search result if available and not expired
        """
        async with self._lock:
            cache_key = query.lower().strip()
            
            if cache_key not in self._search_cache:
                return None
                
            cached_data = self._search_cache[cache_key]
            
            if cached_data.is_expired():
                del self._search_cache[cache_key]
                return None
                
            return cached_data.data

    async def cache_search_result(self, query: str, result: str) -> None:
        """
        Cache a search result.
        
        Args:
            query: Search query
            result: Search result
        """
        async with self._lock:
            cache_key = query.lower().strip()
            expires_at = datetime.now() + timedelta(hours=self.cache_duration_hours)
            
            self._search_cache[cache_key] = CachedData(
                data=result,
                expires_at=expires_at
            )

    async def get_style_info(self, style: str) -> Optional[str]:
        """
        Get cached style information.
        
        Args:
            style: Rap style name
            
        Returns:
            Optional[str]: Cached style information if available and not expired
        """
        async with self._lock:
            cache_key = style.lower().strip()
            
            if cache_key not in self._style_cache:
                return None
                
            cached_data = self._style_cache[cache_key]
            
            if cached_data.is_expired():
                del self._style_cache[cache_key]
                return None
                
            return cached_data.data

    async def cache_style_info(self, style: str, info: str) -> None:
        """
        Cache style information.
        
        Args:
            style: Rap style name
            info: Style information
        """
        async with self._lock:
            cache_key = style.lower().strip()
            expires_at = datetime.now() + timedelta(hours=self.cache_duration_hours)
            
            self._style_cache[cache_key] = CachedData(
                data=info,
                expires_at=expires_at
            )

    async def clear_cache(self) -> None:
        """Clear all cached data."""
        async with self._lock:
            self._rapper_cache.clear()
            self._search_cache.clear()
            self._style_cache.clear()

    async def clear_expired_cache(self) -> None:
        """Remove expired entries from cache."""
        async with self._lock:
            # Clear expired rapper data
            expired_rappers = []
            for key, data in self._rapper_cache.items():
                expiry_time = data.last_updated + timedelta(hours=self.cache_duration_hours)
                if datetime.now() > expiry_time:
                    expired_rappers.append(key)
            
            for key in expired_rappers:
                del self._rapper_cache[key]
            
            # Clear expired search results
            expired_searches = []
            for key, data in self._search_cache.items():
                if data.is_expired():
                    expired_searches.append(key)
            
            for key in expired_searches:
                del self._search_cache[key]
            
            # Clear expired style info
            expired_styles = []
            for key, data in self._style_cache.items():
                if data.is_expired():
                    expired_styles.append(key)
            
            for key in expired_styles:
                del self._style_cache[key]

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dict[str, int]: Cache statistics
        """
        return {
            "rapper_cache_size": len(self._rapper_cache),
            "search_cache_size": len(self._search_cache),
            "style_cache_size": len(self._style_cache)
        }


# Create a singleton instance of the data cache service
data_cache_service = DataCacheService()
