"""
Artist data models for CSV processing.
"""
import re
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class ArtistData(BaseModel):
    """Model representing an artist's data from CSV."""

    artist: str = Field(..., description="Artist name")
    genres: str = Field(..., description="Semicolon-separated genres")
    songs: float = Field(..., description="Number of songs")
    lyric: str = Field(..., description="Song lyrics text")

    @staticmethod
    def clean_lyrics_text(text: str) -> str:
        """
        Clean lyrics text by removing newline characters and handling special characters.

        Args:
            text: Raw lyrics text that may contain newlines

        Returns:
            str: Cleaned lyrics text suitable for CSV storage
        """
        if not isinstance(text, str):
            return str(text) if text is not None else ""

        # Remove all types of newline characters
        cleaned = re.sub(r'[\r\n]+', ' ', text)

        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Strip leading and trailing whitespace
        cleaned = cleaned.strip()

        return cleaned
    
    @validator('genres')
    def validate_genres(cls, v):
        """Validate that genres is a non-empty string."""
        if not v or not v.strip():
            raise ValueError("Genres cannot be empty")
        return v.strip()
    
    @validator('artist')
    def validate_artist(cls, v):
        """Validate that artist name is not empty."""
        if not v or not v.strip():
            raise ValueError("Artist name cannot be empty")
        return v.strip()
    
    @validator('lyric')
    def validate_lyric(cls, v):
        """Validate and clean lyric text."""
        if not v or not str(v).strip():
            raise ValueError("Lyric cannot be empty")
        # Clean the lyrics text to remove newlines and normalize whitespace
        cleaned = cls.clean_lyrics_text(v)
        if not cleaned:
            raise ValueError("Lyric cannot be empty after cleaning")
        return cleaned
    
    @validator('songs')
    def validate_songs(cls, v):
        """Validate that songs count is positive."""
        if v <= 0:
            raise ValueError("Songs count must be positive")
        return v
    
    def get_parsed_genres(self) -> List[str]:
        """Parse semicolon-separated genres into a list."""
        return [genre.strip() for genre in self.genres.split(';') if genre.strip()]
    
    def get_embedding_content(self) -> str:
        """
        Generate content for embedding from artist, genres, and songs count.
        This will be used to create vector embeddings for semantic search.
        """
        genres_list = self.get_parsed_genres()
        genres_text = ", ".join(genres_list)
        
        return f"Artist: {self.artist}. Genres: {genres_text}. Songs: {int(self.songs)} songs."
    
    def get_metadata(self) -> dict:
        """Generate metadata for the document."""
        return {
            "artist": self.artist,
            "genres": self.get_parsed_genres(),
            "songs_count": int(self.songs),
            "source": "csv_import"
        }


class ProcessingResult(BaseModel):
    """Result of processing a CSV file."""
    
    total_records: int = Field(..., description="Total number of records processed")
    successful_records: int = Field(..., description="Number of successfully processed records")
    failed_records: int = Field(..., description="Number of failed records")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    collection_name: str = Field(..., description="Name of the Qdrant collection used")
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_records == 0:
            return 0.0
        return (self.successful_records / self.total_records) * 100
