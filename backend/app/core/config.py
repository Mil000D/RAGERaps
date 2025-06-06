"""
Configuration settings for the RAGERaps application.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    openai_api_key: str
    tavily_api_key: str
    langsmith_api_key: Optional[str] = None

    langsmith_project: str = "ragerapps"
    langsmith_tracing_v2: bool = True

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection_name: str = "rap_styles"
    qdrant_artists_collection_name: str = "artists_lyrics"

    debug: bool = False
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
