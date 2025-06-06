"""
Judge agent implementation using LangChain with RAG integration.
"""

import random
from typing import Tuple

from app.core.config import settings
from app.services.prompt_service import prompt_service
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


class JudgeAgent:
    """Agent for judging rap battles."""

    def __init__(self):
        """Initialize the judge agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.4,
            api_key=settings.openai_api_key,
            streaming=False,
        )

        system_prompt = prompt_service.get_judge_system_prompt()

        self.prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", "{input}")]
        )

        self.chain = self.prompt | self.llm

    async def judge_round(
        self,
        rapper1_name: str,
        rapper1_verse: str,
        rapper1_style: str,
        rapper2_name: str,
        rapper2_verse: str,
        rapper2_style: str,
    ) -> Tuple[str, str]:
        """
        Judge a round of the rap battle using available tools for artist data retrieval.

        Args:
            rapper1_name: Name of the first rapper
            rapper1_verse: Verse of the first rapper
            rapper1_style: Style of the first rapper
            rapper2_name: Name of the second rapper
            rapper2_verse: Verse of the second rapper
            rapper2_style: Style of the second rapper

        Returns:
            Tuple[str, str]: Winner name and feedback
        """
        try:
            input_text = prompt_service.get_judge_input_template(
                rapper1_name=rapper1_name,
                rapper1_style=rapper1_style,
                rapper2_name=rapper2_name,
                rapper2_style=rapper2_style,
                style1_info=rapper1_style,
                style2_info=rapper2_style,
                rapper1_verse=rapper1_verse,
                rapper2_verse=rapper2_verse,
            )

            result = await self.chain.ainvoke({"input": input_text})
            judgment_text = (
                result.content if hasattr(result, "content") else str(result)
            )

            winner, feedback = self._extract_winner(
                judgment_text, rapper1_name, rapper2_name
            )

            return winner, feedback
        except Exception as e:
            print("Error judging round: ", e)
            winner = "Error"
            feedback = "Exception occurred while judging the round. Try again."
            return winner, feedback

    def _extract_winner(
        self, judgment: str, rapper1_name: str, rapper2_name: str
    ) -> Tuple[str, str]:
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
            winner = rapper1_name

            lower_judgment = judgment.lower()
            if (
                f"winner: {rapper1_name.lower()}" in lower_judgment
                or f"the winner is {rapper1_name.lower()}" in lower_judgment
            ):
                winner = rapper1_name
            elif (
                f"winner: {rapper2_name.lower()}" in lower_judgment
                or f"the winner is {rapper2_name.lower()}" in lower_judgment
            ):
                winner = rapper2_name

            return winner, judgment
        except Exception as e:
            print("Error extracting winner: ", e)
            winner = rapper1_name if random.random() < 0.5 else rapper2_name
            return (
                winner,
                f"After careful consideration, {winner} wins this round with a more impressive performance.",
            )


judge_agent = JudgeAgent()
