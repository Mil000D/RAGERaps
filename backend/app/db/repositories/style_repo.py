"""
Repository for rap styles stored in Qdrant.
"""

from typing import Dict, List, Optional

from langchain_openai import OpenAIEmbeddings
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, PointStruct

from app.core.config import settings
from app.db.database import Database


class StyleRepository:
    """Repository for managing rap styles in Qdrant."""

    def __init__(self):
        """Initialize the repository."""
        self.client = Database.get_client()
        self.collection_name = settings.qdrant_collection_name
        self.embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)

    async def add_style(
        self,
        style_name: str,
        description: str,
        examples: List[str],
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Add a new rap style to the database.

        Args:
            style_name: Name of the rap style
            description: Description of the style
            examples: List of example verses in this style
            metadata: Additional metadata about the style

        Returns:
            str: ID of the added style
        """
        # Combine style information for embedding
        text_to_embed = f"{style_name}: {description}\n\nExamples:\n" + "\n".join(
            examples
        )

        # Generate embedding
        embedding = await self.embeddings.aembed_query(text_to_embed)

        # Prepare payload
        payload = {
            "style_name": style_name,
            "description": description,
            "examples": examples,
        }

        if metadata:
            payload.update(metadata)

        # Create a unique ID based on the style name
        style_id = style_name.lower().replace(" ", "_")

        # Add to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(id=style_id, vector=embedding, payload=payload)],
        )

        return style_id

    async def get_style(self, style_id: str) -> Optional[Dict]:
        """
        Get a rap style by ID.

        Args:
            style_id: ID of the style to retrieve

        Returns:
            Optional[Dict]: Style data if found, None otherwise
        """
        # Get from Qdrant
        result = self.client.retrieve(
            collection_name=self.collection_name, ids=[style_id]
        )

        if not result:
            return None

        return result[0].payload

    async def search_styles(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search for rap styles based on a query.

        Args:
            query: Search query
            limit: Maximum number of results to return

        Returns:
            List[Dict]: List of matching styles
        """
        # Generate embedding for the query
        embedding = await self.embeddings.aembed_query(query)

        # Search in Qdrant
        results = self.client.search(
            collection_name=self.collection_name, query_vector=embedding, limit=limit
        )

        return [hit.payload for hit in results]

    async def get_style_by_name(self, style_name: str) -> Optional[Dict]:
        """
        Get a rap style by name.

        Args:
            style_name: Name of the style to retrieve

        Returns:
            Optional[Dict]: Style data if found, None otherwise
        """
        # Search in Qdrant with filter
        results = self.client.search(
            collection_name=self.collection_name,
            query_filter=Filter(
                must=[
                    FieldCondition(key="style_name", match=MatchValue(value=style_name))
                ]
            ),
            limit=1,
        )

        if not results:
            return None

        return results[0].payload


# Create a repository instance
style_repository = StyleRepository()
