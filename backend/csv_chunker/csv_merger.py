"""
CSV Merger Tool for RAGERaps

This module provides functionality to merge two CSV files containing artist and song data.
It merges based on Link/ALink columns and filters for English language songs only.
"""

import pandas as pd
import argparse
import sys
from pathlib import Path
from typing import Optional

sys.path.append(str(Path(__file__).parent.parent))
from app.utils.common import clean_lyrics_text


class CSVMerger:
    """Handles merging of artist and song CSV files."""

    def __init__(self):
        self.artists_df: Optional[pd.DataFrame] = None
        self.songs_df: Optional[pd.DataFrame] = None
        self.merged_df: Optional[pd.DataFrame] = None

    def load_artists_csv(self, file_path: str) -> None:
        """
        Load the artists CSV file with proper Unicode handling.

        Expected columns: Artist, Genres, Songs, Popularity, Link

        Args:
            file_path: Path to the artists CSV file
        """
        try:
            encodings_to_try = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]

            for encoding in encodings_to_try:
                try:
                    self.artists_df = pd.read_csv(file_path, encoding=encoding)
                    print(f"✓ Successfully loaded artists CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    if encoding == encodings_to_try[-1]:
                        raise
                    continue

            required_columns = ["Artist", "Genres", "Songs", "Popularity", "Link"]

            if not all(col in self.artists_df.columns for col in required_columns):
                missing = [
                    col
                    for col in required_columns
                    if col not in self.artists_df.columns
                ]
                raise ValueError(f"Artists CSV missing required columns: {missing}")

            print(f"✓ Loaded artists CSV: {len(self.artists_df)} records")

        except Exception as e:
            raise Exception(f"Error loading artists CSV: {str(e)}")

    def load_songs_csv(self, file_path: str) -> None:
        """
        Load the songs CSV file with proper Unicode handling.

        Expected columns: ALink, SName, SLink, Lyric, language

        Args:
            file_path: Path to the songs CSV file
        """
        try:
            encodings_to_try = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]

            for encoding in encodings_to_try:
                try:
                    self.songs_df = pd.read_csv(file_path, encoding=encoding)
                    print(f"✓ Successfully loaded songs CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    if encoding == encodings_to_try[-1]:
                        raise
                    continue

            required_columns = ["ALink", "SName", "SLink", "Lyric", "language"]

            if not all(col in self.songs_df.columns for col in required_columns):
                missing = [
                    col for col in required_columns if col not in self.songs_df.columns
                ]
                raise ValueError(f"Songs CSV missing required columns: {missing}")

            print(f"✓ Loaded songs CSV: {len(self.songs_df)} records")

            if "Lyric" in self.songs_df.columns:
                print("Cleaning lyrics text...")
                self.songs_df["Lyric"] = self.songs_df["Lyric"].apply(clean_lyrics_text)
                print("✓ Lyrics text cleaned")

        except Exception as e:
            raise Exception(f"Error loading songs CSV: {str(e)}")

    def filter_english_songs(self) -> None:
        """Filter songs to include only English language songs."""
        if self.songs_df is None:
            raise ValueError("Songs CSV not loaded")

        initial_count = len(self.songs_df)
        self.songs_df = self.songs_df[self.songs_df["language"] == "en"]
        final_count = len(self.songs_df)

        print(
            f"✓ Filtered for English songs: {final_count} out of {initial_count} songs"
        )

    def merge_data(self) -> None:
        """
        Merge the artists and songs data based on Link and ALink columns.

        Creates a merged dataset with columns: Artist, Genres, Songs, Lyric
        """
        if self.artists_df is None or self.songs_df is None:
            raise ValueError("Both CSV files must be loaded before merging")

        self.merged_df = pd.merge(
            self.artists_df[["Artist", "Genres", "Songs", "Link"]],
            self.songs_df[["ALink", "SName", "Lyric"]],
            left_on="Link",
            right_on="ALink",
            how="inner",
        )

        self.merged_df = self.merged_df[["Artist", "Genres", "Songs", "Lyric"]]

        print(f"✓ Merged data: {len(self.merged_df)} records")

    def save_merged_csv(self, output_path: str) -> None:
        """
        Save the merged data to a CSV file with proper Unicode encoding.

        Args:
            output_path: Path where to save the merged CSV file
        """
        if self.merged_df is None:
            raise ValueError("No merged data to save. Run merge_data() first.")

        try:
            if "Lyric" in self.merged_df.columns:
                print("Final cleaning of lyrics text before saving...")
                self.merged_df["Lyric"] = self.merged_df["Lyric"].apply(
                    clean_lyrics_text
                )

            self.merged_df.to_csv(
                output_path,
                index=False,
                encoding="utf-8",
                quoting=1,
                escapechar="\\",
                lineterminator="\n",
            )
            print(f"✓ Saved merged CSV to: {output_path}")

        except Exception as e:
            raise Exception(f"Error saving merged CSV: {str(e)}")


def main():
    """Main function to run the CSV merger from command line."""
    parser = argparse.ArgumentParser(description="Merge artist and song CSV files")
    parser.add_argument("artists_csv", help="Path to the artists CSV file")
    parser.add_argument("songs_csv", help="Path to the songs CSV file")
    parser.add_argument("output_csv", help="Path for the output merged CSV file")

    args = parser.parse_args()

    if not Path(args.artists_csv).exists():
        print(f"Error: Artists CSV file not found: {args.artists_csv}")
        sys.exit(1)

    if not Path(args.songs_csv).exists():
        print(f"Error: Songs CSV file not found: {args.songs_csv}")
        sys.exit(1)

    try:
        merger = CSVMerger()

        print("Loading CSV files...")
        merger.load_artists_csv(args.artists_csv)
        merger.load_songs_csv(args.songs_csv)

        print("Filtering for English songs...")
        merger.filter_english_songs()

        print("Merging data...")
        merger.merge_data()

        print("Saving merged data...")
        merger.save_merged_csv(args.output_csv)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
