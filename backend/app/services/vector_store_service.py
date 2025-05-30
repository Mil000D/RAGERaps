"""
Vector store service for managing artist data in Qdrant using LangChain.
"""
import asyncio
from typing import List, Optional, Dict, Any
from uuid import uuid4

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue

from app.core.config import settings
from app.models.artist import ArtistData


class VectorStoreService:
    """Service for managing vector store operations with artist data."""
    
    def __init__(self):
        """Initialize the vector store service."""
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.openai_api_key)
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
                    url=settings.qdrant_url, 
                    api_key=settings.qdrant_api_key
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
            
            # Ensure collection exists
            await self._ensure_artists_collection_exists()
            
            # Create vector store instance
            self._vector_store = QdrantVectorStore(
                client=client,
                collection_name=settings.qdrant_artists_collection_name,
                embedding=self.embeddings
            )
        
        return self._vector_store

    def _convert_dict_filter_to_qdrant_filter(self, filter_dict: Dict[str, Any]) -> Filter:
        """
        Convert a dictionary filter to Qdrant Filter format.

        Args:
            filter_dict: Dictionary filter (e.g., {"artist": "Eminem"})

        Returns:
            Filter: Qdrant Filter object
        """
        conditions = []

        for key, value in filter_dict.items():
            # Create a field condition for exact match
            condition = FieldCondition(
                key=key,
                match=MatchValue(value=value)
            )
            conditions.append(condition)

        # If multiple conditions, combine with AND logic
        if len(conditions) == 1:
            return Filter(must=[conditions[0]])
        else:
            return Filter(must=conditions)

    async def _ensure_artists_collection_exists(self) -> None:
        """Ensure the artists collection exists in Qdrant."""
        client = self.get_client()
        collection_name = settings.qdrant_artists_collection_name
        
        if not client.collection_exists(collection_name):
            # Create collection with appropriate vector size for text-embedding-3-small
            # text-embedding-3-small has 1536 dimensions
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
    
    async def add_artist_data(self, artist_data: ArtistData) -> str:
        """
        Add a single artist's data to the vector store.
        
        Args:
            artist_data: The artist data to add
            
        Returns:
            str: The document ID
        """
        vector_store = await self.get_vector_store()
        
        # Create document for vector storage
        document = Document(
            page_content=artist_data.get_embedding_content(),
            metadata={
                **artist_data.get_metadata(),
                "lyric": artist_data.lyric  # Store full lyric as metadata for retrieval
            }
        )
        
        # Generate unique ID
        doc_id = str(uuid4())
        
        # Add document to vector store
        await asyncio.to_thread(
            vector_store.add_documents,
            documents=[document],
            ids=[doc_id]
        )
        
        return doc_id
    
    async def add_artist_data_batch(self, artist_data_list: List[ArtistData]) -> List[str]:
        """
        Add multiple artist data entries to the vector store in batch.
        
        Args:
            artist_data_list: List of artist data to add
            
        Returns:
            List[str]: List of document IDs
        """
        if not artist_data_list:
            return []
        
        vector_store = await self.get_vector_store()
        
        # Create documents for vector storage
        documents = []
        doc_ids = []
        
        for artist_data in artist_data_list:
            document = Document(
                page_content=artist_data.get_embedding_content(),
                metadata={
                    **artist_data.get_metadata(),
                    "lyric": artist_data.lyric  # Store full lyric as metadata for retrieval
                }
            )
            documents.append(document)
            doc_ids.append(str(uuid4()))
        
        # Add documents to vector store in batch
        await asyncio.to_thread(
            vector_store.add_documents,
            documents=documents,
            ids=doc_ids
        )
        
        return doc_ids
    
    async def search_artists(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
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

        # Convert filter_dict to Qdrant filter format if provided
        qdrant_filter = None
        if filter_dict:
            qdrant_filter = self._convert_dict_filter_to_qdrant_filter(filter_dict)

        # Perform similarity search
        results = await asyncio.to_thread(
            vector_store.similarity_search,
            query=query,
            k=k,
            filter=qdrant_filter
        )

        return results
    
    async def search_artists_with_scores(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """
        Search for artists with similarity scores.

        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Optional metadata filters (e.g., {"artist": "Eminem"})

        Returns:
            List[tuple[Document, float]]: Search results with scores
        """
        vector_store = await self.get_vector_store()

        # Convert filter_dict to Qdrant filter format if provided
        qdrant_filter = None
        if filter_dict:
            qdrant_filter = self._convert_dict_filter_to_qdrant_filter(filter_dict)

        # Perform similarity search with scores
        results = await asyncio.to_thread(
            vector_store.similarity_search_with_score,
            query=query,
            k=k,
            filter=qdrant_filter
        )

        return results
    
    async def delete_artist_data(self, doc_ids: List[str]) -> None:
        """
        Delete artist data by document IDs.
        
        Args:
            doc_ids: List of document IDs to delete
        """
        vector_store = await self.get_vector_store()
        
        await asyncio.to_thread(
            vector_store.delete,
            ids=doc_ids
        )
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the artists collection.
        
        Returns:
            Dict[str, Any]: Collection information
        """
        client = self.get_client()
        collection_name = settings.qdrant_artists_collection_name
        
        if not client.collection_exists(collection_name):
            return {"exists": False}
        
        collection_info = client.get_collection(collection_name)
        return {
            "exists": True,
            "vectors_count": collection_info.vectors_count,
            "indexed_vectors_count": collection_info.indexed_vectors_count,
            "points_count": collection_info.points_count,
            "status": collection_info.status
        }


# Create a singleton instance
vector_store_service = VectorStoreService()
