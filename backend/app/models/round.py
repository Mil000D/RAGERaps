"""
Round model definitions.
"""

from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.verse import Verse


class Round(BaseModel):
    """
    Model for a battle round.

    Represents a single round in a rap battle, containing verses from both rappers.
    """

    id: UUID = Field(
        default_factory=uuid4, description="Unique round ID - automatically generated"
    )
    battle_id: UUID = Field(
        ...,
        description="ID of the battle this round belongs to - must be a valid UUID of an existing battle",
    )
    round_number: int = Field(
        ...,
        description="Round number - typically 1, 2, or 3",
        ge=1,
        le=3,
        examples=[1, 2, 3],
    )
    rapper1_verse: Optional[Verse] = Field(
        default=None,
        description="First rapper's verse - contains the lyrics and metadata",
    )
    rapper2_verse: Optional[Verse] = Field(
        default=None,
        description="Second rapper's verse - contains the lyrics and metadata",
    )
    winner: Optional[str] = Field(
        default=None,
        description="Winner of the round - name of the rapper who won",
        examples=["Kendrick Lamar", "Drake"],
    )
    user_judgment: Optional[bool] = Field(
        default=None,
        description="Whether user judged this round - True if judged by user, False if by AI",
    )
    status: str = Field(
        default="in_progress",
        description="Round status - can be 'in_progress' or 'completed'",
        examples=["in_progress", "completed"],
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Judgment feedback explaining the decision - provided by AI or user",
        examples=[
            "Great flow and wordplay from rapper 1",
            "Rapper 2 had better delivery",
        ],
    )
