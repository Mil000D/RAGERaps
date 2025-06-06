"""
Service for generating verses in rap battles.
"""

import logging
import random
from typing import Dict, List, Optional, Tuple

from app.agents.parallel_workflow import execute_battle_round_parallel
from app.models.battle import BattleResponse
from app.models.round import Round
from app.models.verse import Verse

logger = logging.getLogger(__name__)


class VerseGenerationService:
    """Service responsible for generating verses for rap battles."""

    async def generate_verses_for_round(
        self,
        battle: BattleResponse,
        round_obj: Round,
        previous_verses: List[Dict[str, str]],
    ) -> Tuple[Optional[Verse], Optional[Verse]]:
        """
        Generate verses for both rappers in a round using parallel execution.

        Args:
            battle: The battle object
            round_obj: The round object
            previous_verses: List of previous verses for context

        Returns:
            Tuple[Optional[Verse], Optional[Verse]]: Generated verses for both rappers
        """
        try:
            logger.info(
                f"Generating verses for round {round_obj.round_number} in battle {battle.id}"
            )

            # Execute parallel verse generation
            result = await execute_battle_round_parallel(
                round_id=round_obj.id,
                rapper1_name=battle.rapper1_name,
                rapper2_name=battle.rapper2_name,
                style1=battle.style1,
                style2=battle.style2,
                round_number=round_obj.round_number,
                previous_verses=previous_verses,
            )

            # Extract verses from the result
            verses = result.get("verses", [])
            rapper1_verse = None
            rapper2_verse = None

            # Find verses for each rapper
            for verse in verses:
                if verse["rapper_name"] == battle.rapper1_name:
                    rapper1_verse = Verse(
                        round_id=round_obj.id,
                        rapper_name=battle.rapper1_name,
                        content=verse["content"],
                    )
                elif verse["rapper_name"] == battle.rapper2_name:
                    rapper2_verse = Verse(
                        round_id=round_obj.id,
                        rapper_name=battle.rapper2_name,
                        content=verse["content"],
                    )

            # Validate and handle results
            if not rapper1_verse or not rapper2_verse:
                logger.warning(
                    f"Failed to generate verses for round {round_obj.round_number}, using fallback"
                )
                return self._generate_fallback_verses(battle, round_obj)

            logger.info(
                f"Successfully generated verses for round {round_obj.round_number}"
            )
            return rapper1_verse, rapper2_verse

        except Exception as e:
            logger.error(
                f"Error generating verses for round {round_obj.round_number}: {str(e)}"
            )
            return self._generate_fallback_verses(battle, round_obj)

    def _generate_fallback_verses(
        self, battle: BattleResponse, round_obj: Round
    ) -> Tuple[Verse, Verse]:
        """
        Generate simple fallback verses when AI generation fails.

        Args:
            battle: The battle object
            round_obj: The round object

        Returns:
            Tuple[Verse, Verse]: Fallback verses for both rappers
        """
        logger.info(f"Generating fallback verses for round {round_obj.round_number}")

        # Simple fallback verses
        fallback_lines = [
            "I'm the king of this game, no one can compete",
            "My rhymes are so fire, they can't be beat",
            "Step to me wrong and you'll face defeat",
            "I'm on another level, my flow's so neat",
            "Respect my name, I'm elite on the street",
            "My words cut deep, my verses are sweet",
            "You can't match my style, accept your defeat",
            "I rise to the top, that's my main feat",
        ]

        rapper1_content = "\n".join(random.sample(fallback_lines, 4))
        rapper2_content = "\n".join(random.sample(fallback_lines, 4))

        rapper1_verse = Verse(
            round_id=round_obj.id,
            rapper_name=battle.rapper1_name,
            content=rapper1_content,
        )

        rapper2_verse = Verse(
            round_id=round_obj.id,
            rapper_name=battle.rapper2_name,
            content=rapper2_content,
        )

        return rapper1_verse, rapper2_verse


# Create singleton instance
verse_generation_service = VerseGenerationService()
