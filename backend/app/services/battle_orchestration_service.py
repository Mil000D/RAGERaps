"""
Service for orchestrating complex battle workflows.
"""

import logging
from typing import Dict, Optional
from uuid import UUID

from app.models.battle import BattleCreate, BattleResponse
from app.models.judgment import JudgmentCreate
from app.services.battle_crud_service import battle_crud_service
from app.services.judgment_service import judgment_service
from app.services.round_management_service import round_management_service
from app.services.verse_generation_service import verse_generation_service

logger = logging.getLogger(__name__)


class BattleOrchestrationService:
    """Service responsible for orchestrating complex battle workflows."""

    def __init__(self):
        self.crud_service = battle_crud_service
        self.verse_service = verse_generation_service
        self.round_service = round_management_service
        self.judgment_service = judgment_service

    async def generate_complete_battle(
        self, battle_data: BattleCreate
    ) -> BattleResponse:
        """
        Generate a complete battle with all 3 rounds and verses.

        Args:
            battle_data: Battle creation data

        Returns:
            BattleResponse: Complete battle with all rounds

        Raises:
            Exception: If battle generation fails
        """
        try:
            logger.info(
                f"Starting complete battle generation: {battle_data.rapper1_name} vs {battle_data.rapper2_name}"
            )

            # Create the battle
            battle = self.crud_service.create_battle(battle_data)

            # Generate all 3 rounds
            for round_number in range(1, 4):
                await self._generate_battle_round(battle, round_number)

                # Check if battle is complete (someone won 2 rounds)
                if self.round_service.is_battle_complete(battle):
                    break

            # Finalize battle
            battle_winner = self.judgment_service.determine_battle_winner(battle)
            if battle_winner:
                battle = self.crud_service.update_battle_winner(
                    battle.id, battle_winner
                )

            logger.info(f"Complete battle generated successfully: {battle.id}")
            return battle

        except Exception as e:
            logger.error(f"Failed to generate complete battle: {str(e)}")
            raise

    async def generate_battle_with_verses(
        self, battle_data: BattleCreate
    ) -> BattleResponse:
        """
        Generate a battle with verses for the first round only.

        Args:
            battle_data: Battle creation data

        Returns:
            BattleResponse: Battle with first round verses

        Raises:
            Exception: If battle generation fails
        """
        try:
            logger.info(
                f"Generating battle with first round verses: {battle_data.rapper1_name} vs {battle_data.rapper2_name}"
            )

            # Create the battle
            battle = self.crud_service.create_battle(battle_data)

            # Generate first round
            await self._generate_battle_round(battle, 1)

            logger.info(f"Battle with first round generated successfully: {battle.id}")
            return battle

        except Exception as e:
            logger.error(f"Failed to generate battle with verses: {str(e)}")
            raise

    async def continue_battle_to_next_round(
        self, battle_id: UUID
    ) -> Optional[BattleResponse]:
        """
        Continue a battle to the next round with verse generation.

        Args:
            battle_id: UUID of the battle

        Returns:
            Optional[BattleResponse]: Updated battle or None if battle is complete

        Raises:
            Exception: If continuation fails
        """
        try:
            battle = self.crud_service.get_battle(battle_id)
            if not battle:
                raise ValueError(f"Battle not found: {battle_id}")

            if self.round_service.is_battle_complete(battle):
                logger.info(f"Battle {battle_id} is already complete")
                return battle

            # Advance to next round
            next_round = battle.current_round + 1
            if next_round > 3:
                logger.info(f"Battle {battle_id} has reached maximum rounds")
                return battle

            # Generate next round
            await self._generate_battle_round(battle, next_round)

            # Check for completion
            if self.round_service.is_battle_complete(battle):
                battle_winner = self.judgment_service.determine_battle_winner(battle)
                if battle_winner:
                    battle = self.crud_service.update_battle_winner(
                        battle.id, battle_winner
                    )

            logger.info(f"Battle {battle_id} continued to round {next_round}")
            return battle

        except Exception as e:
            logger.error(f"Failed to continue battle {battle_id}: {str(e)}")
            raise

    async def judge_round(
        self,
        battle_id: UUID,
        round_id: UUID,
        user_judgment: Optional[JudgmentCreate] = None,
    ) -> Optional[BattleResponse]:
        """
        Judge a round (either by AI or user) and potentially continue to next round.

        Args:
            battle_id: UUID of the battle
            round_id: UUID of the round
            user_judgment: Optional user judgment (if None, uses AI)

        Returns:
            Optional[BattleResponse]: Updated battle

        Raises:
            Exception: If judging fails
        """
        try:
            logger.info(f"Judging round {round_id} in battle {battle_id}")

            # Judge the round
            use_ai = user_judgment is None
            battle = await self.judgment_service.judge_round_and_update_battle(
                battle_id, round_id, use_ai, user_judgment
            )

            if not battle:
                return None

            # If battle is not complete and we haven't reached the max rounds, generate next round
            if (
                not self.round_service.is_battle_complete(battle)
                and len(battle.rounds) < 3
            ):
                await self.continue_battle_to_next_round(battle_id)
                # Refresh battle data
                battle = self.crud_service.get_battle(battle_id)

            logger.info(f"Round {round_id} judged successfully")
            return battle

        except Exception as e:
            logger.error(f"Failed to judge round {round_id}: {str(e)}")
            raise

    async def _generate_battle_round(
        self,
        battle: BattleResponse,
        round_number: int,
    ) -> None:
        """
        Generate a complete battle round with verses.

        Args:
            battle: Battle object
            round_number: Round number to generate

        Raises:
            Exception: If round generation fails
        """
        try:
            logger.info(f"Generating round {round_number} for battle {battle.id}")

            # Create the round
            round_obj = self.round_service.create_round(battle.id, round_number)

            # Get previous verses for context
            previous_verses = self.round_service.get_previous_verses(
                battle, round_number
            )

            # Generate verses
            (
                rapper1_verse,
                rapper2_verse,
            ) = await self.verse_service.generate_verses_for_round(
                battle, round_obj, previous_verses
            )

            if not rapper1_verse or not rapper2_verse:
                raise Exception(f"Failed to generate verses for round {round_number}")

            # Add verses to round
            self.round_service.add_verses_to_round(
                battle.id, round_obj.id, rapper1_verse, rapper2_verse
            )

            # Update battle current round
            battle.current_round = round_number

            logger.info(f"Successfully generated round {round_number}")

        except Exception as e:
            logger.error(f"Failed to generate round {round_number}: {str(e)}")
            raise



# Create singleton instance
battle_orchestration_service = BattleOrchestrationService()
