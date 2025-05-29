"""
Main data processing pipeline service for artist CSV data.
"""
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.models.artist import ProcessingResult
from app.services.csv_processor_service import csv_processor_service
from app.services.vector_store_service import vector_store_service
from app.db.database import db


class DataPipelineService:
    """Main service for orchestrating the data processing pipeline."""
    
    def __init__(self):
        """Initialize the data pipeline service."""
        self.csv_processor = csv_processor_service
        self.vector_store = vector_store_service
    
    async def initialize(self) -> None:
        """Initialize the pipeline by ensuring database collections exist."""
        await db.initialize()
        # Ensure the artists collection is properly set up
        await self.vector_store._ensure_artists_collection_exists()
    
    async def process_csv_file(self, file_path: str) -> ProcessingResult:
        """
        Process a CSV file through the complete pipeline.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            ProcessingResult: Summary of processing results
        """
        # Ensure pipeline is initialized
        await self.initialize()
        
        # Validate file exists
        if not Path(file_path).exists():
            return ProcessingResult(
                total_records=0,
                successful_records=0,
                failed_records=1,
                errors=[f"File not found: {file_path}"],
                collection_name=settings.qdrant_artists_collection_name
            )
        
        # Process the CSV file
        result = await self.csv_processor.process_csv_file(file_path)
        return result
    
    async def process_csv_string(self, csv_content: str) -> ProcessingResult:
        """
        Process CSV content from a string through the complete pipeline.
        
        Args:
            csv_content: CSV content as string
            
        Returns:
            ProcessingResult: Summary of processing results
        """
        # Ensure pipeline is initialized
        await self.initialize()
        
        # Process the CSV content
        result = await self.csv_processor.process_csv_string(csv_content)
        return result
    
    async def search_artists(
        self, 
        query: str, 
        k: int = 5,
        include_lyrics: bool = True,
        filter_by_genre: Optional[List[str]] = None,
        filter_by_artist: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for artists using semantic similarity.
        
        Args:
            query: Search query
            k: Number of results to return
            include_lyrics: Whether to include full lyrics in results
            filter_by_genre: Optional list of genres to filter by
            filter_by_artist: Optional artist name to filter by
            
        Returns:
            List[Dict[str, Any]]: Search results with metadata
        """
        # Build filter dictionary
        filter_dict = {}
        if filter_by_genre:
            filter_dict["genres"] = {"$in": filter_by_genre}
        if filter_by_artist:
            filter_dict["artist"] = filter_by_artist
        
        # Perform search
        results = await self.vector_store.search_artists_with_scores(
            query=query,
            k=k,
            filter_dict=filter_dict if filter_dict else None
        )
        
        # Format results
        formatted_results = []
        for doc, score in results:
            result = {
                "artist": doc.metadata.get("artist"),
                "genres": doc.metadata.get("genres", []),
                "songs_count": doc.metadata.get("songs_count"),
                "similarity_score": score,
                "embedding_content": doc.page_content
            }
            
            if include_lyrics:
                result["lyric"] = doc.metadata.get("lyric")
            
            formatted_results.append(result)
        
        return formatted_results
    
    async def get_artist_by_name(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific artist by name.
        
        Args:
            artist_name: Name of the artist
            
        Returns:
            Optional[Dict[str, Any]]: Artist data if found
        """
        results = await self.search_artists(
            query=artist_name,
            k=1,
            filter_by_artist=artist_name
        )
        
        return results[0] if results else None
    
    async def get_artists_by_genre(
        self, 
        genre: str, 
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get artists by genre.
        
        Args:
            genre: Genre to search for
            k: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of artists in the genre
        """
        return await self.search_artists(
            query=f"Genre: {genre}",
            k=k,
            filter_by_genre=[genre]
        )
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the artists collection.
        
        Returns:
            Dict[str, Any]: Collection statistics
        """
        return await self.vector_store.get_collection_info()
    
    async def clear_collection(self) -> Dict[str, Any]:
        """
        Clear all data from the artists collection.
        
        Returns:
            Dict[str, Any]: Operation result
        """
        try:
            client = self.vector_store.get_client()
            collection_name = settings.qdrant_artists_collection_name
            
            # Delete and recreate the collection
            if client.collection_exists(collection_name):
                client.delete_collection(collection_name)
            
            # Recreate the collection
            await self.vector_store._ensure_artists_collection_exists()
            
            return {
                "success": True,
                "message": f"Collection '{collection_name}' cleared successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to clear collection: {str(e)}"
            }
    
    async def delete_artists_by_ids(self, doc_ids: List[str]) -> Dict[str, Any]:
        """
        Delete specific artists by their document IDs.
        
        Args:
            doc_ids: List of document IDs to delete
            
        Returns:
            Dict[str, Any]: Operation result
        """
        try:
            await self.vector_store.delete_artist_data(doc_ids)
            return {
                "success": True,
                "message": f"Deleted {len(doc_ids)} artists successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to delete artists: {str(e)}"
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the pipeline components.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        health_status = {
            "pipeline": "healthy",
            "components": {}
        }
        
        try:
            # Check Qdrant connection
            client = self.vector_store.get_client()
            collections = client.get_collections()
            health_status["components"]["qdrant"] = {
                "status": "healthy",
                "collections_count": len(collections.collections)
            }
        except Exception as e:
            health_status["components"]["qdrant"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["pipeline"] = "unhealthy"
        
        try:
            # Check embeddings service
            embedding_test = await asyncio.to_thread(
                self.vector_store.embeddings.embed_query,
                "test"
            )
            health_status["components"]["embeddings"] = {
                "status": "healthy",
                "embedding_dimension": len(embedding_test)
            }
        except Exception as e:
            health_status["components"]["embeddings"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["pipeline"] = "unhealthy"
        
        return health_status


# Create a singleton instance
data_pipeline_service = DataPipelineService()
