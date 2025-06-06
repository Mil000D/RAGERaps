"""
Artist retrieval tool for accessing vector store data during agent execution.
"""

import logging
from typing import List, Optional

from langchain_core.tools import BaseTool
from langchain_core.documents import Document

from app.services.vector_store_service import vector_store_service

logger = logging.getLogger(__name__)


class ArtistRetrievalTool(BaseTool):
    """Tool for retrieving artist lyrics and style information from the vector store."""

    name: str = "retrieve_artist_data"
    description: str = "Retrieve artist lyrics and style information from the vector store. Use this to get rap style data and lyrics for specific artists or similar artists in a given style. IMPORTANT: Always pass the 'style' parameter when you know the rap style context (e.g., aggressive, melodic, storytelling, etc.) to get more relevant results."

    def _run(
        self,
        artist_name: str,
        style: Optional[str] = None,
        k: Optional[int] = 5,
        include_similar: Optional[bool] = True,
    ) -> str:
        """
        Synchronous implementation of the artist retrieval tool.

        Args:
            artist_name: Name of the artist to retrieve data for
            style: Optional style/genre to focus the search
            k: Number of documents to retrieve
            include_similar: Whether to include similar artists

        Returns:
            Formatted string with artist data and lyrics
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                self._arun(artist_name, style, k, include_similar)
            )
        except RuntimeError:
            return asyncio.run(self._arun(artist_name, style, k, include_similar))

    async def _arun(
        self,
        artist_name: str,
        style: Optional[str] = None,
        k: Optional[int] = 5,
        include_similar: Optional[bool] = True,
    ) -> str:
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
            k = min(k or 5, 10)

            if style:
                search_query = f"{artist_name} {style} rap lyrics style flow"
            else:
                search_query = f"{artist_name} rap lyrics style"

            artist_docs = await self._safe_search(search_query, k)

            similar_docs = []
            if include_similar and len(artist_docs) < k:
                remaining_k = k - len(artist_docs)
                if style:
                    style_query = f"{style} rap lyrics style flow technique"
                else:
                    style_query = "rap lyrics style flow technique"

                all_docs = await self._safe_search(style_query, remaining_k * 2)

                similar_docs = [
                    doc
                    for doc in all_docs
                    if doc.metadata.get("artist", "").lower() != artist_name.lower()
                ][:remaining_k]

            return self._format_results(artist_name, artist_docs, similar_docs, style)

        except Exception as e:
            logger.error(f"Error in artist retrieval tool: {str(e)}")
            return f"Error retrieving data for {artist_name}: {str(e)}"

    async def _safe_search(self, query: str, k: int) -> List[Document]:
        """
        Perform a safe vector store search with error handling.

        Args:
            query: Search query
            k: Number of results

        Returns:
            List of retrieved documents
        """
        try:
            results = await vector_store_service.search_artists(query=query, k=k)
            return results
        except Exception as e:
            logger.warning(f"Vector store search failed: {str(e)}")
            return []

    def _format_results(
        self,
        artist_name: str,
        artist_docs: List[Document],
        similar_docs: List[Document],
        style: Optional[str],
    ) -> str:
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

        style_text = f" ({style})" if style else ""
        result_parts.append(f"=== ARTIST DATA: {artist_name}{style_text} ===")

        if artist_docs:
            result_parts.append(f"\n--- {artist_name} LYRICS & STYLE ---")

            all_genres = set()
            total_songs = 0

            for i, doc in enumerate(artist_docs[:3], 1):
                full_lyrics = doc.metadata.get("lyric", "")
                if full_lyrics:
                    lyrics_preview = (
                        full_lyrics[:1500] + "..."
                        if len(full_lyrics) > 1500
                        else full_lyrics
                    )
                    result_parts.append(f"\nLyrics Sample {i}:")
                    result_parts.append(lyrics_preview)

                genres = doc.metadata.get("genres", [])
                if isinstance(genres, list):
                    all_genres.update(genres)

                songs_count = doc.metadata.get("songs_count", 0)
                if isinstance(songs_count, (int, float)):
                    total_songs += int(songs_count)

            if all_genres:
                result_parts.append(f"\nGenres: {', '.join(sorted(all_genres))}")
            if total_songs > 0:
                result_parts.append(f"Total Songs in Database: {total_songs}")

            result_parts.append(
                f"Retrieved {len(artist_docs)} lyrical samples from {artist_name}"
            )
        else:
            result_parts.append(f"\n--- NO SPECIFIC DATA FOUND FOR {artist_name} ---")

        if similar_docs:
            result_parts.append(
                f"\n--- SIMILAR {style.upper() if style else 'RAP'} ARTISTS ---"
            )

            similar_artists = set()
            for doc in similar_docs[:3]:
                artist = doc.metadata.get("artist", "Unknown")
                similar_artists.add(artist)

                full_lyrics = doc.metadata.get("lyric", "")
                if full_lyrics:
                    lyrics_preview = (
                        full_lyrics[:1500] + "..."
                        if len(full_lyrics) > 1500
                        else full_lyrics
                    )
                    result_parts.append(f"\n{artist} Style Example:")
                    result_parts.append(lyrics_preview)

            result_parts.append(
                f"\nSimilar Artists Found: {', '.join(sorted(similar_artists))}"
            )

        result_parts.append("\n=== END ARTIST DATA ===")
        result_parts.append(
            f"Total Documents Retrieved: {len(artist_docs) + len(similar_docs)}"
        )

        if not artist_docs and not similar_docs:
            result_parts.append(
                f"\nNo lyrical data found for {artist_name}. Consider using general rap style characteristics."
            )

        return "\n".join(result_parts)


artist_retrieval_tool = ArtistRetrievalTool()
