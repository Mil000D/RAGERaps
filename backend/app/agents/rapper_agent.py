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
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.config import settings
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

        # Initialize tools
        self.tools = []

        # # Add style tools
        # self.tools.extend([
        #     style_tool.get_style,
        #     style_tool.search_styles
        # ])

        # Initialize MCP tools (will be loaded asynchronously)
        self.mcp_tools = []

        # Bind tools to the LLM (will be updated with MCP tools)
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Create the graph with the tools we have available
        # This ensures we have a working graph even if MCP tools fail to load
        self.graph = self._create_graph()

    async def _init_mcp_tools(self, server_url="http://localhost:8888/mcp"):
        """
        Initialize MCP tools from the server.

        Args:
            server_url: URL of the MCP server

        Returns:
            bool: True if MCP tools were successfully initialized, False otherwise
        """
        try:
            print(f"Connecting to MCP server at {server_url}...")

            # Connect to the MCP server
            client = MultiServerMCPClient(
                {
                    "search": {
                        "url": server_url,
                        "transport": "streamable_http",
                    }
                }
            )

            # Get all tools from the server
            print("Fetching tools from MCP server...")
            self.mcp_tools = await client.get_tools()
            print(f"Retrieved {len(self.mcp_tools)} tools from MCP server")

            if not self.mcp_tools:
                print("Warning: No tools were retrieved from the MCP server")
                return False

            # Add MCP tools to the tools list
            self.tools.extend(self.mcp_tools)

            # Update the LLM with tools
            self.llm_with_tools = self.llm.bind_tools(self.tools)

            # Create the graph with updated tools
            self.graph = self._create_graph()

            print("MCP tools successfully initialized and integrated")
            return True
        except Exception as e:
            print(f"Error initializing MCP tools: {str(e)}")
            print("The application will continue with style tools only")
            # We already created the graph in __init__ with style tools only
            return False

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
            # Initialize MCP tools if not already initialized
            if self.graph is None:
                print("Graph not initialized. Creating graph with available tools...")
                # Create the graph with whatever tools we have available
                self.graph = self._create_graph()

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
        except Exception as e:
            print(f"Error generating verse: {str(e)}")
            return f"Error generating verse: {str(e)}"

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
        # Create system content with biographical attack instructions as a standard feature
        system_content = f"""You are {rapper_name}, a skilled rapper in a rap battle against {opponent_name}.
Your task is to create an impressive rap verse in the style of {style} for round {round_number} of the battle.

Follow these guidelines:
1. Research {rapper_name} style, background, and facts using the available search tools.
   Use any of these tools if they are available:
   - search_internet or search_wikipedia for general information
   - search_rapper_info or search_rapper_wikipedia specifically for rapper information
   - search for general web searches
2. Research the {style} rap style using the style tools (get_style, search_styles)
3. Create a verse that incorporates elements of {style} and {rapper_name}'s persona
4. IMPORTANT: Research {opponent_name}'s biography, career, and personal life using search tools.
5. Include specific personal attacks and disses based on real facts about {opponent_name}'s life, career mistakes, controversies, or personal details.
6. Reference at least 2-3 specific biographical details about {opponent_name} in your disses.
7. Make your disses clever, creative, and authentic to {style} rap style.
8. Keep the verse between 12-16 lines to allow room for detailed disses.
"""

        # Add common ending
        system_content += """
Remember to stay in character throughout the verse and make it sound authentic to the style.
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

# Define an initialization function that will be called from the application startup
async def initialize_rapper_agent():
    """Initialize the rapper agent with MCP tools."""
    await rapper_agent._init_mcp_tools()

# Note: This function will be called during application startup
# We don't call it here to avoid the "no running event loop" error
