"""
Service for managing rap battles.
"""
import logging
import random
from typing import List, Optional, Tuple
from uuid import UUID

from app.agents.judge_agent import judge_agent
from app.agents.parallel_workflow import execute_battle_round_parallel
from app.db.repositories.battle_repo import battle_repository
from app.models.battle import BattleCreate, BattleResponse
from app.models.judgment import JudgmentCreate
from app.models.verse import Verse
from app.services.prompt_service import prompt_service

# Configure logger
logger = logging.getLogger(__name__)


def get_previous_verses(battle, round_number):
    """
    Get verses from previous rounds.

    Args:
        battle: Battle object
        round_number: Current round number

    Returns:
        List of previous verses
    """
    previous_verses = []
    for r in battle.rounds:
        if r.round_number < round_number:
            if r.rapper1_verse:
                previous_verses.append({
                    "rapper_name": battle.rapper1_name,
                    "content": r.rapper1_verse.content
                })
            if r.rapper2_verse:
                previous_verses.append({
                    "rapper_name": battle.rapper2_name,
                    "content": r.rapper2_verse.content
                })
    return previous_verses


def _clean_judgment_feedback(feedback: str, winner: str) -> str:
    """
    Clean up judgment feedback by removing redundant winner declarations.

    Args:
        feedback: Original feedback text
        winner: Name of the winner

    Returns:
        str: Cleaned feedback text
    """
    # Check for improperly formatted winner declaration (no delimiter after name)
    winner_header_match = feedback.lower().startswith(f"winner: {winner.lower()}")
    if winner_header_match:
        # Find where the winner name ends
        winner_end_pos = feedback.lower().find(winner.lower()) + len(winner)

        # If there's no delimiter after the winner name, add a period and newline
        if winner_end_pos < len(feedback) and feedback[winner_end_pos] != '\n' and feedback[winner_end_pos] != '.':
            # Insert delimiter after winner name
            feedback = feedback[:winner_end_pos] + ".\n\n" + feedback[winner_end_pos:].lstrip()

    # Format the sections consistently
    sections = {
        "Analysis of": "\n\nAnalysis of",
        "Comparison:": "\n\nComparison:"
    }

    for section, formatted in sections.items():
        pos = feedback.find(section)
        if pos > 0:
            # Ensure there's proper formatting before section headers
            feedback = feedback[:pos] + formatted + feedback[pos+len(section):]

    # Remove winner declaration from the beginning if present
    if feedback.lower().startswith(f"winner: {winner.lower()}"):
        # Find the first sentence end after winner declaration and remove everything before it
        first_sentence_end = feedback.find(".", feedback.lower().find(winner.lower()))
        if first_sentence_end > 0:
            feedback = feedback[first_sentence_end + 1:].strip()

    # Extract and clean the comparison section
    comparison_pos = feedback.lower().find("comparison:")
    if comparison_pos > 0:
        # Look for "Winner:" or "[winner] wins" phrases in the comparison section
        comparison_text = feedback[comparison_pos + len("Comparison:"):]

        # Patterns to look for in the comparison section
        winner_patterns = [
            f"winner: {winner}",
            f"the winner is {winner}",
            f"{winner} wins",
            f"{winner} is the winner"
        ]

        for pattern in winner_patterns:
            pattern_pos = comparison_text.lower().find(pattern.lower())
            if pattern_pos > 0:
                # Find the last complete sentence before the winner declaration
                last_period = comparison_text.rfind(".", 0, pattern_pos)
                if last_period > 0:
                    # Keep only the text up to that sentence
                    clean_comparison = comparison_text[:last_period + 1].strip()

                    # Replace the original comparison text with the cleaned version
                    feedback = feedback[:comparison_pos + len("Comparison:")] + " " + clean_comparison
                    break

    # Ensure feedback doesn't end with multiple periods
    feedback = feedback.rstrip(".") + "."

    return feedback


