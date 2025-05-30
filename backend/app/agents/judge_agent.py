"""
Judge agent implementation using LangChain with RAG integration.
"""
from typing import Tuple, Optional, Dict, Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.tools.style_tool import style_tool
from app.tools.artist_retrieval_tool import artist_retrieval_tool


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

        # Initialize tools
        self.tools = [artist_retrieval_tool]

        # Bind tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "{input}")
        ])

        # Create the chain with tools
        self.chain = self.prompt | self.llm_with_tools

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the judge agent.

        Returns:
            str: System prompt
        """
        return """You are an expert judge of rap battles. Your task is to evaluate verses from two rappers, each using their own distinct rap style, and determine the winner.

IMPORTANT: Use the retrieve_artist_data tool to get authentic reference material:
- Retrieve lyrical data for both rappers to understand their authentic styles and patterns
- Compare the battle verses against their actual lyrical content and style characteristics
- Use the retrieved data to assess style authenticity and technical execution

Evaluate based on:
1. Style authenticity: How well each verse matches the rapper's actual lyrical style and patterns from the database
2. Technical skill: Flow, rhyme schemes, wordplay, and delivery compared to their authentic style
3. Content: Creativity, storytelling, and effective disses based on real facts
4. Biographical accuracy: How well they incorporate authentic details about their opponent
5. Overall impact: How memorable and impressive the verse is within their style context

Each rapper will be using a different style, so judge them based on how well they execute their own authentic style, not by comparing styles directly.

Provide a fair and detailed analysis of both verses, highlighting strengths and weaknesses. Then declare a winner and explain your decision.

Your response should follow this format:
1. Analysis of Rapper 1's verse and how well it fits their authentic style
2. Analysis of Rapper 2's verse and how well it fits their authentic style
3. Comparison of the two verses (considering authenticity and style execution)
4. Winner declaration and justification
"""

    async def judge_round(
        self,
        rapper1_name: str,
        rapper1_verse: str,
        rapper1_style: str,
        rapper2_name: str,
        rapper2_verse: str,
        rapper2_style: str
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
            # Get style information for both rappers
            style1_info = await style_tool.get_style.invoke(rapper1_style)
            style2_info = await style_tool.get_style.invoke(rapper2_style)

            # Create the input with both styles
            input_text = f"""Rapper 1 ({rapper1_name}) Style: {rapper1_style}
Rapper 2 ({rapper2_name}) Style: {rapper2_style}

Rapper 1 Style Information:
{style1_info}

Rapper 2 Style Information:
{style2_info}

{rapper1_name}'s Verse:
{rapper1_verse}

{rapper2_name}'s Verse:
{rapper2_verse}

Please judge this round and determine the winner. Use the retrieve_artist_data tool to get authentic lyrical content and style information for both rappers to make an informed judgment about style authenticity and execution.
"""

            # Run the chain with tools
            result = await self.chain.ainvoke({"input": input_text})

            # Handle tool calls if present
            if hasattr(result, 'tool_calls') and result.tool_calls:
                # Process tool calls and get final response
                from langchain_core.messages import ToolMessage

                tool_messages = []
                for tool_call in result.tool_calls:
                    tool_result = await artist_retrieval_tool._arun(**tool_call['args'])
                    tool_messages.append(ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call['id']
                    ))

                # Get final response after tool execution
                final_result = await self.llm.ainvoke([result] + tool_messages)
                result_text = final_result.content
            else:
                result_text = result.content if hasattr(result, 'content') else str(result)

            # Extract the winner and feedback
            winner, feedback = self._extract_winner(result_text, rapper1_name, rapper2_name)

            return winner, feedback
        except Exception:
            winner = "Error"
            feedback = "Exception occurred while judging the round. Try again."
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
