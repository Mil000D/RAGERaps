"""
Judgment model definitions.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def utc_now():
    """Get current UTC time with timezone information."""
    return datetime.now(timezone.utc)


class JudgmentBase(BaseModel):
    """
    Base model for judgment data.

    Contains the essential fields required for a judgment.
    """

    round_id: UUID = Field(
        ...,
        description="ID of the round being judged - must be a valid UUID of an existing round"
    )
    winner: str = Field(
        ...,
        description="Name of the winner - must match one of the rapper names in the battle",
        examples=["Kendrick Lamar", "Drake"]
    )


class JudgmentCreate(JudgmentBase):
    """
    Model for creating a new judgment.

    Used when submitting a judgment for a round.
    """

    feedback: Optional[str] = Field(
        default=None,
        description="Feedback on the judgment - explains why the winner was chosen",
        examples=["Kendrick's verse had better flow and more creative wordplay."]
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "round_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "winner": "Kendrick Lamar",
                "feedback": "Kendrick's verse had better flow and more creative wordplay."
            }
        }
    }


class JudgmentDB(JudgmentBase):
    """
    Model for judgment data stored in the database.

    Includes additional fields that are generated when storing the judgment.
    """

    id: UUID = Field(
        default_factory=uuid4,
        description="Unique judgment ID - automatically generated"
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Creation timestamp - when the judgment was created"
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Feedback on the judgment - explains why the winner was chosen"
    )
    user_submitted: bool = Field(
        default=False,
        description="Whether the judgment was submitted by a user or generated automatically"
    )


class JudgmentResponse(JudgmentDB):
    """
    Model for judgment response data.

    Used when returning judgment data to the client.
    """

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "round_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "winner": "Kendrick Lamar",
                "created_at": "2023-01-01T00:00:00.000Z",
                "feedback": "Kendrick's verse had better flow and more creative wordplay.",
                "user_submitted": True
            }
        }
    }


