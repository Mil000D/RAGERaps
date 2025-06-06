"""
Common utility functions used across the application.
"""

import re
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Get current UTC time with timezone information."""
    return datetime.now(timezone.utc)


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
