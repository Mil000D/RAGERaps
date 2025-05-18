"""
Battle-related endpoints for the RAGERaps API.

These endpoints allow you to create and manage rap battles with a simplified "Best of 3" format.
Battles can be generated with verses only, allowing the user to choose between AI judgment
or manually selecting a winner. A rapper wins after winning 2 rounds.
"""
from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, Path, status

from app.models.battle import BattleCreate, BattleResponse
from app.models.judgment import JudgmentCreate
from app.services.battle_service import battle_service

router = APIRouter(prefix="/battles", tags=["battles"])


@router.post(
    "/with-verses",
    response_model=BattleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a battle with verses only",
    response_description="The battle with verses for both rappers but without judgment"
)
async def generate_battle_with_verses(
    battle_data: BattleCreate = Body(
        ...,
        examples=[
            {
                "style1": "Conscious Rap",
                "style2": "Trap",
                "rapper1_name": "Kendrick Lamar",
                "rapper2_name": "Drake"
            },
            {
                "style1": "Old School",
                "style2": "Mumble Rap",
                "rapper1_name": "Jay-Z",
                "rapper2_name": "Future"
            }
        ]
    )
):
    """
    Generate a battle with verses for both rappers but without automatic judgment.

    This endpoint creates a battle and generates verses for both rappers in the first round,
    but does not automatically judge the round. This allows the user to choose between
    AI judgment or manually selecting a winner.

    The battle generation process:
    1. Creates a new battle with the specified rappers and style
    2. Generates verses for both rappers in the first round
    3. Returns the battle without judging the round

    After receiving the response, the client can:
    - Send a request to the `/battles/{battle_id}/rounds/{round_id}/judge` endpoint to use AI judgment
    - Send a request to the `/battles/{battle_id}/rounds/{round_id}/user-judge` endpoint to manually select a winner

    - **style1**: The rap style for the first rapper (e.g., "Conscious Rap", "Old School")
    - **style2**: The rap style for the second rapper (e.g., "Trap", "Mumble Rap")
    - **rapper1_name**: Name of the first rapper
    - **rapper2_name**: Name of the second rapper

    This operation may take some time to complete as it involves multiple AI operations.
    """
    try:
        return await battle_service.generate_battle_with_verses(battle_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating battle: {str(e)}"
        )

@router.get(
    "",
    response_model=List[BattleResponse],
    status_code=status.HTTP_200_OK,
    summary="List all rap battles",
    response_description="List of all battles in the system"
)
async def list_battles():
    """
    List all rap battles in the system.

    Returns a list of all battles, including their current state, rounds, and verses.
    Battles are ordered from newest to oldest.
    """
    return await battle_service.list_battles()


@router.get(
    "/{battle_id}",
    response_model=BattleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific rap battle",
    response_description="Detailed information about the requested battle"
)
async def get_battle(
    battle_id: UUID = Path(
        ...,
        description="The ID of the battle to retrieve",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6"
    )
):
    """
    Get detailed information about a specific rap battle.

    Returns all information about the battle, including:
    - Battle metadata (styles for each rapper, rapper names, status)
    - All rounds and their status
    - All verses generated so far
    - Judgments for completed rounds

    If the battle is not found, returns a 404 error.
    """
    battle = await battle_service.get_battle(battle_id)
    if not battle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battle with ID {battle_id} not found"
        )

    return battle


@router.post(
    "/{battle_id}/rounds/{round_id}/judge",
    response_model=BattleResponse,
    status_code=status.HTTP_200_OK,
    summary="Judge a round using AI",
    response_description="The updated battle with the AI judgment"
)
async def judge_round_ai(
    battle_id: UUID = Path(
        ...,
        description="The ID of the battle",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6"
    ),
    round_id: UUID = Path(
        ...,
        description="The ID of the round to judge",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6"
    )
):
    """
    Judge a round of the battle using AI.

    This endpoint triggers the AI judge to evaluate both verses and determine a winner.
    The judgment includes detailed feedback explaining the decision.

    After judging:
    1. The round is marked as completed with the winner and feedback
    2. The rapper's win count is updated
    3. If a rapper has won 2 rounds, they are declared the overall winner
    4. If the battle isn't over, a new round is automatically created with verses for both rappers
    5. The updated battle state is returned

    Requirements:
    - Both rappers must have verses in the round
    - The round must not already have a judgment

    This operation may take some time to complete as it involves complex AI analysis.
    """
    success, battle = await battle_service.judge_round(battle_id, round_id)
    if not success or not battle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not judge round. Make sure both rappers have verses in this round."
        )

    return battle


@router.post(
    "/{battle_id}/rounds/{round_id}/user-judge",
    response_model=BattleResponse,
    status_code=status.HTTP_200_OK,
    summary="Judge a round manually",
    response_description="The updated battle with the user judgment"
)
async def judge_round_user(
    judgment: JudgmentCreate = Body(
        ...,
        examples=[
            {
                "round_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "winner": "Kendrick Lamar",
                "feedback": "Kendrick's verse had better flow and more creative wordplay."
            }
        ]
    ),
    battle_id: UUID = Path(
        ...,
        description="The ID of the battle",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6"
    ),
    round_id: UUID = Path(
        ...,
        description="The ID of the round to judge",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6"
    )
):
    """
    Manually judge a round of the battle.

    This endpoint allows you to submit a judgment for a round, specifying the winner
    and optional feedback. The judgment is recorded as user-submitted.

    After judging:
    1. The round is marked as completed with the winner and feedback
    2. The rapper's win count is updated
    3. If a rapper has won 2 rounds, they are declared the overall winner
    4. If the battle isn't over, a new round is automatically created with verses for both rappers
    5. The updated battle state is returned

    Requirements:
    - Both rappers must have verses in the round
    - The round must not already have a judgment
    - The winner must be one of the two rappers in the battle
    """
    # Ensure the round_id in the path matches the round_id in the judgment
    if judgment.round_id != round_id:
        judgment.round_id = round_id

    success, battle = await battle_service.judge_round(battle_id, round_id, judgment)
    if not success or not battle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not judge round. Make sure both rappers have verses in this round."
        )

    return battle
