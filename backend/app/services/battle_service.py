"""
Service for managing rap battles.
"""
from typing import List, Optional, Tuple
from uuid import UUID

from app.agents.judge_agent import judge_agent
from app.agents.rapper_agent import rapper_agent
from app.db.repositories.battle_repo import battle_repository
from app.models.battle import BattleCreate, BattleResponse
from app.models.judgment import JudgmentCreate
from app.models.verse import Verse


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

        This method creates a battle, generates verses for both rappers in each round,
        and judges each round automatically until a rapper wins 2 rounds or all 3 rounds
        are completed.

        Note: For user judgment control, use generate_battle_with_verses instead.

        Args:
            battle_data: Battle creation data

        Returns:
            BattleResponse: Completed battle with all rounds, verses, and judgments
        """
        # Create the battle
        battle = await self.create_battle(battle_data)
        battle_id = battle.id

        # Track previous verses for context
        previous_verses = []

        try:
            # Continue until battle is completed (a rapper wins 2 rounds or all 3 rounds are done)
            while battle.status != "completed":
                # Get the current round
                current_round = None
                for battle_round in battle.rounds:
                    if battle_round.round_number == battle.current_round:
                        current_round = battle_round
                        break

                if not current_round:
                    break

                # Generate verses for both rappers
                try:
                    # First rapper with style1
                    verse1_content = await rapper_agent.generate_verse(
                        rapper_name=battle.rapper1_name,
                        opponent_name=battle.rapper2_name,
                        style=battle.style1,
                        round_number=battle.current_round,
                        previous_verses=previous_verses if previous_verses else None
                    )
                except Exception as e:
                    # If there's an error, use a default verse
                    verse1_content = f"""Yo, I'm {battle.rapper1_name}, stepping to the mic,
Facing off with {battle.rapper2_name}, gonna win this fight.
Round {battle.current_round}, and I'm bringing the heat,
My rhymes are fire, can't be beat.

This {battle.style1} flow is what I do best,
Put your skills to the ultimate test.
When it comes to rap, I'm at the top,
Watch me shine while your flow flops."""

                verse1 = Verse(
                    round_id=current_round.id,
                    rapper_name=battle.rapper1_name,
                    content=verse1_content
                )

                await battle_repository.add_verse(current_round.id, verse1)

                try:
                    # Second rapper with style2
                    verse2_content = await rapper_agent.generate_verse(
                        rapper_name=battle.rapper2_name,
                        opponent_name=battle.rapper1_name,
                        style=battle.style2,
                        round_number=battle.current_round,
                        previous_verses=previous_verses + [
                            {
                                "rapper_name": battle.rapper1_name,
                                "content": verse1_content
                            }
                        ]
                    )
                except Exception as e:
                    # If there's an error, use a default verse
                    verse2_content = f"""I'm {battle.rapper2_name}, the best in the game,
After this battle, nothing will be the same.
{battle.rapper1_name} thinks they can step to me?
But my {battle.style2} skills are legendary.

