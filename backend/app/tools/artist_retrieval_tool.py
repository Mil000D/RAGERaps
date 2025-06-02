"""
Artist retrieval tool for accessing vector store data during agent execution.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool
from langchain_core.documents import Document

from app.services.vector_store_service import vector_store_service

logger = logging.getLogger(__name__)


class ArtistRetrievalInput(BaseModel):
    """Input schema for artist retrieval tool."""
    artist_name: str = Field(description="Name of the artist to retrieve lyrics and style information for")
    style: Optional[str] = Field(default=None, description="Musical style/genre to focus the search on")
    k: Optional[int] = Field(default=5, description="Number of documents to retrieve (max 10)")
    include_similar: Optional[bool] = Field(default=True, description="Whether to include similar artists if specific artist data is limited")


class ArtistRetrievalTool(BaseTool):
    """Tool for retrieving artist lyrics and style information from the vector store."""

    name: str = "retrieve_artist_data"
    description: str = """Retrieve lyrics and style information for a specific artist from the vector database.

    This tool searches the artists_lyrics collection for:
    - Complete lyrics content from the specified artist
    - Style characteristics and genre information
    - Similar artists' examples if the specific artist has limited data

    Use this when you need authentic lyrical content, style examples, or genre information
    to generate more accurate and style-appropriate rap verses or make informed judgments.

    Input should include the artist name and optionally the style/genre to focus on."""

    args_schema: Type[BaseModel] = ArtistRetrievalInput
    
    async def _arun(self, artist_name: str, style: Optional[str] = None, k: Optional[int] = 5, include_similar: Optional[bool] = True) -> str:
        """
        Async implementation of the artist retrieval tool.
        
        Args:
            artist_name: Name of the artist to retrieve data for
            style: Optional style/genre to focus the search
            k: Number of documents to retrieve
            include_similar: Whether to include similar artists
            
        Returns:
            Formatted string with artist data and lyrics
        """
        try:
            # Validate and limit k
            k = min(k or 5, 10)
            
            # Build search query
            if style:
                search_query = f"{artist_name} {style} rap lyrics style flow"
            else:
                search_query = f"{artist_name} rap lyrics style"
            
            # Search for artist-specific content
            artist_filter = {"artist": artist_name}
            artist_docs = await self._safe_search(search_query, k, artist_filter)
            
            # Search for similar artists if needed and requested
            similar_docs = []
            if include_similar and len(artist_docs) < k:
                remaining_k = k - len(artist_docs)
                if style:
                    style_query = f"{style} rap lyrics style flow technique"
                else:
                    style_query = f"rap lyrics style flow technique"
                
                all_docs = await self._safe_search(style_query, remaining_k * 2, None)
                # Filter out the original artist
                similar_docs = [
                    doc for doc in all_docs 
                    if doc.metadata.get("artist", "").lower() != artist_name.lower()
                ][:remaining_k]
            
            # Format the results
            return self._format_results(artist_name, artist_docs, similar_docs, style)
            
        except Exception as e:
            logger.error(f"Error in artist retrieval tool: {str(e)}")
            return f"Error retrieving data for {artist_name}: {str(e)}"
    
    def _run(self, artist_name: str, style: Optional[str] = None, k: Optional[int] = 5, include_similar: Optional[bool] = True) -> str:
        """Sync wrapper for async implementation."""
        return asyncio.run(self._arun(artist_name, style, k, include_similar))
    
    async def _safe_search(self, query: str, k: int, filter_dict: Optional[Dict[str, Any]]) -> List[Document]:
        """
        Perform a safe vector store search with error handling.
        
        Args:
            query: Search query
            k: Number of results
            filter_dict: Optional metadata filters
            
        Returns:
            List of retrieved documents
        """
        try:
            results = await vector_store_service.search_artists(
                query=query,
                k=k,
                filter_dict=filter_dict
            )
            return results
        except Exception as e:
            logger.warning(f"Vector store search failed: {str(e)}")
            return []
    
    def _format_results(self, artist_name: str, artist_docs: List[Document], similar_docs: List[Document], style: Optional[str]) -> str:
        """
        Format the retrieval results into a readable string.
        
        Args:
            artist_name: Name of the queried artist
            artist_docs: Documents specific to the artist
            similar_docs: Documents from similar artists
            style: Optional style parameter
            
        Returns:
            Formatted string with artist data
        """
        result_parts = []
        
        # Header
        style_text = f" ({style})" if style else ""
        result_parts.append(f"=== ARTIST DATA: {artist_name}{style_text} ===")
        
        # Artist-specific content
        if artist_docs:
            result_parts.append(f"\n--- {artist_name} LYRICS & STYLE ---")
            
            # Collect genres and characteristics
            all_genres = set()
            total_songs = 0
            
            for i, doc in enumerate(artist_docs[:3], 1):  # Limit to 3 examples
                # Extract full lyrics from metadata
                full_lyrics = doc.metadata.get("lyric", "")
                if full_lyrics:
                    # Show first 300 characters of lyrics
                    lyrics_preview = full_lyrics[:300] + "..." if len(full_lyrics) > 300 else full_lyrics
                    result_parts.append(f"\nLyrics Sample {i}:")
                    result_parts.append(lyrics_preview)
                
                # Collect metadata
                genres = doc.metadata.get("genres", [])
                if isinstance(genres, list):
                    all_genres.update(genres)
                
                songs_count = doc.metadata.get("songs_count", 0)
                if isinstance(songs_count, (int, float)):
                    total_songs += int(songs_count)
            
            # Add summary info
            if all_genres:
                result_parts.append(f"\nGenres: {', '.join(sorted(all_genres))}")
            if total_songs > 0:
                result_parts.append(f"Total Songs in Database: {total_songs}")
            
            result_parts.append(f"Retrieved {len(artist_docs)} lyrical samples from {artist_name}")
        else:
            result_parts.append(f"\n--- NO SPECIFIC DATA FOUND FOR {artist_name} ---")
        
        # Similar artists content
        if similar_docs:
            result_parts.append(f"\n--- SIMILAR {style.upper() if style else 'RAP'} ARTISTS ---")
            
            similar_artists = set()
            for doc in similar_docs[:3]:  # Limit to 3 examples
                artist = doc.metadata.get("artist", "Unknown")
                similar_artists.add(artist)
                
                full_lyrics = doc.metadata.get("lyric", "")
                if full_lyrics:
                    lyrics_preview = full_lyrics[:200] + "..." if len(full_lyrics) > 200 else full_lyrics
                    result_parts.append(f"\n{artist} Style Example:")
                    result_parts.append(lyrics_preview)
            
            result_parts.append(f"\nSimilar Artists Found: {', '.join(sorted(similar_artists))}")
        
        # Footer with usage instructions
        result_parts.append(f"\n=== END ARTIST DATA ===")
        result_parts.append(f"Total Documents Retrieved: {len(artist_docs) + len(similar_docs)}")
        
        if not artist_docs and not similar_docs:
            result_parts.append(f"\nNo lyrical data found for {artist_name}. Consider using general rap style characteristics.")
        
        return "\n".join(result_parts)


# Create tool instance
artist_retrieval_tool = ArtistRetrievalTool()
