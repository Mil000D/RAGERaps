"""
Vector store service for managing artist data in Qdrant using LangChain.
"""

from typing import List, Optional

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
)

from app.core.config import settings


class VectorStoreService:
    """Service for managing vector store operations with artist data."""

    def __init__(self):
        """Initialize the vector store service."""
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small", api_key=settings.openai_api_key
        )
        self._client: Optional[QdrantClient] = None
        self._vector_store: Optional[QdrantVectorStore] = None

    def get_client(self) -> QdrantClient:
        """
        Get or create a Qdrant client instance.

        Returns:
            QdrantClient: The Qdrant client instance
        """
        if self._client is None:
            if settings.qdrant_api_key:
                self._client = QdrantClient(
                    url=settings.qdrant_url, api_key=settings.qdrant_api_key
                )
            else:
                self._client = QdrantClient(url=settings.qdrant_url)
        return self._client

    async def get_vector_store(self) -> QdrantVectorStore:
        """
        Get or create a QdrantVectorStore instance for artists collection.

        Returns:
            QdrantVectorStore: The vector store instance
        """
        if self._vector_store is None:
            client = self.get_client()

            await self._ensure_artists_collection_exists()

            self._vector_store = QdrantVectorStore(
                client=client,
                collection_name=settings.qdrant_artists_collection_name,
                embedding=self.embeddings,
            )

        return self._vector_store

    async def _ensure_artists_collection_exists(self) -> None:
        """Ensure the artists collection exists in Qdrant."""
        client = self.get_client()
        collection_name = settings.qdrant_artists_collection_name

        if not client.collection_exists(collection_name):
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )

            try:
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name="artist",
                    field_schema="keyword",
                )
            except Exception as e:
                print(f"Warning: Could not create artist index: {e}")

            try:
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name="song",
                    field_schema="keyword",
                )
            except Exception as e:
                print(f"Warning: Could not create song index: {e}")

            try:
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name="album",
                    field_schema="keyword",
                )
            except Exception as e:
                print(f"Warning: Could not create album index: {e}")

    async def search_artists(self, query: str, k: int = 5) -> List[Document]:
        """
        Search for artists using semantic similarity.

        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Optional metadata filters (e.g., {"artist": "Eminem"})

        Returns:
            List[Document]: Search results with lyrics in metadata
        """
        vector_store = await self.get_vector_store()

        try:
            results = await vector_store.asimilarity_search(query=query, k=k)
        except Exception as e:
            print(f"Vector store search failed: {e}")
            return []

        return results

    async def add_artist_data_batch(self, artist_data_list) -> List[str]:
        """
        Add multiple artist data records to the vector store.

        Args:
            artist_data_list: List of ArtistData objects

        Returns:
            List[str]: List of document IDs of stored data
        """
        vector_store = await self.get_vector_store()

        documents = []
        for artist_data in artist_data_list:
            content = f"Artist: {artist_data.artist}\nGenres: {artist_data.genres}\nLyrics: {artist_data.lyric}"

            metadata = {
                "artist": artist_data.artist,
                "genres": artist_data.genres,
                "songs": artist_data.songs,
                "lyric": artist_data.lyric,
            }

            document = Document(page_content=content, metadata=metadata)
            documents.append(document)

        doc_ids = await vector_store.aadd_documents(documents)
        return doc_ids


vector_store_service = VectorStoreService()
