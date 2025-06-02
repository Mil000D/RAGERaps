"""
API routes for artist data processing and search.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel

from app.models.artist import ProcessingResult
from app.services.data_pipeline_service import data_pipeline_service


router = APIRouter(prefix="/artists", tags=["artists"])


class SearchRequest(BaseModel):
    """Request model for artist search."""
    query: str
    k: int = 5
    include_lyrics: bool = True
    filter_by_genre: Optional[List[str]] = None
    filter_by_artist: Optional[str] = None


class CSVContentRequest(BaseModel):
    """Request model for CSV content processing."""
    csv_content: str


@router.post("/upload-csv", response_model=ProcessingResult)
async def upload_csv_file(file: UploadFile = File(...)):
    """
    Upload and process a CSV file with artist data with proper Unicode handling.

    Args:
        file: CSV file with columns: Artist, Genres, Songs, Lyric

    Returns:
        ProcessingResult: Summary of processing results
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    try:
        # Read file content as bytes
        content = await file.read()

        # Try to decode with different encodings
        csv_content = None
        encodings_to_try = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']

        for encoding in encodings_to_try:
            try:
                csv_content = content.decode(encoding)
                break
            except UnicodeDecodeError:
                if encoding == encodings_to_try[-1]:  # Last encoding failed
                    raise HTTPException(
                        status_code=400,
                        detail="Could not decode the CSV file. Please ensure it's properly encoded."
                    )
                continue

        if csv_content is None:
            raise HTTPException(
                status_code=400,
                detail="Could not decode the CSV file with any supported encoding."
            )

        # Process the CSV content
        result = await data_pipeline_service.process_csv_string(csv_content)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV file: {str(e)}")


@router.post("/process-csv", response_model=ProcessingResult)
async def process_csv_content(request: CSVContentRequest):
    """
    Process CSV content directly from request body.
    
    Args:
        request: CSV content as string
        
    Returns:
        ProcessingResult: Summary of processing results
    """
    try:
        result = await data_pipeline_service.process_csv_string(request.csv_content)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV content: {str(e)}")


@router.post("/search", response_model=List[Dict[str, Any]])
async def search_artists(request: SearchRequest):
    """
    Search for artists using semantic similarity.
    
    Args:
        request: Search parameters
        
    Returns:
        List[Dict[str, Any]]: Search results
    """
    try:
        results = await data_pipeline_service.search_artists(
            query=request.query,
            k=request.k,
            include_lyrics=request.include_lyrics,
            filter_by_genre=request.filter_by_genre,
            filter_by_artist=request.filter_by_artist
        )
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_artists_get(
    query: str = Query(..., description="Search query"),
    k: int = Query(5, description="Number of results to return"),
    include_lyrics: bool = Query(True, description="Include full lyrics in results"),
    filter_by_genre: Optional[str] = Query(None, description="Filter by genre (comma-separated for multiple)"),
    filter_by_artist: Optional[str] = Query(None, description="Filter by artist name")
):
    """
    Search for artists using GET request with query parameters.
    
    Args:
        query: Search query
        k: Number of results to return
        include_lyrics: Include full lyrics in results
        filter_by_genre: Filter by genre (comma-separated for multiple)
        filter_by_artist: Filter by artist name
        
    Returns:
        List[Dict[str, Any]]: Search results
    """
    try:
        # Parse genres if provided
        genres_filter = None
        if filter_by_genre:
            genres_filter = [g.strip() for g in filter_by_genre.split(',') if g.strip()]
        
        results = await data_pipeline_service.search_artists(
            query=query,
            k=k,
            include_lyrics=include_lyrics,
            filter_by_genre=genres_filter,
            filter_by_artist=filter_by_artist
        )
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/by-name/{artist_name}", response_model=Optional[Dict[str, Any]])
async def get_artist_by_name(artist_name: str):
    """
    Get a specific artist by name.
    
    Args:
        artist_name: Name of the artist
        
    Returns:
        Optional[Dict[str, Any]]: Artist data if found
    """
    try:
        result = await data_pipeline_service.get_artist_by_name(artist_name)
        if not result:
            raise HTTPException(status_code=404, detail=f"Artist '{artist_name}' not found")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get artist: {str(e)}")


@router.get("/by-genre/{genre}", response_model=List[Dict[str, Any]])
async def get_artists_by_genre(
    genre: str,
    k: int = Query(10, description="Number of results to return")
):
    """
    Get artists by genre.
    
    Args:
        genre: Genre to search for
        k: Number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of artists in the genre
    """
    try:
        results = await data_pipeline_service.get_artists_by_genre(genre, k)
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get artists by genre: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any])
async def get_collection_stats():
    """
    Get statistics about the artists collection.
    
    Returns:
        Dict[str, Any]: Collection statistics
    """
    try:
        stats = await data_pipeline_service.get_collection_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collection stats: {str(e)}")


@router.delete("/clear", response_model=Dict[str, Any])
async def clear_collection():
    """
    Clear all data from the artists collection.
    
    Returns:
        Dict[str, Any]: Operation result
    """
    try:
        result = await data_pipeline_service.clear_collection()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear collection: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Perform a health check on the pipeline components.
    
    Returns:
        Dict[str, Any]: Health check results
    """
    try:
        health = await data_pipeline_service.health_check()
        return health
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
