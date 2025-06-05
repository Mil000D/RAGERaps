"""
Service for judging rap battle rounds.
"""

import logging
import random
from typing import Optional, Tuple
from uuid import UUID

from app.agents.judge_agent import judge_agent
from app.db.repositories.battle_repo import battle_repository
from app.models.battle import BattleResponse
from app.models.judgment import JudgmentCreate
from app.models.round import Round

logger = logging.getLogger(__name__)


class JudgmentService:
    """Service responsible for judging battle rounds."""

    def __init__(self):
        self.repository = battle_repository

    async def judge_round_ai(
        self, battle: BattleResponse, current_round: Round
    ) -> Tuple[str, str]:
        """
        Use AI to judge a battle round.

        Args:
            battle: Battle object
            current_round: Round to judge

        Returns:
            Tuple[str, str]: (winner_name, feedback)
        """
        try:
            logger.info(
                f"AI judging round {current_round.round_number} of battle {battle.id}"
            )

            if not current_round.rapper1_verse or not current_round.rapper2_verse:
                raise ValueError("Cannot judge round without both verses")

            # Use the judge agent to evaluate the round
            winner, feedback = await judge_agent.judge_round(
                rapper1_name=battle.rapper1_name,
                rapper1_verse=current_round.rapper1_verse.content,
                rapper1_style=battle.style1,
                rapper2_name=battle.rapper2_name,
                rapper2_verse=current_round.rapper2_verse.content,
                rapper2_style=battle.style2,
            )

            # Validate winner
            if winner not in [battle.rapper1_name, battle.rapper2_name]:
                logger.warning(f"Invalid winner from AI: {winner}, using fallback")
                return self._fallback_judgment(battle)

            logger.info(
                f"AI judged round {current_round.round_number}: winner is {winner}"
            )
            return winner, feedback

        except Exception as e:
            logger.error(
                f"AI judging failed for round {current_round.round_number}: {str(e)}"
            )
            return self._fallback_judgment(battle)

    def _fallback_judgment(self, battle: BattleResponse) -> Tuple[str, str]:
        """
        Provide fallback judgment when AI fails.

        Args:
            battle: Battle object

        Returns:
            Tuple[str, str]: (winner_name, feedback)
        """
        logger.info("Using random fallback judgment")

        winner = random.choice([battle.rapper1_name, battle.rapper2_name])
        feedback = "Winner determined by random selection due to AI judgment failure."

        return winner, feedback

    async def judge_round_and_update_battle(
        self,
        battle_id: UUID,
        round_id: UUID,
        use_ai: bool = True,
        user_judgment: Optional[JudgmentCreate] = None,
    ) -> Optional[BattleResponse]:
        """
        Judge a round and update the battle accordingly.

        Args:
            battle_id: UUID of the battle
            round_id: UUID of the round
            use_ai: Whether to use AI judgment
            user_judgment: Optional user judgment (if not using AI)

        Returns:
            Optional[BattleResponse]: Updated battle

        Raises:
            ValueError: If input data is invalid
            Exception: If judgment fails
        """
        try:
            battle = self.repository.get_battle(battle_id)
            if not battle:
                raise ValueError(f"Battle not found: {battle_id}")

            # Find the round
            target_round = None
            for round_obj in battle.rounds:
                if round_obj.id == round_id:
                    target_round = round_obj
                    break

            if not target_round:
                raise ValueError(f"Round not found: {round_id}")

            if use_ai:
                # Use AI judgment
                winner, feedback = await self.judge_round_ai(battle, target_round)
                target_round.user_judgment = False
                target_round.feedback = feedback
            else:
                # Use user judgment
                if not user_judgment:
                    raise ValueError("User judgment required when use_ai=False")

                winner = user_judgment.winner
                target_round.user_judgment = True
                # Store user feedback if provided
                if hasattr(user_judgment, 'feedback') and user_judgment.feedback:
                    target_round.feedback = user_judgment.feedback

            # Update round
            target_round.winner = winner
            target_round.status = "completed"

            # Update battle win counts
            if winner == battle.rapper1_name:
                battle.rapper1_wins += 1
            else:
                battle.rapper2_wins += 1

            # Check for battle completion
            battle_winner = self.determine_battle_winner(battle)
            if battle_winner:
                battle.winner = battle_winner
                battle.status = "completed"

            # Save changes
            updated_battle = self.repository.update_battle(battle)
            logger.info(f"Round {round_id} judged successfully, winner: {winner}")

            return updated_battle

        except Exception as e:
            logger.error(f"Failed to judge round {round_id}: {str(e)}")
            raise

    def determine_battle_winner(self, battle: BattleResponse) -> Optional[str]:
        """
        Determine the overall winner of a battle.

        Args:
            battle: Battle object

        Returns:
            Optional[str]: Winner name if there is one, None otherwise
        """
        # Winner needs 2 out of 3 rounds
        if battle.rapper1_wins >= 2:
            return battle.rapper1_name
        elif battle.rapper2_wins >= 2:
            return battle.rapper2_name

        # If all 3 rounds are complete but no clear winner, use round count
        completed_rounds = sum(1 for r in battle.rounds if r.status == "completed")
        if completed_rounds >= 3:
            if battle.rapper1_wins > battle.rapper2_wins:
                return battle.rapper1_name
            elif battle.rapper2_wins > battle.rapper1_wins:
                return battle.rapper2_name
            else:
                # Tie - could implement tiebreaker logic here
                return random.choice([battle.rapper1_name, battle.rapper2_name])

        return None


# Create singleton instance
judgment_service = JudgmentService()
