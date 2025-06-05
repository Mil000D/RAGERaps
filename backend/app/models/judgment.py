"""
Judgment model definitions.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JudgmentBase(BaseModel):
    """
    Base model for judgment data.

    Contains the essential fields required for a judgment.
    """

    round_id: UUID = Field(
        ...,
        description="ID of the round being judged - must be a valid UUID of an existing round",
    )
    winner: str = Field(
        ...,
        description="Name of the winner - must match one of the rapper names in the battle",
        examples=["Kendrick Lamar", "Drake"],
    )


class JudgmentCreate(JudgmentBase):
    """
    Model for creating a new judgment.

    Used when submitting a judgment for a round.
    """

    feedback: Optional[str] = Field(
        default=None,
        description="Feedback on the judgment - explains why the winner was chosen",
        examples=["Kendrick's verse had better flow and more creative wordplay."],
    )
