"""
Database connection and initialization module.
"""
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import settings


class Database:
    """Database connection manager."""
    
    _client: Optional[QdrantClient] = None
    
    @classmethod
    def get_client(cls) -> QdrantClient:
        """
        Get or create a Qdrant client instance.
        
        Returns:
            QdrantClient: The Qdrant client instance.
        """
        if cls._client is None:
            cls._client = QdrantClient(url=settings.qdrant_url)
        return cls._client
    
    @classmethod
    async def initialize(cls) -> None:
        """
        Initialize the database and create collections if they don't exist.
        """
        client = cls.get_client()
        
        # Check if the collection exists, if not create it
        if not client.collection_exists(settings.qdrant_collection_name):
            # Using 1536 dimensions for OpenAI embeddings
            client.create_collection(
                collection_name=settings.qdrant_collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )
            
            # Here we would add initial rap styles data
            # This will be implemented in a separate module


# Create a database instance
db = Database()
