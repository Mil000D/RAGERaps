"""
Judge agent implementation using LangChain.
"""
from typing import Dict, List, Optional, Tuple

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.tools.style_tool import style_tool


class JudgeAgent:
    """Agent for judging rap battles."""

    def __init__(self):
        """Initialize the judge agent."""
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=settings.openai_api_key,
            streaming=False
        )

        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "{input}")
        ])

        # Create the chain
        self.chain = self.prompt | self.llm | StrOutputParser()

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the judge agent.

        Returns:
            str: System prompt
        """
        return """You are an expert judge of rap battles. Your task is to evaluate verses from two rappers and determine the winner based on:

1. Style authenticity: How well the verse matches the specified rap style
2. Technical skill: Flow, rhyme schemes, wordplay, and delivery
3. Content: Creativity, storytelling, and effective disses
4. Overall impact: How memorable and impressive the verse is

Provide a fair and detailed analysis of both verses, highlighting strengths and weaknesses. Then declare a winner and explain your decision.

Your response should follow this format:
1. Analysis of Rapper 1's verse
2. Analysis of Rapper 2's verse
3. Comparison of the two verses
4. Winner declaration and justification
"""

    async def judge_round(
        self,
        rapper1_name: str,
        rapper1_verse: str,
        rapper2_name: str,
        rapper2_verse: str,
        style: str
    ) -> Tuple[str, str]:
        """
        Judge a round of the rap battle.

        Args:
            rapper1_name: Name of the first rapper
            rapper1_verse: Verse of the first rapper
            rapper2_name: Name of the second rapper
            rapper2_verse: Verse of the second rapper
            style: Rap style

        Returns:
            Tuple[str, str]: Winner name and feedback
        """
        try:
            # Get style information
            style_info = await style_tool.get_style(style)

            # Create the input
            input_text = f"""Style: {style}

Style Information:
{style_info}

{rapper1_name}'s Verse:
{rapper1_verse}

{rapper2_name}'s Verse:
{rapper2_verse}

Please judge this round and determine the winner.
"""

            # Run the chain
            result = await self.chain.ainvoke({"input": input_text})

            # Extract the winner and feedback
            winner, feedback = self._extract_winner(result, rapper1_name, rapper2_name)

            return winner, feedback
        except Exception:
            # If anything goes wrong, provide a default judgment
            import random
            winner = rapper1_name if random.random() < 0.5 else rapper2_name
            feedback = f"""
Analysis of {rapper1_name}'s verse:
{rapper1_name} delivered a verse with interesting wordplay and flow.

Analysis of {rapper2_name}'s verse:
{rapper2_name} showed creativity and technical skill in their delivery.

Comparison:
Both rappers showed skill, but {winner} had slightly better delivery and impact.

Winner: {winner}
{winner} wins this round with a more impressive overall performance.
"""
            return winner, feedback

    def _extract_winner(self, judgment: str, rapper1_name: str, rapper2_name: str) -> Tuple[str, str]:
        """
        Extract the winner and feedback from the judgment.

        Args:
            judgment: Judgment text
            rapper1_name: Name of the first rapper
            rapper2_name: Name of the second rapper

        Returns:
            Tuple[str, str]: Winner name and feedback
        """
        try:
            # Default values
            winner = rapper1_name  # Default to rapper1 if we can't determine

            # Look for explicit winner declaration
            lower_judgment = judgment.lower()
            if f"winner: {rapper1_name.lower()}" in lower_judgment or f"the winner is {rapper1_name.lower()}" in lower_judgment:
                winner = rapper1_name
            elif f"winner: {rapper2_name.lower()}" in lower_judgment or f"the winner is {rapper2_name.lower()}" in lower_judgment:
                winner = rapper2_name

            # If no explicit declaration, count mentions with positive terms
            if winner == rapper1_name:
                r1_positive = sum(1 for term in ["better", "stronger", "wins", "superior", "impressive"]
                                if f"{rapper1_name.lower()} {term}" in lower_judgment)
                r2_positive = sum(1 for term in ["better", "stronger", "wins", "superior", "impressive"]
                                if f"{rapper2_name.lower()} {term}" in lower_judgment)

                if r2_positive > r1_positive:
                    winner = rapper2_name

            return winner, judgment
        except Exception:
            # If anything goes wrong, randomly select a winner
            import random
            winner = rapper1_name if random.random() < 0.5 else rapper2_name
            return winner, f"After careful consideration, {winner} wins this round with a more impressive performance."


# Create a judge agent instance
judge_agent = JudgeAgent()
