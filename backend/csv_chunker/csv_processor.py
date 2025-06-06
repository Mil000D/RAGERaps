"""
CSV processing service for artist data using LangChain components.
"""

import asyncio
import tempfile
import chardet
import re
import sys
from pathlib import Path
from typing import List, AsyncGenerator

from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from pydantic import ValidationError


sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from csv_chunker.artist import ArtistData, ProcessingResult
from app.services.vector_store_service import vector_store_service


class CSVProcessorService:
    """Service for processing CSV files with artist data."""

    def __init__(self):
        """Initialize the CSV processor service."""
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small", api_key=settings.openai_api_key
        )

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

        cleaned = re.sub(r"[\r\n]+", " ", text)

        cleaned = re.sub(r"\s+", " ", cleaned)

        cleaned = cleaned.strip()

        return cleaned

    def _detect_encoding(self, file_path: str) -> str:
        """
        Detect the encoding of a file using chardet.

        Args:
            file_path: Path to the file

        Returns:
            str: Detected encoding or 'utf-8' as fallback
        """
        try:
            with open(file_path, "rb") as file:
                raw_data = file.read(10000)
                result = chardet.detect(raw_data)
                encoding = result.get("encoding", "utf-8")
                confidence = result.get("confidence", 0)

                if confidence < 0.7:
                    encoding = "utf-8"

                return encoding
        except Exception:
            return "utf-8"

    def _get_encoding_fallbacks(self, detected_encoding: str) -> List[str]:
        """
        Get a list of encodings to try, starting with the detected one.

        Args:
            detected_encoding: The encoding detected by chardet

        Returns:
            List[str]: List of encodings to try in order
        """

        common_encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]

        if detected_encoding and detected_encoding.lower() not in [
            enc.lower() for enc in common_encodings
        ]:
            return [detected_encoding] + common_encodings

        if detected_encoding:
            encodings = [detected_encoding]
            encodings.extend(
                [
                    enc
                    for enc in common_encodings
                    if enc.lower() != detected_encoding.lower()
                ]
            )
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
            detected_encoding = self._detect_encoding(file_path)
            encodings_to_try = self._get_encoding_fallbacks(detected_encoding)

            loader = None
            successful_encoding = None

            for encoding in encodings_to_try:
                try:
                    loader = CSVLoader(
                        file_path=file_path,
                        encoding=encoding,
                        csv_args={
                            "delimiter": ",",
                            "quotechar": '"',
                            "fieldnames": ["Artist", "Genres", "Songs", "Lyric"],
                        },
                    )

                    test_docs = list(loader.lazy_load())
                    if test_docs:
                        successful_encoding = encoding
                        break

                except (UnicodeDecodeError, UnicodeError) as e:
                    if encoding == encodings_to_try[-1]:
                        errors.append(
                            f"Failed to decode file with any encoding. Last error: {str(e)}"
                        )
                        raise
                    continue
                except Exception as e:
                    if encoding == encodings_to_try[-1]:
                        errors.append(
                            f"Failed to load CSV with encoding {encoding}: {str(e)}"
                        )
                        raise
                    continue

            if not loader or not successful_encoding:
                raise Exception("Could not find a suitable encoding for the CSV file")

            print(f"✓ Successfully loaded CSV with {successful_encoding} encoding")

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
            collection_name=settings.qdrant_artists_collection_name,
        )

    async def _process_csv_in_batches(
        self, loader: CSVLoader, batch_size: int = 50
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
        batch_results = {"total": 0, "successful": 0, "failed": 0, "errors": []}

        try:
            for document in loader.lazy_load():
                batch.append(document)
                batch_results["total"] += 1

                if len(batch) >= batch_size:
                    batch_result = await self._process_document_batch(batch)
                    batch_results["successful"] += batch_result["successful"]
                    batch_results["failed"] += batch_result["failed"]
                    batch_results["errors"].extend(batch_result["errors"])

                    yield batch_results.copy()

                    batch = []
                    batch_results = {
                        "total": 0,
                        "successful": 0,
                        "failed": 0,
                        "errors": [],
                    }

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

        for doc in documents:
            try:
                artist_data = self._parse_document_to_artist_data(doc)
                artist_data_batch.append(artist_data)

            except ValidationError as e:
                failed += 1
                errors.append(f"Validation error for document: {str(e)}")
            except Exception as e:
                failed += 1
                errors.append(f"Parsing error for document: {str(e)}")

        if artist_data_batch:
            try:
                doc_ids = await vector_store_service.add_artist_data_batch(
                    artist_data_batch
                )
                successful += len(doc_ids)

            except Exception as e:
                failed += len(artist_data_batch)
                errors.append(f"Vector store error for batch: {str(e)}")

        return {"successful": successful, "failed": failed, "errors": errors}

    def _parse_document_to_artist_data(self, document: Document) -> ArtistData:
        """
        Parse a LangChain Document into an ArtistData model.

        Args:
            document: Document from CSVLoader

        Returns:
            ArtistData: Parsed and validated artist data
        """

        content = document.page_content

        data = {}
        for line in content.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()

        raw_lyric = data.get("Lyric", "")
        cleaned_lyric = self.clean_lyrics_text(raw_lyric)

        return ArtistData(
            artist=data.get("Artist", ""),
            genres=data.get("Genres", ""),
            songs=float(data.get("Songs", 0)),
            lyric=cleaned_lyric,
        )

csv_processor_service = CSVProcessorService()


async def main():
    """Main function to run CSV processor as standalone script."""
    import argparse

    parser = argparse.ArgumentParser(description="Process CSV files with artist data")
    parser.add_argument("file_path", help="Path to the CSV file to process")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of records to process in each batch (default: 50)",
    )

    args = parser.parse_args()

    if not Path(args.file_path).exists():
        print(f"Error: File '{args.file_path}' not found.")
        sys.exit(1)

    print(f"Processing CSV file: {args.file_path}")
    print(f"Batch size: {args.batch_size}")
    print("-" * 50)

    try:
        result = await csv_processor_service.process_csv_file(args.file_path)

        print("\n" + "=" * 50)
        print("PROCESSING RESULTS")
        print("=" * 50)
        print(f"Total records processed: {result.total_records}")
        print(f"Successful records: {result.successful_records}")
        print(f"Failed records: {result.failed_records}")
        print(
            f"Success rate: {(result.successful_records / result.total_records * 100):.1f}%"
            if result.total_records > 0
            else "0%"
        )
        print(f"Collection name: {result.collection_name}")

        if result.errors:
            print(f"\nErrors encountered ({len(result.errors)}):")
            for i, error in enumerate(result.errors[:10], 1):
                print(f"  {i}. {error}")
            if len(result.errors) > 10:
                print(f"  ... and {len(result.errors) - 10} more errors")

        print("\n✓ Processing completed successfully!")

    except Exception as e:
        print(f"\n✗ Processing failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
