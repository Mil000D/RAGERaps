"""
Round model definitions.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.verse import Verse


def utc_now():
    """Get current UTC time with timezone information."""
    return datetime.now(timezone.utc)


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
    judge_feedback: Optional[str] = Field(
        default=None,
        description="Feedback from the judge - explanation of the judgment",
    )
    user_judgment: Optional[bool] = Field(
        default=None,
        description="Whether user judged this round - True if judged by user, False if by AI",
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Creation timestamp - when the round was created",
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        description="Last update timestamp - when the round was last updated",
    )
    status: str = Field(
        default="in_progress",
        description="Round status - can be 'in_progress' or 'completed'",
        examples=["in_progress", "completed"],
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "battle_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "round_number": 1,
                "rapper1_verse": None,
                "rapper2_verse": None,
                "winner": None,
                "judge_feedback": None,
                "user_judgment": None,
                "created_at": "2023-01-01T00:00:00.000Z",
                "updated_at": "2023-01-01T00:00:00.000Z",
                "status": "in_progress",
            }
        },
    }
