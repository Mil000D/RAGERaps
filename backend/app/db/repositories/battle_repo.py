"""
Repository for battles stored in memory.
"""

from typing import Dict, List, Optional
from uuid import UUID

from app.db.interfaces import IBattleRepository
from app.models.battle import BattleDB, BattleCreate
from app.models.round import Round
from app.models.verse import Verse


class InMemoryBattleRepository(IBattleRepository):
    """Repository for managing battles in memory."""

    def __init__(self):
        """Initialize the repository."""
        self.battles: Dict[UUID, BattleDB] = {}

    def create_battle(self, battle_data: BattleCreate) -> BattleDB:
        """
        Create a new battle.

        Args:
            battle_data: Battle creation data

        Returns:
            BattleDB: Created battle
        """
        battle = BattleDB(
            rapper1_name=battle_data.rapper1_name,
            rapper2_name=battle_data.rapper2_name,
            style1=battle_data.style1,
            style2=battle_data.style2,
        )

        self.battles[battle.id] = battle
        return battle

    def get_battle(self, battle_id: UUID) -> Optional[BattleDB]:
        """
        Get a battle by ID.

        Args:
            battle_id: ID of the battle to retrieve

        Returns:
            Optional[BattleDB]: Battle if found, None otherwise
        """
        return self.battles.get(battle_id)

    def list_battles(self) -> List[BattleDB]:
        """
        List all battles.

        Returns:
            List[BattleDB]: List of all battles
        """
        return list(self.battles.values())

    def update_battle(self, battle: BattleDB) -> BattleDB:
        """
        Update an existing battle.

        Args:
            battle: Battle to update

        Returns:
            BattleDB: Updated battle

        Raises:
            ValueError: If battle does not exist
        """
        if battle.id not in self.battles:
            raise ValueError(f"Battle with ID {battle.id} does not exist")

        self.battles[battle.id] = battle
        return battle

    def add_round_to_battle(self, battle_id: UUID, round_obj: Round) -> Round:
        """
        Add a round to a battle.

        Args:
            battle_id: ID of the battle
            round_obj: Round to add

        Returns:
            Round: Added round

        Raises:
            ValueError: If battle does not exist
        """
        battle = self.battles.get(battle_id)
        if not battle:
            raise ValueError(f"Battle with ID {battle_id} does not exist")

        battle.rounds.append(round_obj)
        battle.current_round = round_obj.round_number
        return round_obj

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
            battle_id: ID of the battle
            round_id: ID of the round
            rapper1_verse: Verse from rapper 1
            rapper2_verse: Verse from rapper 2

        Returns:
            Round: Updated round

        Raises:
            ValueError: If battle or round does not exist
        """
        battle = self.battles.get(battle_id)
        if not battle:
            raise ValueError(f"Battle with ID {battle_id} does not exist")

        for battle_round in battle.rounds:
            if battle_round.id == round_id:
                battle_round.rapper1_verse = rapper1_verse
                battle_round.rapper2_verse = rapper2_verse

                return battle_round

        raise ValueError(
            f"Round with ID {round_id} does not exist in battle {battle_id}"
        )


battle_repository = InMemoryBattleRepository()
