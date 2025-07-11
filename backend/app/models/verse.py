"""
Verse model definitions.
"""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Verse(BaseModel):
    """
    Model for a rap verse.

    Represents a verse generated by a rapper in a battle round.
    """

    id: UUID = Field(
        default_factory=uuid4, description="Unique verse ID - automatically generated"
    )
    round_id: UUID = Field(
        ...,
        description="ID of the round this verse belongs to - must be a valid UUID of an existing round",
    )
    rapper_name: str = Field(
        ...,
        description="Name of the rapper who created this verse",
        examples=["Kendrick Lamar", "Drake"],
    )
    content: str = Field(
        ...,
        description="Verse content - the actual rap lyrics",
        examples=[
            "I flow like water, you're just a drought\nMy rhymes hit harder, no doubt\nWhile you're stuck in the past, I innovate\nYour tired flow is something I can't tolerate"
        ],
    )
