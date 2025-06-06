"""
Repository interfaces for dependency inversion.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.models.battle import BattleCreate, BattleDB
from app.models.round import Round
from app.models.verse import Verse


class IBattleRepository(ABC):
    """Interface for battle repository operations."""

    @abstractmethod
    def create_battle(self, battle_data: BattleCreate) -> BattleDB:
        """Create a new battle."""
        pass

    @abstractmethod
    def get_battle(self, battle_id: UUID) -> Optional[BattleDB]:
        """Get a battle by ID."""
        pass

    @abstractmethod
    def list_battles(self) -> List[BattleDB]:
        """List all battles."""
        pass

    @abstractmethod
    def update_battle(self, battle: BattleDB) -> BattleDB:
        """Update an existing battle."""
        pass

    @abstractmethod
    def add_round_to_battle(self, battle_id: UUID, round_obj: Round) -> Round:
        """Add a round to a battle."""
        pass

    @abstractmethod
    def add_verses_to_round(
        self,
        battle_id: UUID,
        round_id: UUID,
        rapper1_verse: Verse,
        rapper2_verse: Verse,
    ) -> Round:
        """Add verses to a round."""
        pass