async def judge_round_ai(battle, current_round) -> JudgmentCreate:
    """
    Use AI to judge a battle round.

    Args:
        battle: Battle object
        current_round: Current round object

    Returns:
        JudgmentCreate: Judgment data
    """
    try:
        if not current_round.rapper1_verse or not current_round.rapper2_verse:
            raise ValueError("Both verses must be present to judge a round")

        winner, feedback = await judge_agent.judge_round(
            rapper1_name=battle.rapper1_name,
            rapper1_verse=current_round.rapper1_verse.content,
            rapper1_style=battle.style1,
            rapper2_name=battle.rapper2_name,
            rapper2_verse=current_round.rapper2_verse.content,
            rapper2_style=battle.style2
        )

        logger.info(f"Round {current_round.round_number} judged by AI. Winner: {winner}")

        return JudgmentCreate(
            round_id=current_round.id,
            winner=winner,
            feedback=feedback
        )
    except Exception as e:
        logger.error(f"Error judging round {current_round.round_number}: {e}")

        # Generate a default judgment if there's an error
        winner = battle.rapper1_name if random.random() < 0.5 else battle.rapper2_name
        feedback = prompt_service.get_default_judgment(
            rapper1_name=battle.rapper1_name,
            rapper2_name=battle.rapper2_name,
            winner=winner
        )
        # Clean up the default feedback
        cleaned_feedback = _clean_judgment_feedback(feedback, winner)

        return JudgmentCreate(
            round_id=current_round.id,
            winner=winner,
            feedback=cleaned_feedback
        )


async def generate_verses_for_round(battle, round_obj, previous_verses=None, cached_data=None):
    """
    Generate verses for both rappers in a round.

    Args:
        battle: Battle object
        round_obj: Round object
        previous_verses: Previous verses for context
        cached_data: Cached data for optimization

    Returns:
        Tuple of (verse1, verse2): Generated verses for both rappers
    """
    try:
        # Execute the battle round with parallel agent execution
        round_result = await execute_battle_round_parallel(
            round_id=str(round_obj.id),
            rapper1_name=battle.rapper1_name,
            rapper2_name=battle.rapper2_name,
            style1=battle.style1,
            style2=battle.style2,
            round_number=round_obj.round_number,
            previous_verses=previous_verses if previous_verses else None,
            cached_data=cached_data
        )

        # Extract verses from the result
        verse1_content = None
        verse2_content = None

        # Process verses
        for verse in round_result["verses"]:
            if verse["rapper_name"] == battle.rapper1_name:
                verse1_content = verse["content"]
            elif verse["rapper_name"] == battle.rapper2_name:
                verse2_content = verse["content"]

        # Create verse objects
        verse1 = Verse(
            round_id=round_obj.id,
            rapper_name=battle.rapper1_name,
            content=verse1_content
        )

        verse2 = Verse(
            round_id=round_obj.id,
            rapper_name=battle.rapper2_name,
            content=verse2_content
        )

        # Return extracted data including cached data for future rounds
        cached_data = round_result.get("cached_data")
        return verse1, verse2, cached_data

    except Exception as e:
        logger.error(f"Error generating verses for round {round_obj.round_number}: {e}")

        # If there's an error, use fallback verses
        verse1_content = prompt_service.get_fallback_verse(
            "rapper1",
            rapper_name=battle.rapper1_name,
            opponent_name=battle.rapper2_name,
            round_number=round_obj.round_number,
            style=battle.style1
        )

        verse2_content = prompt_service.get_fallback_verse(
            "rapper2",
            rapper_name=battle.rapper2_name,
            opponent_name=battle.rapper1_name,
            round_number=battle.round_number,
            style=battle.style2
        )

        verse1 = Verse(
            round_id=round_obj.id,
            rapper_name=battle.rapper1_name,
            content=verse1_content
        )

        verse2 = Verse(
            round_id=round_obj.id,
            rapper_name=battle.rapper2_name,
            content=verse2_content
        )

        return verse1, verse2, None


