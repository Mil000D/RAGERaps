"""
Rapper agent implementation using LangGraph.
"""
from typing import Annotated, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, add_messages
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.config import settings
from app.tools.search_tool import search_tool
from app.tools.style_tool import style_tool


class RapperState(TypedDict):
    """State for the rapper agent."""

    messages: Annotated[List[AnyMessage], add_messages]
    rapper_name: str
    opponent_name: str
    style: str
    context: Optional[Dict]


class RapperAgent:
    """Agent for generating rap verses."""

    def __init__(self):
        """Initialize the rapper agent."""
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=settings.openai_api_key,
            streaming=False
        )

        # Define tools
        self.tools = [
            search_tool.search,
            search_tool.get_rapper_info,
            style_tool.get_style,
            style_tool.search_styles
        ]

        # Bind tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Create the graph
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """
        Create the LangGraph for the rapper agent.

        Returns:
            StateGraph: The created graph
        """
        # Define the nodes
        def rapper_node(state: RapperState):
            """Process the state and generate a response."""
            # Generate a response
            response = self.llm_with_tools.invoke(state["messages"])

            return {"messages": [response]}

        # Create the tool node
        tool_node = ToolNode(tools=self.tools)

        # Create the graph
        graph_builder = StateGraph(RapperState)

        # Add nodes
        graph_builder.add_node("rapper", rapper_node)
        graph_builder.add_node("tools", tool_node)

        # Add edges
        graph_builder.add_conditional_edges(
            "rapper",
            tools_condition,
            {
                "tools": "tools",
                END: END
            }
        )
        graph_builder.add_edge("tools", "rapper")

        # Set the entry point
        graph_builder.set_entry_point("rapper")

        # Compile the graph
        return graph_builder.compile()

    async def generate_verse(
        self,
        rapper_name: str,
        opponent_name: str,
        style: str,
        round_number: int,
        previous_verses: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate a rap verse.

        Args:
            rapper_name: Name of the rapper
            opponent_name: Name of the opponent
            style: Rap style
            round_number: Current round number
            previous_verses: Previous verses in the battle

        Returns:
            str: Generated verse
        """
        try:
            # Create the system message
            system_message = self._create_system_message(
                rapper_name, opponent_name, style, round_number, previous_verses
            )

            # Create the human message
            human_message = HumanMessage(
                content=f"Generate a rap verse for {rapper_name} in the style of {style} for round {round_number}."
            )

            # Initialize the state
            initial_state = {
                "messages": [system_message, human_message],
                "rapper_name": rapper_name,
                "opponent_name": opponent_name,
                "style": style,
                "context": None
            }

            # Run the graph
            result = await self.graph.ainvoke(initial_state)

            # Extract the verse from the result
            verse_content = self._extract_verse(result["messages"])

            return verse_content
        except Exception:
            return "Error generating verse."

    def _create_system_message(
        self,
        rapper_name: str,
        opponent_name: str,
        style: str,
        round_number: int,
        previous_verses: Optional[List[Dict]] = None
    ) -> SystemMessage:
        """
        Create a system message for the rapper agent.

        Args:
            rapper_name: Name of the rapper
            opponent_name: Name of the opponent
            style: Rap style
            round_number: Current round number
            previous_verses: Previous verses in the battle

        Returns:
            SystemMessage: The created system message
        """
        system_content = f"""You are {rapper_name}, a skilled rapper in a rap battle against {opponent_name}.
Your task is to create an impressive rap verse in the style of {style} for round {round_number} of the battle.

Follow these guidelines:
1. Research {rapper_name} style, background, and facts using the search tools
2. Research the {style} rap style using the style tools
3. Create a verse that incorporates elements of {style} and {rapper_name}'s persona
4. Make references to real facts about {rapper_name} and diss {opponent_name}
5. Keep the verse between 8-16 lines
6. Be creative, authentic, and true to the style
"""

        # Add context about previous verses if available
        if previous_verses:
            system_content += "\nPrevious verses in this battle:\n"
            for verse in previous_verses:
                system_content += f"\n{verse['rapper_name']}:\n{verse['content']}\n"

        return SystemMessage(content=system_content)

    def _extract_verse(self, messages: List[AnyMessage]) -> str:
        """
        Extract the verse from the agent's messages.

        Args:
            messages: List of messages

        Returns:
            str: Extracted verse
        """
        try:
            # Get the last message
            last_message = messages[-1]

            # Extract the content
            content = last_message.content

            # Clean up the content
            # Remove any explanations or notes before or after the verse
            if "```" in content:
                # Extract content between code blocks
                verse_parts = content.split("```")
                if len(verse_parts) >= 3:
                    return verse_parts[1].strip()

            # If no code blocks, try to extract the verse directly
            lines = content.split("\n")
            verse_lines = []
            in_verse = False

            for line in lines:
                if line.strip() and not line.startswith("I'll") and not line.startswith("Here's") and not line.startswith("This is"):
                    in_verse = True

                if in_verse:
                    verse_lines.append(line)

            extracted_verse = "\n".join(verse_lines).strip()

            # If we couldn't extract anything meaningful, return the raw content
            if not extracted_verse:
                return content

            return extracted_verse
        except Exception:
            return "Error extracting verse."


# Create a rapper agent instance
rapper_agent = RapperAgent()
