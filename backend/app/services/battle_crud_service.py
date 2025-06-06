"""
Service for basic CRUD operations on battles.
"""

import logging
from typing import List, Optional
from uuid import UUID

from app.db.repositories.battle_repo import battle_repository
from app.models.battle import BattleCreate, BattleResponse

logger = logging.getLogger(__name__)


class BattleCrudService:
    """Service responsible for basic battle CRUD operations."""

    def __init__(self):
        self.repository = battle_repository

    def create_battle(self, battle_data: BattleCreate) -> BattleResponse:
        """
        Create a new battle.

        Args:
            battle_data: Battle creation data

        Returns:
            BattleResponse: Created battle

        Raises:
            Exception: If battle creation fails
        """
        try:
            logger.info(
                f"Creating battle between {battle_data.rapper1_name} and {battle_data.rapper2_name}"
            )

            battle = self.repository.create_battle(battle_data)
            logger.info(f"Successfully created battle with ID: {battle.id}")

            return battle
        except Exception as e:
            logger.error(f"Failed to create battle: {str(e)}")
            raise

    def get_battle(self, battle_id: UUID) -> Optional[BattleResponse]:
        """
        Get a battle by ID.

        Args:
            battle_id: UUID of the battle

        Returns:
            Optional[BattleResponse]: Battle if found, None otherwise
        """
        try:
            battle = self.repository.get_battle(battle_id)
            if not battle:
                logger.warning(f"Battle not found: {battle_id}")
            return battle
        except Exception as e:
            logger.error(f"Failed to get battle {battle_id}: {str(e)}")
            raise

    def list_battles(self) -> List[BattleResponse]:
        """
        List all battles.

        Returns:
            List[BattleResponse]: List of all battles
        """
        try:
            battles = self.repository.list_battles()
            logger.info(f"Retrieved {len(battles)} battles")
            return battles
        except Exception as e:
            logger.error(f"Failed to list battles: {str(e)}")
            raise

    def update_battle_winner(
        self, battle_id: UUID, winner: str
    ) -> Optional[BattleResponse]:
        """
        Update battle winner.

        Args:
            battle_id: UUID of the battle
            winner: Winner name

        Returns:
            Optional[BattleResponse]: Updated battle if successful, None otherwise
        """
        try:
            battle = self.repository.get_battle(battle_id)
            if not battle:
                logger.warning(f"Battle not found for winner update: {battle_id}")
                return None

            battle.winner = winner
            battle.status = "completed"
            updated_battle = self.repository.update_battle(battle)
            logger.info(f"Set battle {battle_id} winner to {winner}")

            return updated_battle
        except Exception as e:
            logger.error(f"Failed to update battle {battle_id} winner: {str(e)}")
            raise


battle_crud_service = BattleCrudService()
