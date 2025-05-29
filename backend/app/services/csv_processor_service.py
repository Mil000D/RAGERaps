"""
CSV processing service for artist data using LangChain components.
"""
import asyncio
import csv
import tempfile
import chardet
from pathlib import Path
from typing import List, Optional, AsyncGenerator
from uuid import uuid4

from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from pydantic import ValidationError

from app.core.config import settings
from app.models.artist import ArtistData, ProcessingResult
from app.services.vector_store_service import vector_store_service


class CSVProcessorService:
    """Service for processing CSV files with artist data."""

    def __init__(self):
        """Initialize the CSV processor service."""
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.openai_api_key)

    def _detect_encoding(self, file_path: str) -> str:
        """
        Detect the encoding of a file using chardet.

        Args:
            file_path: Path to the file

        Returns:
            str: Detected encoding or 'utf-8' as fallback
        """
        try:
            with open(file_path, 'rb') as file:
                # Read a sample of the file for detection
                raw_data = file.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)

                # If confidence is too low, fallback to utf-8
                if confidence < 0.7:
                    encoding = 'utf-8'

                return encoding
        except Exception:
            # If detection fails, fallback to utf-8
            return 'utf-8'

    def _get_encoding_fallbacks(self, detected_encoding: str) -> List[str]:
        """
        Get a list of encodings to try, starting with the detected one.

        Args:
            detected_encoding: The encoding detected by chardet

        Returns:
            List[str]: List of encodings to try in order
        """
        # Common encodings to try
        common_encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']

        # Start with detected encoding if it's not already in the list
        if detected_encoding and detected_encoding.lower() not in [enc.lower() for enc in common_encodings]:
            return [detected_encoding] + common_encodings

        # If detected encoding is already in common list, prioritize it
        if detected_encoding:
            encodings = [detected_encoding]
            encodings.extend([enc for enc in common_encodings if enc.lower() != detected_encoding.lower()])
            return encodings

        return common_encodings
    
    async def process_csv_file(self, file_path: str) -> ProcessingResult:
        """
        Process a CSV file and return processing results with proper encoding handling.

        Args:
            file_path: Path to the CSV file

        Returns:
            ProcessingResult: Summary of processing results
        """
        total_records = 0
        successful_records = 0
        failed_records = 0
        errors = []

        try:
            # Detect file encoding
            detected_encoding = self._detect_encoding(file_path)
            encodings_to_try = self._get_encoding_fallbacks(detected_encoding)

            loader = None
            successful_encoding = None

            # Try different encodings until one works
            for encoding in encodings_to_try:
                try:
                    # Load CSV using LangChain's CSVLoader with specific encoding
                    loader = CSVLoader(
                        file_path=file_path,
                        encoding=encoding,
                        csv_args={
                            "delimiter": ",",
                            "quotechar": "\"",
                            "fieldnames": ["Artist", "Genres", "Songs", "Lyric"]
                        }
                    )

                    # Test if the loader can read the file by trying to load one document
                    test_docs = list(loader.lazy_load())
                    if test_docs:  # If we can load at least one document, encoding is good
                        successful_encoding = encoding
                        break

                except (UnicodeDecodeError, UnicodeError) as e:
                    if encoding == encodings_to_try[-1]:  # Last encoding failed
                        errors.append(f"Failed to decode file with any encoding. Last error: {str(e)}")
                        raise
                    continue
                except Exception as e:
                    if encoding == encodings_to_try[-1]:  # Last encoding failed
                        errors.append(f"Failed to load CSV with encoding {encoding}: {str(e)}")
                        raise
                    continue

            if not loader or not successful_encoding:
                raise Exception("Could not find a suitable encoding for the CSV file")

            print(f"✓ Successfully loaded CSV with {successful_encoding} encoding")

            # Process documents in batches
            async for batch_result in self._process_csv_in_batches(loader):
                total_records += batch_result["total"]
                successful_records += batch_result["successful"]
                failed_records += batch_result["failed"]
                errors.extend(batch_result["errors"])

        except Exception as e:
            errors.append(f"Failed to process CSV file: {str(e)}")
            failed_records = total_records if total_records > 0 else 1

        return ProcessingResult(
            total_records=total_records,
            successful_records=successful_records,
            failed_records=failed_records,
            errors=errors,
            collection_name=settings.qdrant_artists_collection_name
        )
    
    async def process_csv_string(self, csv_content: str) -> ProcessingResult:
        """
        Process CSV content from a string with proper Unicode handling.

        Args:
            csv_content: CSV content as string

        Returns:
            ProcessingResult: Summary of processing results
        """
        # Create temporary file for CSV content with UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(csv_content)
            temp_file_path = temp_file.name

        try:
            result = await self.process_csv_file(temp_file_path)
            return result
        finally:
            # Clean up temporary file
            Path(temp_file_path).unlink(missing_ok=True)
    
    async def _process_csv_in_batches(
        self, 
        loader: CSVLoader, 
        batch_size: int = 50
    ) -> AsyncGenerator[dict, None]:
        """
        Process CSV documents in batches for better memory management.
        
        Args:
            loader: Configured CSVLoader instance
            batch_size: Number of documents to process in each batch
            
        Yields:
            dict: Batch processing results
        """
        batch = []
        batch_results = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # Use lazy loading to process documents one by one
            for document in loader.lazy_load():
                batch.append(document)
                batch_results["total"] += 1
                
                if len(batch) >= batch_size:
                    # Process current batch
                    batch_result = await self._process_document_batch(batch)
                    batch_results["successful"] += batch_result["successful"]
                    batch_results["failed"] += batch_result["failed"]
                    batch_results["errors"].extend(batch_result["errors"])
                    
                    yield batch_results.copy()
                    
                    # Reset for next batch
                    batch = []
                    batch_results = {
                        "total": 0,
                        "successful": 0,
                        "failed": 0,
                        "errors": []
                    }
            
            # Process remaining documents in the last batch
            if batch:
                batch_result = await self._process_document_batch(batch)
                batch_results["successful"] += batch_result["successful"]
                batch_results["failed"] += batch_result["failed"]
                batch_results["errors"].extend(batch_result["errors"])
                
                yield batch_results
                
        except Exception as e:
            batch_results["errors"].append(f"Error during batch processing: {str(e)}")
            batch_results["failed"] = batch_results["total"]
            yield batch_results
    
    async def _process_document_batch(self, documents: List[Document]) -> dict:
        """
        Process a batch of documents.

        Args:
            documents: List of Document objects from CSV

        Returns:
            dict: Batch processing results
        """
        successful = 0
        failed = 0
        errors = []
        artist_data_batch = []

        # First, parse all documents in the batch
        for doc in documents:
            try:
                # Parse document content into ArtistData model
                artist_data = self._parse_document_to_artist_data(doc)
                artist_data_batch.append(artist_data)

            except ValidationError as e:
                failed += 1
                errors.append(f"Validation error for document: {str(e)}")
            except Exception as e:
                failed += 1
                errors.append(f"Parsing error for document: {str(e)}")

        # Then, store the valid artist data in vector store as a batch
        if artist_data_batch:
            try:
                doc_ids = await vector_store_service.add_artist_data_batch(artist_data_batch)
                successful += len(doc_ids)

            except Exception as e:
                failed += len(artist_data_batch)
                errors.append(f"Vector store error for batch: {str(e)}")

        return {
            "successful": successful,
            "failed": failed,
            "errors": errors
        }
    
    def _parse_document_to_artist_data(self, document: Document) -> ArtistData:
        """
        Parse a LangChain Document into an ArtistData model.
        
        Args:
            document: Document from CSVLoader
            
        Returns:
            ArtistData: Parsed and validated artist data
        """
        # The document.page_content contains the CSV row data
        # We need to parse it back into individual fields
        content = document.page_content
        
        # Parse the content - CSVLoader formats it as key-value pairs
        data = {}
        for line in content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        
        return ArtistData(
            artist=data.get('Artist', ''),
            genres=data.get('Genres', ''),
            songs=float(data.get('Songs', 0)),
            lyric=data.get('Lyric', '')
        )
    
    async def _process_artist_data(self, artist_data: ArtistData) -> str:
        """
        Process individual artist data and store in vector database.

        Args:
            artist_data: Validated artist data

        Returns:
            str: Document ID of stored data
        """
        return await vector_store_service.add_artist_data(artist_data)


# Create a singleton instance
csv_processor_service = CSVProcessorService()