class BattleService:
    """Service for managing rap battles."""

    async def create_battle(self, battle_data: BattleCreate) -> BattleResponse:
        """
        Create a new battle.

        Args:
            battle_data: Battle creation data

        Returns:
            BattleResponse: Created battle
        """
        # Create the battle
        battle = await battle_repository.create_battle(battle_data)

        # Create the first round
        await battle_repository.add_round(battle.id, 1)

        return BattleResponse.model_validate(battle)

    async def generate_complete_battle(self, battle_data: BattleCreate) -> BattleResponse:
        """
        Generate a complete battle with all rounds and verses in one go.

        This method creates a battle and generates verses for both rappers in each round.
        Automatic judging has been removed - users can manually judge rounds using the API endpoints.

        Note: This method now behaves similarly to generate_battle_with_verses but for all rounds.

        Args:
            battle_data: Battle creation data

        Returns:
            BattleResponse: Battle with all rounds and verses (no automatic judgments)
        """
        # Create the battle
        battle = await self.create_battle(battle_data)
        battle_id = battle.id

        # Track previous verses for context
        previous_verses = []

        # Track cached data across rounds to avoid redundant API calls
        cached_data = None

        try:
            # Generate verses for all rounds (no automatic judging)
            for round_number in range(1, 4):  # Generate verses for rounds 1, 2, and 3
                # Get the current round
                current_round = None
                for battle_round in battle.rounds:
                    if battle_round.round_number == round_number:
                        current_round = battle_round
                        break

                if not current_round:
                    # Create the round if it doesn't exist
                    await battle_repository.add_round(battle_id, round_number)
                    battle = await self.get_battle(battle_id)
                    for battle_round in battle.rounds:
                        if battle_round.round_number == round_number:
                            current_round = battle_round
                            break

                if not current_round:
                    break

                # Generate verses for both rappers in parallel (no automatic judging)
                try:
                    # Generate verses using our refactored helper function
                    verse1, verse2, new_cached_data = await generate_verses_for_round(
                        battle=battle,
                        round_obj=current_round,
                        previous_verses=previous_verses if previous_verses else None,
                        cached_data=cached_data
                    )

                    # Update cached data if available
                    if new_cached_data:
                        cached_data = new_cached_data

                    # Save verses to database
                    await battle_repository.add_verse(current_round.id, verse1)
                    await battle_repository.add_verse(current_round.id, verse2)

                    # Add verses to previous verses for context in next round
                    previous_verses.append({
                        "rapper_name": battle.rapper1_name,
                        "content": verse1.content
                    })
                    previous_verses.append({
                        "rapper_name": battle.rapper2_name,
                        "content": verse2.content
                    })

                    # Note: Automatic judging has been removed. Users can manually judge rounds using the API endpoints.
                except Exception as e:
                    logger.error(f"Error generating verses for round {round_number}: {e}")

                    # If there's an error, use default verses and judgment
                    # First rapper with style1
                    verse1_content = prompt_service.get_fallback_verse(
                        "rapper1",
                        rapper_name=battle.rapper1_name,
                        opponent_name=battle.rapper2_name,
                        round_number=battle.current_round,
                        style=battle.style1
                    )

                    verse1 = Verse(
                        round_id=current_round.id,
                        rapper_name=battle.rapper1_name,
                        content=verse1_content
                    )

                    await battle_repository.add_verse(current_round.id, verse1)

                    # Second rapper with style2
                    verse2_content = prompt_service.get_fallback_verse(
                        "rapper2",
                        rapper_name=battle.rapper2_name,
                        opponent_name=battle.rapper1_name,
                        round_number=battle.current_round,
                        style=battle.style2
                    )

                    verse2 = Verse(
                        round_id=current_round.id,
                        rapper_name=battle.rapper2_name,
                        content=verse2_content
                    )

                    await battle_repository.add_verse(current_round.id, verse2)

                    # Add verses to previous verses for context in next round
                    previous_verses.append({
                        "rapper_name": battle.rapper1_name,
                        "content": verse1_content
                    })
                    previous_verses.append({
                        "rapper_name": battle.rapper2_name,
                        "content": verse2_content
                    })
        except Exception as e:
            logger.error(f"Error generating complete battle: {e}")

            # If there's an error during generation, return the battle in its current state
            # This ensures we don't lose progress if something goes wrong
            battle = await self.get_battle(battle_id)
            if not battle:
                # If we can't get the battle, re-raise the exception
                raise e

        return battle

    async def get_battle(self, battle_id: UUID) -> Optional[BattleResponse]:
        """
        Get a battle by ID.

        Args:
            battle_id: ID of the battle to retrieve

        Returns:
            Optional[BattleResponse]: Battle if found, None otherwise
        """
        battle = await battle_repository.get_battle(battle_id)
        if not battle:
            return None

        return BattleResponse.model_validate(battle)

    async def list_battles(self) -> List[BattleResponse]:
        """
        List all battles.

        Returns:
            List[BattleResponse]: List of all battles
        """
        battles = await battle_repository.list_battles()
        return [BattleResponse.model_validate(battle) for battle in battles]

    async def generate_battle_with_verses(self, battle_data: BattleCreate) -> BattleResponse:
        """
        Generate a battle with verses for both rappers but without automatic judgment.

        This method creates a battle and generates verses for both rappers in the first round,
        but does not automatically judge the round. This allows the user to choose between
        AI judgment or manually selecting a winner.

        Args:
            battle_data: Battle creation data

        Returns:
            BattleResponse: Battle with verses but without judgment
        """
        # Create the battle
        battle = await self.create_battle(battle_data)
        battle_id = battle.id

        try:
            # Get the current round (should be round 1)
            current_round = None
            for battle_round in battle.rounds:
                if battle_round.round_number == battle.current_round:
                    current_round = battle_round
                    break

            if not current_round:
                return BattleResponse.model_validate(battle)

            # Generate verses for both rappers
            verse1, verse2, _ = await generate_verses_for_round(
                battle=battle,
                round_obj=current_round,
                previous_verses=None,
                cached_data=None
            )

            # Save verses to database
            await battle_repository.add_verse(current_round.id, verse1)
            await battle_repository.add_verse(current_round.id, verse2)

            # Get the updated battle
            battle = await self.get_battle(battle_id)
            if not battle:
                raise Exception("Battle not found after adding verses")

        except Exception as e:
            logger.error(f"Error generating battle with verses: {e}")

            # If there's an error during generation, return the battle in its current state
            battle = await self.get_battle(battle_id)
            if not battle:
                # If we can't get the battle, re-raise the exception
                raise e

        return battle

    async def judge_round(self, battle_id: UUID, round_id: UUID, user_judgment: Optional[JudgmentCreate] = None) -> Tuple[bool, BattleResponse]:
        """
        Judge a round of the battle.

        This method judges a round of the battle, either using the provided user judgment
        or by using the AI judge agent. After judging, it updates the battle state,
        checks if a rapper has won 2 rounds, and creates a new round if needed.

        Args:
            battle_id: ID of the battle
            round_id: ID of the round
            user_judgment: User judgment if provided

        Returns:
            Tuple[bool, BattleResponse]: Success status and updated battle
        """
        # Get the battle
        battle = await battle_repository.get_battle(battle_id)
        if not battle:
            return False, None

        # Find the round
        current_round = None
        for battle_round in battle.rounds:
            if battle_round.id == round_id:
                current_round = battle_round
                break

        if not current_round:
            return False, BattleResponse.model_validate(battle)

        # Check if both verses are present
        if not current_round.rapper1_verse or not current_round.rapper2_verse:
            return False, BattleResponse.model_validate(battle)

        # Process judgment (either user provided or AI generated)
        if user_judgment:
            judgment = user_judgment
            user_submitted = True
        else:
            # Use AI to judge the round
            judgment = await judge_round_ai(battle, current_round)
            user_submitted = False

        # Add the judgment to the database
        success = await battle_repository.add_judgment(judgment, user_submitted=user_submitted)
        if not success:
            return False, BattleResponse.model_validate(battle)

        # Get updated battle after judgment
        battle = await battle_repository.get_battle(battle_id)

        # Create next round if battle isn't completed and we're not at round 3 yet
        if battle.status != "completed" and current_round.round_number < 3:
            await self._create_next_round_with_verses(battle, current_round)

        # Get the final battle state
        battle = await self.get_battle(battle_id)
        return success, BattleResponse.model_validate(battle)

    async def _create_next_round_with_verses(self, battle, current_round):
        """
        Helper method to create the next round and generate verses for it.

        Args:
            battle: Battle object
            current_round: Current round that was just judged
        """
        # Create the next round
        await battle_repository.add_round(battle.id, current_round.round_number + 1)

        # Get the updated battle
        battle = await battle_repository.get_battle(battle.id)

        # Find the new round
        new_round = None
        for battle_round in battle.rounds:
            if battle_round.round_number == current_round.round_number + 1:
                new_round = battle_round
                break

        if new_round:
            # Get previous verses for context
            previous_verses = get_previous_verses(battle, new_round.round_number)

            # Generate verses for both rappers
            verse1, verse2, _ = await generate_verses_for_round(
                battle=battle,
                round_obj=new_round,
                previous_verses=previous_verses,
                cached_data=None
            )

            # Save verses to database
            await battle_repository.add_verse(new_round.id, verse1)
            await battle_repository.add_verse(new_round.id, verse2)

battle_service = BattleService()
