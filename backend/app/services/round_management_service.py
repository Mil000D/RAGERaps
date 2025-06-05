"""
Service for managing rounds in rap battles.
"""

import logging
from typing import Dict, List
from uuid import UUID

from app.db.repositories.battle_repo import battle_repository
from app.models.battle import BattleResponse
from app.models.round import Round
from app.models.verse import Verse

logger = logging.getLogger(__name__)


class RoundManagementService:
    """Service responsible for managing battle rounds."""

    def __init__(self):
        self.repository = battle_repository

    def get_previous_verses(
        self, battle: BattleResponse, round_number: int
    ) -> List[Dict[str, str]]:
        """
        Get verses from previous rounds for context.

        Args:
            battle: Battle object
            round_number: Current round number

        Returns:
            List[Dict[str, str]]: List of previous verses
        """
        previous_verses = []

        for round_obj in battle.rounds:
            if round_obj.round_number < round_number:
                if round_obj.rapper1_verse:
                    previous_verses.append(
                        {
                            "rapper_name": battle.rapper1_name,
                            "content": round_obj.rapper1_verse.content,
                        }
                    )
                if round_obj.rapper2_verse:
                    previous_verses.append(
                        {
                            "rapper_name": battle.rapper2_name,
                            "content": round_obj.rapper2_verse.content,
                        }
                    )

        return previous_verses

    def create_round(self, battle_id: UUID, round_number: int) -> Round:
        """
        Create a new round for a battle.

        Args:
            battle_id: UUID of the battle
            round_number: Number of the round (1-3)

        Returns:
            Round: Created round object

        Raises:
            ValueError: If round number is invalid
            Exception: If round creation fails
        """
        if round_number < 1 or round_number > 3:
            raise ValueError(f"Invalid round number: {round_number}. Must be 1-3.")

        try:
            logger.info(f"Creating round {round_number} for battle {battle_id}")

            round_obj = Round(
                battle_id=battle_id,
                round_number=round_number,
            )

            created_round = self.repository.add_round_to_battle(battle_id, round_obj)
            logger.info(
                f"Successfully created round {round_number} with ID: {created_round.id}"
            )

            return created_round
        except Exception as e:
            logger.error(
                f"Failed to create round {round_number} for battle {battle_id}: {str(e)}"
            )
            raise

    def add_verses_to_round(
        self,
        battle_id: UUID,
        round_id: UUID,
        rapper1_verse: Verse,
        rapper2_verse: Verse,
    ) -> Round:
        """
        Add verses to a round.

        Args:
            battle_id: UUID of the battle
            round_id: UUID of the round
            rapper1_verse: Verse from first rapper
            rapper2_verse: Verse from second rapper

        Returns:
            Round: Updated round with verses

        Raises:
            Exception: If adding verses fails
        """
        try:
            logger.info(f"Adding verses to round {round_id}")

            updated_round = self.repository.add_verses_to_round(
                battle_id, round_id, rapper1_verse, rapper2_verse
            )

            logger.info(f"Successfully added verses to round {round_id}")
            return updated_round
        except Exception as e:
            logger.error(f"Failed to add verses to round {round_id}: {str(e)}")
            raise

    def is_battle_complete(self, battle: BattleResponse) -> bool:
        """
        Check if a battle is complete.

        Args:
            battle: Battle object

        Returns:
            bool: True if battle is complete
        """
        # Battle is complete if someone has won 2 rounds (best of 3)
        if battle.rapper1_wins >= 2 or battle.rapper2_wins >= 2:
            return True

        # Battle is also complete if all 3 rounds are finished (final tiebreaker)
        completed_rounds = sum(1 for r in battle.rounds if r.status == "completed")
        if completed_rounds >= 3:
            return True
            
        return False


# Create singleton instance
round_management_service = RoundManagementService()