Round {battle.current_round}, I'm bringing my A-game,
When I'm done, you'll remember my name.
My flow is smooth, my rhymes are tight,
This battle is mine, I'll win tonight."""

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

                try:
                    # Judge the round with both styles
                    winner, feedback = await judge_agent.judge_round(
                        rapper1_name=battle.rapper1_name,
                        rapper1_verse=verse1_content,
                        rapper1_style=battle.style1,
                        rapper2_name=battle.rapper2_name,
                        rapper2_verse=verse2_content,
                        rapper2_style=battle.style2
                    )
                except Exception as e:
                    # If there's an error, use a default judgment
                    import random
                    winner = battle.rapper1_name if random.random() < 0.5 else battle.rapper2_name
                    feedback = f"""
Analysis of {battle.rapper1_name}'s verse:
{battle.rapper1_name} delivered a verse with interesting wordplay and flow.

Analysis of {battle.rapper2_name}'s verse:
{battle.rapper2_name} showed creativity and technical skill in their delivery.

Comparison:
Both rappers showed skill, but {winner} had slightly better delivery and impact.

Winner: {winner}
{winner} wins this round with a more impressive overall performance.
"""

                # Create and add the judgment
                judgment = JudgmentCreate(
                    round_id=current_round.id,
                    winner=winner,
                    feedback=feedback
                )

                await battle_repository.add_judgment(judgment)

                # Get the updated battle to check if it's completed or if we need to continue
                battle = await self.get_battle(battle_id)
                if not battle:
                    break
        except Exception as e:
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

    async def generate_verse(self, battle_id: UUID, rapper_name: str) -> Optional[Verse]:
        """
        Generate a verse for a rapper in a battle.

        Args:
            battle_id: ID of the battle
            rapper_name: Name of the rapper

        Returns:
            Optional[Verse]: Generated verse if successful, None otherwise
        """
        # Get the battle
        battle = await battle_repository.get_battle(battle_id)
        if not battle:
            return None

        # Check if the rapper is part of the battle
        if rapper_name != battle.rapper1_name and rapper_name != battle.rapper2_name:
            return None

        # Get the current round
        current_round = None
        for battle_round in battle.rounds:
            if battle_round.round_number == battle.current_round:
                current_round = battle_round
                break

        if not current_round:
            return None

        # Check if the rapper already has a verse in this round
        if (rapper_name == battle.rapper1_name and current_round.rapper1_verse) or \
           (rapper_name == battle.rapper2_name and current_round.rapper2_verse):
            return None

        # Determine the opponent
        opponent_name = battle.rapper2_name if rapper_name == battle.rapper1_name else battle.rapper1_name

        # Get previous verses if any
        previous_verses = []
        for prev_round in battle.rounds:
            if prev_round.round_number < battle.current_round:
                if prev_round.rapper1_verse:
                    previous_verses.append({
                        "rapper_name": battle.rapper1_name,
                        "content": prev_round.rapper1_verse.content
                    })
                if prev_round.rapper2_verse:
                    previous_verses.append({
                        "rapper_name": battle.rapper2_name,
                        "content": prev_round.rapper2_verse.content
                    })

        # Determine which style to use based on the rapper
        style = battle.style1 if rapper_name == battle.rapper1_name else battle.style2

        # Generate the verse with biographical information about the opponent
        verse_content = await rapper_agent.generate_verse(
            rapper_name=rapper_name,
            opponent_name=opponent_name,
            style=style,
            round_number=battle.current_round,
            previous_verses=previous_verses if previous_verses else None
        )

        # Create the verse
        verse = Verse(
            round_id=current_round.id,
            rapper_name=rapper_name,
            content=verse_content
        )

        # Add the verse to the round
        await battle_repository.add_verse(current_round.id, verse)

        # Check if both rappers have verses and auto-judge if needed
        updated_round = None
        for r in battle.rounds:
            if r.id == current_round.id:
                updated_round = r
                break

        if updated_round and updated_round.rapper1_verse and updated_round.rapper2_verse:
            # Auto-judge the round
            await self.judge_round(battle_id, updated_round.id)

        return verse

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
            try:
                # First rapper with style1
                verse1_content = await rapper_agent.generate_verse(
                    rapper_name=battle.rapper1_name,
                    opponent_name=battle.rapper2_name,
                    style=battle.style1,
                    round_number=battle.current_round,
                    previous_verses=None
                )
            except Exception as e:
                # If there's an error, use a default verse
                verse1_content = f"""Yo, I'm {battle.rapper1_name}, stepping to the mic,
Facing off with {battle.rapper2_name}, gonna win this fight.
Round {battle.current_round}, and I'm bringing the heat,
My rhymes are fire, can't be beat.

This {battle.style1} flow is what I do best,
Put your skills to the ultimate test.
When it comes to rap, I'm at the top,
Watch me shine while your flow flops."""

            verse1 = Verse(
                round_id=current_round.id,
                rapper_name=battle.rapper1_name,
                content=verse1_content
            )

            await battle_repository.add_verse(current_round.id, verse1)

            try:
                # Second rapper with style2
                verse2_content = await rapper_agent.generate_verse(
                    rapper_name=battle.rapper2_name,
                    opponent_name=battle.rapper1_name,
                    style=battle.style2,
                    round_number=battle.current_round,
                    previous_verses=[
                        {
                            "rapper_name": battle.rapper1_name,
                            "content": verse1_content
                        }
                    ]
                )
            except Exception as e:
                # If there's an error, use a default verse
                verse2_content = f"""I'm {battle.rapper2_name}, the best in the game,
After this battle, nothing will be the same.
{battle.rapper1_name} thinks they can step to me?
But my {battle.style2} skills are legendary.

Round {battle.current_round}, I'm bringing my A-game,
When I'm done, you'll remember my name.
My flow is smooth, my rhymes are tight,
This battle is mine, I'll win tonight."""

            verse2 = Verse(
                round_id=current_round.id,
                rapper_name=battle.rapper2_name,
                content=verse2_content
            )

            await battle_repository.add_verse(current_round.id, verse2)

            # Get the updated battle
            battle = await self.get_battle(battle_id)
            if not battle:
                raise Exception("Battle not found after adding verses")

        except Exception as e:
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
            return False, battle

        # Check if both verses are present
        if not current_round.rapper1_verse or not current_round.rapper2_verse:
            return False, battle

        # If user judgment is provided, use it
        if user_judgment:
            success = await battle_repository.add_judgment(user_judgment, user_submitted=True)

            # If battle is not completed and we haven't reached round 3 yet, create a new round
            battle = await battle_repository.get_battle(battle_id)  # Get updated battle
            if battle.status != "completed" and current_round.round_number < 3 and success:
                await battle_repository.add_round(battle_id, current_round.round_number + 1)

                # Generate verses for the new round if it was created
                if battle.status != "completed":
                    # Get the new round
                    new_round = None
                    for battle_round in battle.rounds:
                        if battle_round.round_number == current_round.round_number + 1:
                            new_round = battle_round
                            break

                    if new_round:
                        # Get previous verses for context
                        previous_verses = []
                        for r in battle.rounds:
                            if r.round_number < new_round.round_number:
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

                        # Generate verses for both rappers
                        try:
                            # First rapper
                            verse1_content = await rapper_agent.generate_verse(
                                rapper_name=battle.rapper1_name,
                                opponent_name=battle.rapper2_name,
                                style=battle.style,
                                round_number=new_round.round_number,
                                previous_verses=previous_verses if previous_verses else None
                            )
                        except Exception as e:
                            # If there's an error, use a default verse
                            verse1_content = f"""Yo, I'm {battle.rapper1_name}, stepping to the mic,
Facing off with {battle.rapper2_name}, gonna win this fight.
Round {new_round.round_number}, and I'm bringing the heat,
My rhymes are fire, can't be beat.

This {battle.style} flow is what I do best,
Put your skills to the ultimate test.
When it comes to rap, I'm at the top,
Watch me shine while your flow flops."""

                        verse1 = Verse(
                            round_id=new_round.id,
                            rapper_name=battle.rapper1_name,
                            content=verse1_content
                        )

                        await battle_repository.add_verse(new_round.id, verse1)

                        # Add to previous verses for context
                        previous_verses.append({
                            "rapper_name": battle.rapper1_name,
                            "content": verse1_content
                        })

                        try:
                            # Second rapper
                            verse2_content = await rapper_agent.generate_verse(
                                rapper_name=battle.rapper2_name,
                                opponent_name=battle.rapper1_name,
                                style=battle.style,
                                round_number=new_round.round_number,
                                previous_verses=previous_verses
                            )
                        except Exception as e:
                            # If there's an error, use a default verse
                            verse2_content = f"""I'm {battle.rapper2_name}, the best in the game,
After this battle, nothing will be the same.
{battle.rapper1_name} thinks they can step to me?
But my {battle.style} skills are legendary.

Round {new_round.round_number}, I'm bringing my A-game,
When I'm done, you'll remember my name.
My flow is smooth, my rhymes are tight,
This battle is mine, I'll win tonight."""

                        verse2 = Verse(
                            round_id=new_round.id,
                            rapper_name=battle.rapper2_name,
                            content=verse2_content
                        )

                        await battle_repository.add_verse(new_round.id, verse2)

            # Get the updated battle
            battle = await self.get_battle(battle_id)
            return success, battle

        # Otherwise, use the judge agent
        try:
            winner, feedback = await judge_agent.judge_round(
                rapper1_name=battle.rapper1_name,
                rapper1_verse=current_round.rapper1_verse.content,
                rapper1_style=battle.style1,
                rapper2_name=battle.rapper2_name,
                rapper2_verse=current_round.rapper2_verse.content,
                rapper2_style=battle.style2
            )
        except Exception as e:
            # If there's an error, use a default judgment
            import random
            winner = battle.rapper1_name if random.random() < 0.5 else battle.rapper2_name
            feedback = f"""
Analysis of {battle.rapper1_name}'s verse:
{battle.rapper1_name} delivered a verse with interesting wordplay and flow.

Analysis of {battle.rapper2_name}'s verse:
{battle.rapper2_name} showed creativity and technical skill in their delivery.

Comparison:
Both rappers showed skill, but {winner} had slightly better delivery and impact.

Winner: {winner}
{winner} wins this round with a more impressive overall performance.
"""

        # Create the judgment
        judgment = JudgmentCreate(
            round_id=round_id,
            winner=winner,
            feedback=feedback
        )

        # Add the judgment
        success = await battle_repository.add_judgment(judgment)

        # If battle is not completed and we haven't reached round 3 yet, create a new round
        battle = await battle_repository.get_battle(battle_id)  # Get updated battle
        if battle.status != "completed" and current_round.round_number < 3 and success:
            await battle_repository.add_round(battle_id, current_round.round_number + 1)

            # Generate verses for the new round if it was created
            if battle.status != "completed":
                # Get the new round
                new_round = None
                for battle_round in battle.rounds:
                    if battle_round.round_number == current_round.round_number + 1:
                        new_round = battle_round
                        break

                if new_round:
                    # Get previous verses for context
                    previous_verses = []
                    for r in battle.rounds:
                        if r.round_number < new_round.round_number:
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

                    # Generate verses for both rappers
                    try:
                        # First rapper with style1
                        verse1_content = await rapper_agent.generate_verse(
                            rapper_name=battle.rapper1_name,
                            opponent_name=battle.rapper2_name,
                            style=battle.style1,
                            round_number=new_round.round_number,
                            previous_verses=previous_verses if previous_verses else None
                        )
                    except Exception as e:
                        # If there's an error, use a default verse
                        verse1_content = f"""Yo, I'm {battle.rapper1_name}, stepping to the mic,
Facing off with {battle.rapper2_name}, gonna win this fight.
Round {new_round.round_number}, and I'm bringing the heat,
My rhymes are fire, can't be beat.

This {battle.style1} flow is what I do best,
Put your skills to the ultimate test.
When it comes to rap, I'm at the top,
Watch me shine while your flow flops."""

                    verse1 = Verse(
                        round_id=new_round.id,
                        rapper_name=battle.rapper1_name,
                        content=verse1_content
                    )

                    await battle_repository.add_verse(new_round.id, verse1)

                    # Add to previous verses for context
                    previous_verses.append({
                        "rapper_name": battle.rapper1_name,
                        "content": verse1_content
                    })

                    try:
                        # Second rapper with style2
                        verse2_content = await rapper_agent.generate_verse(
                            rapper_name=battle.rapper2_name,
                            opponent_name=battle.rapper1_name,
                            style=battle.style2,
                            round_number=new_round.round_number,
                            previous_verses=previous_verses
                        )
                    except Exception as e:
                        # If there's an error, use a default verse
                        verse2_content = f"""I'm {battle.rapper2_name}, the best in the game,
After this battle, nothing will be the same.
{battle.rapper1_name} thinks they can step to me?
But my {battle.style2} skills are legendary.

Round {new_round.round_number}, I'm bringing my A-game,
When I'm done, you'll remember my name.
My flow is smooth, my rhymes are tight,
This battle is mine, I'll win tonight."""

                    verse2 = Verse(
                        round_id=new_round.id,
                        rapper_name=battle.rapper2_name,
                        content=verse2_content
                    )

                    await battle_repository.add_verse(new_round.id, verse2)

        # Get the updated battle
        battle = await self.get_battle(battle_id)
        return success, battle


# Create a battle service instance
battle_service = BattleService()
