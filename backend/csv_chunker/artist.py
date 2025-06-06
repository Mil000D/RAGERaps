"""
Artist data models for CSV processing.
"""

from typing import List
from pydantic import BaseModel, Field


class ArtistData(BaseModel):
    """Model representing an artist's data from CSV."""

    artist: str = Field(..., description="Artist name")
    genres: str = Field(..., description="Semicolon-separated genres")
    songs: float = Field(..., description="Number of songs")
    lyric: str = Field(..., description="Song lyrics text")


class ProcessingResult(BaseModel):
    """Result of processing a CSV file."""

    total_records: int = Field(..., description="Total number of records processed")
    successful_records: int = Field(
        ..., description="Number of successfully processed records"
    )
    failed_records: int = Field(..., description="Number of failed records")
    errors: List[str] = Field(
        default_factory=list, description="List of error messages"
    )
    collection_name: str = Field(..., description="Name of the Qdrant collection used")
