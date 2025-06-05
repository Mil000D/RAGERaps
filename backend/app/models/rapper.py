"""
Rapper model definitions.
"""

from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RapperInfo(BaseModel):
    """Model for rapper information."""

    id: UUID = Field(default_factory=uuid4, description="Unique rapper ID")
    name: str = Field(..., description="Rapper name")
    bio: Optional[str] = Field(default=None, description="Rapper biography")
    facts: List[str] = Field(default_factory=list, description="Facts about the rapper")
    style: Optional[str] = Field(default=None, description="Rapper's style")
    metadata: Dict[str, str] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        """Pydantic model configuration."""

        from_attributes = True
