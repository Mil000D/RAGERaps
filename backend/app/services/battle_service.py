"""
Service for managing rap battles.

This is a facade service that delegates to the new focused services.
Maintained for backward compatibility.
"""

import logging
from typing import List, Optional
from uuid import UUID

from app.models.battle import BattleCreate, BattleResponse
from app.models.judgment import JudgmentCreate
from app.services.battle_crud_service import battle_crud_service
from app.services.battle_orchestration_service import battle_orchestration_service
from app.services.judgment_service import judgment_service
from app.services.round_management_service import round_management_service

logger = logging.getLogger(__name__)


def get_previous_verses(battle, round_number):
    """
    Get verses from previous rounds.

    Deprecated: Use round_management_service.get_previous_verses() instead.
    """
    return round_management_service.get_previous_verses(battle, round_number)


def judge_round_ai(battle, current_round):
    """
    Use AI to judge a battle round.

    Deprecated: Use judgment_service.judge_round_ai() instead.
    """
    return judgment_service.judge_round_ai(battle, current_round)


class BattleService:
    """
    Main battle service that orchestrates battle operations.

    This is a facade that delegates to focused services for better maintainability.
    """

    def __init__(self):
        self.crud_service = battle_crud_service
        self.orchestration_service = battle_orchestration_service
        self.judgment_service = judgment_service

    def create_battle(self, battle_data: BattleCreate) -> BattleResponse:
        """
        Create a new battle.

        Args:
            battle_data: Battle creation data

        Returns:
            BattleResponse: Created battle
        """
        return self.crud_service.create_battle(battle_data)

    async def generate_complete_battle(
        self, battle_data: BattleCreate
    ) -> BattleResponse:
        """
        Generate a complete battle with all 3 rounds and verses.

        Args:
            battle_data: Battle creation data

        Returns:
            BattleResponse: Complete battle with all rounds
        """
        return await self.orchestration_service.generate_complete_battle(battle_data)

    async def generate_battle_with_verses(
        self, battle_data: BattleCreate
    ) -> BattleResponse:
        """
        Generate a battle with verses for the first round only.

        Args:
            battle_data: Battle creation data

        Returns:
            BattleResponse: Battle with first round verses
        """
        return await self.orchestration_service.generate_battle_with_verses(battle_data)

    def get_battle(self, battle_id: UUID) -> Optional[BattleResponse]:
        """
        Get a battle by ID.

        Args:
            battle_id: UUID of the battle

        Returns:
            Optional[BattleResponse]: Battle if found, None otherwise
        """
        return self.crud_service.get_battle(battle_id)

    def list_battles(self) -> List[BattleResponse]:
        """
        List all battles.

        Returns:
            List[BattleResponse]: List of all battles
        """
        return self.crud_service.list_battles()

    async def judge_round(
        self,
        battle_id: UUID,
        round_id: UUID,
        user_judgment: Optional[JudgmentCreate] = None,
    ) -> Optional[BattleResponse]:
        """
        Judge a round and update the battle accordingly.

        Args:
            battle_id: UUID of the battle
            round_id: UUID of the round
            user_judgment: Optional user judgment (if None, uses AI)

        Returns:
            Optional[BattleResponse]: Updated battle
        """
        return await self.orchestration_service.judge_round(
            battle_id, round_id, user_judgment
        )


battle_service = BattleService()
