"""
Battle model definitions.
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.round import Round


def utc_now():
    """Get current UTC time with timezone information."""
    return datetime.now(timezone.utc)


class BattleBase(BaseModel):
    """Base model for battle data."""

    style: str = Field(
        ...,
        description="The rap battle style",
        examples=["Old School", "Gangsta Rap", "Trap", "Conscious Rap", "Boom Bap"]
    )


class BattleCreate(BattleBase):
    """
    Model for creating a new battle.

    This model is used when creating a new rap battle between two rappers.
    """

    rapper1_name: str = Field(
        ...,
        description="Name of the first rapper",
        examples=["Kendrick Lamar", "Jay-Z", "Eminem"]
    )
    rapper2_name: str = Field(
        ...,
        description="Name of the second rapper",
        examples=["Drake", "Snoop Dogg", "Nas"]
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "style": "Old School",
                "rapper1_name": "Kendrick Lamar",
                "rapper2_name": "Drake"
            }
        }
    }


class BattleDB(BattleBase):
    """
    Model for battle data stored in the database.

    This model represents the complete battle data as stored in the database,
    including generated fields like ID and timestamps.
    """

    id: UUID = Field(
        default_factory=uuid4,
        description="Unique battle ID"
    )
    rapper1_name: str = Field(
        ...,
        description="Name of the first rapper"
    )
    rapper2_name: str = Field(
        ...,
        description="Name of the second rapper"
    )
    rounds: List[Round] = Field(
        default_factory=list,
        description="Battle rounds - contains all rounds in the battle"
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Creation timestamp - when the battle was created"
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        description="Last update timestamp - when the battle was last updated"
    )
    status: str = Field(
        default="in_progress",
        description="Battle status - can be 'in_progress' or 'completed'",
        examples=["in_progress", "completed"]
    )
    current_round: int = Field(
        default=1,
        description="Current round number - starts at 1 and goes up to 3",
        ge=1,
        le=3
    )
    rapper1_wins: int = Field(
        default=0,
        description="Number of rounds won by the first rapper",
        ge=0,
        le=3
    )
    rapper2_wins: int = Field(
        default=0,
        description="Number of rounds won by the second rapper",
        ge=0,
        le=3
    )
    winner: Optional[str] = Field(
        default=None,
        description="Winner of the battle - set when a rapper wins 2 rounds or after all 3 rounds are completed"
    )


class BattleResponse(BattleDB):
    """
    Model for battle response data.

    This model is used when returning battle data to the client.
    It includes all fields from BattleDB and is configured to work with ORM models.
    """

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "style": "Old School",
                "rapper1_name": "Kendrick Lamar",
                "rapper2_name": "Drake",
                "rounds": [],
                "created_at": "2023-01-01T00:00:00.000Z",
                "updated_at": "2023-01-01T00:00:00.000Z",
                "status": "in_progress",
                "current_round": 1,
                "rapper1_wins": 0,
                "rapper2_wins": 0,
                "winner": None
            }
        }
    }
