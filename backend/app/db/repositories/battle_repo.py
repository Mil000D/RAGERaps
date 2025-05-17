"""
Repository for battles stored in memory.
"""
from typing import Dict, List, Optional
from uuid import UUID

from app.models.battle import BattleDB, BattleCreate
from app.models.judgment import JudgmentCreate
from app.models.round import Round
from app.models.verse import Verse


class BattleRepository:
    """Repository for managing battles in memory."""

    def __init__(self):
        """Initialize the repository."""
        self.battles: Dict[UUID, BattleDB] = {}

    async def create_battle(self, battle_data: BattleCreate) -> BattleDB:
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
            style=battle_data.style
        )

        self.battles[battle.id] = battle
        return battle

    async def get_battle(self, battle_id: UUID) -> Optional[BattleDB]:
        """
        Get a battle by ID.

        Args:
            battle_id: ID of the battle to retrieve

        Returns:
            Optional[BattleDB]: Battle if found, None otherwise
        """
        return self.battles.get(battle_id)

    async def list_battles(self) -> List[BattleDB]:
        """
        List all battles.

        Returns:
            List[BattleDB]: List of all battles
        """
        return list(self.battles.values())

    async def add_round(self, battle_id: UUID, round_number: int) -> Optional[Round]:
        """
        Add a new round to a battle.

        Args:
            battle_id: ID of the battle
            round_number: Round number

        Returns:
            Optional[Round]: Created round if successful, None otherwise
        """
        battle = await self.get_battle(battle_id)
        if not battle:
            return None

        new_round = Round(
            battle_id=battle_id,
            round_number=round_number
        )

        battle.rounds.append(new_round)
        battle.current_round = round_number

        return new_round

    async def add_verse(self, round_id: UUID, verse: Verse) -> Optional[Verse]:
        """
        Add a verse to a round.

        Args:
            round_id: ID of the round
            verse: Verse to add

        Returns:
            Optional[Verse]: Added verse if successful, None otherwise
        """
        # Find the battle and round
        for battle in self.battles.values():
            for battle_round in battle.rounds:
                if battle_round.id == round_id:
                    # Determine which rapper's verse to update
                    if verse.rapper_name == battle.rapper1_name:
                        battle_round.rapper1_verse = verse
                    elif verse.rapper_name == battle.rapper2_name:
                        battle_round.rapper2_verse = verse
                    else:
                        return None

                    # Update the round status if both verses are present
                    if battle_round.rapper1_verse and battle_round.rapper2_verse:
                        battle_round.status = "completed"

                    return verse

        return None

    async def add_judgment(self, judgment: JudgmentCreate, user_submitted: bool = False) -> bool:
        """
        Add a judgment to a round.

        Args:
            judgment: Judgment to add
            user_submitted: Whether the judgment was submitted by a user

        Returns:
            bool: True if successful, False otherwise
        """
        # Find the battle and round
        for battle in self.battles.values():
            for battle_round in battle.rounds:
                if battle_round.id == judgment.round_id:
                    battle_round.winner = judgment.winner
                    battle_round.judge_feedback = judgment.feedback
                    battle_round.user_judgment = user_submitted

                    # Update the win counts
                    if judgment.winner == battle.rapper1_name:
                        battle.rapper1_wins += 1
                    elif judgment.winner == battle.rapper2_name:
                        battle.rapper2_wins += 1

                    # Check if a rapper has won 2 rounds (Best of 3)
                    if battle.rapper1_wins >= 2:
                        battle.status = "completed"
                        battle.winner = battle.rapper1_name
                    elif battle.rapper2_wins >= 2:
                        battle.status = "completed"
                        battle.winner = battle.rapper2_name
                    # If this is the final round (3) and no one has 2 wins yet
                    elif battle_round.round_number == 3:
                        battle.status = "completed"

                        # Determine the overall winner
                        if battle.rapper1_wins > battle.rapper2_wins:
                            battle.winner = battle.rapper1_name
                        elif battle.rapper2_wins > battle.rapper1_wins:
                            battle.winner = battle.rapper2_name
                        # In case of a tie after 3 rounds (should be rare)
                        else:
                            # Use the winner of the last round as the tiebreaker
                            battle.winner = judgment.winner

                    return True

        return False


# Create a repository instance
battle_repository = BattleRepository()
