"""
Rapper agent implementation using LangGraph.
"""
from typing import Annotated, Dict, List, Optional, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.config import settings
from app.services.data_cache_service import data_cache_service, RapperCacheData


class RapperState(TypedDict):
    """State for the rapper agent."""

    messages: Annotated[List[AnyMessage], add_messages]
    rapper_name: str
    opponent_name: str
    style: str
    context: Optional[Dict]
    cached_data: Optional[Dict[str, RapperCacheData]]
    round_number: int
    is_first_round: bool


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

    async def _get_or_fetch_rapper_data(
        self,
        rapper_name: str,
        opponent_name: str,
        style: str,
        is_first_round: bool,
        cached_data: Optional[Dict[str, RapperCacheData]] = None
    ) -> Dict[str, RapperCacheData]:
        """
        Get or fetch rapper data, using cache when available.

        Args:
            rapper_name: Name of the rapper
            opponent_name: Name of the opponent
            style: Rap style
            is_first_round: Whether this is the first round
            cached_data: Existing cached data

        Returns:
            Dict[str, RapperCacheData]: Cached data for both rappers
        """
        result_cache = cached_data or {}

        # If not first round and we have cached data, return it
        if not is_first_round and cached_data:
            return result_cache

        # For first round, fetch data if not already cached
        for name in [rapper_name, opponent_name]:
            cache_key = name.lower().strip()

            # Check if we already have cached data for this rapper
            if cache_key in result_cache:
                continue

            # Try to get from cache service
            cached_rapper_data = await data_cache_service.get_rapper_data(name)

            if cached_rapper_data:
                result_cache[cache_key] = cached_rapper_data
            else:
                # Need to fetch data using MCP tools
                if is_first_round and self.mcp_tools:
                    rapper_data = await self._fetch_rapper_data_with_tools(name)
                    result_cache[cache_key] = rapper_data

                    # Cache the data for future use
                    await data_cache_service.cache_rapper_data(
                        rapper_name=name,
                        biographical_info=rapper_data.biographical_info,
                        wikipedia_info=rapper_data.wikipedia_info,
                        internet_search_info=rapper_data.internet_search_info,
                        style_info=rapper_data.style_info
                    )
                else:
                    # Create empty cache data if no tools available
                    result_cache[cache_key] = RapperCacheData(rapper_name=name)

        return result_cache

    async def _fetch_rapper_data_with_tools(self, rapper_name: str) -> RapperCacheData:
        """
        Fetch rapper data using MCP tools.

        Args:
            rapper_name: Name of the rapper

        Returns:
            RapperCacheData: Fetched data
        """
        rapper_data = RapperCacheData(rapper_name=rapper_name)

        try:
            # Try to find the search tools
            wikipedia_tool = None
            rapper_wikipedia_tool = None
            internet_tool = None
            rapper_info_tool = None

            for tool in self.mcp_tools:
                tool_name = getattr(tool, 'name', '')
                if tool_name == 'search_wikipedia':
                    wikipedia_tool = tool
                elif tool_name == 'search_rapper_wikipedia':
                    rapper_wikipedia_tool = tool
                elif tool_name == 'search_internet':
                    internet_tool = tool
                elif tool_name == 'search_rapper_info':
                    rapper_info_tool = tool

            # Fetch Wikipedia information
            if rapper_wikipedia_tool:
                try:
                    wikipedia_result = await rapper_wikipedia_tool.ainvoke({"rapper_name": rapper_name})
                    rapper_data.wikipedia_info = str(wikipedia_result)
                except Exception as e:
                    print(f"Error fetching Wikipedia data for {rapper_name}: {e}")

            # Fetch internet search information
            if rapper_info_tool:
                try:
                    internet_result = await rapper_info_tool.ainvoke({"rapper_name": rapper_name})
                    rapper_data.internet_search_info = str(internet_result)
                except Exception as e:
                    print(f"Error fetching internet data for {rapper_name}: {e}")

            # Combine biographical info
            bio_parts = []
            if rapper_data.wikipedia_info:
                bio_parts.append(f"Wikipedia: {rapper_data.wikipedia_info}")
            if rapper_data.internet_search_info:
                bio_parts.append(f"Internet: {rapper_data.internet_search_info}")

            rapper_data.biographical_info = "\n\n".join(bio_parts) if bio_parts else None

        except Exception as e:
            print(f"Error fetching data for {rapper_name}: {e}")

        return rapper_data

    async def generate_verse(
        self,
        rapper_name: str,
        opponent_name: str,
        style: str,
        round_number: int,
        previous_verses: Optional[List[Dict]] = None,
        cached_data: Optional[Dict[str, RapperCacheData]] = None
    ) -> str:
        """
        Generate a rap verse.

        Args:
            rapper_name: Name of the rapper
            opponent_name: Name of the opponent
            style: Rap style
            round_number: Current round number
            previous_verses: Previous verses in the battle
            cached_data: Cached data for rappers (used to avoid redundant API calls)

        Returns:
            str: Generated verse
        """
        try:
            # Initialize MCP tools if not already initialized
            if self.graph is None:
                print("Graph not initialized. Creating graph with available tools...")
                # Create the graph with whatever tools we have available
                self.graph = self._create_graph()

            # Determine if this is the first round
            is_first_round = round_number == 1

            # Get or fetch rapper data using cache
            rapper_cache_data = await self._get_or_fetch_rapper_data(
                rapper_name=rapper_name,
                opponent_name=opponent_name,
                style=style,
                is_first_round=is_first_round,
                cached_data=cached_data
            )

            # Create the system message with cached data
            system_message = self._create_system_message(
                rapper_name, opponent_name, style, round_number, previous_verses, rapper_cache_data
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
                "context": None,
                "cached_data": rapper_cache_data,
                "round_number": round_number,
                "is_first_round": is_first_round
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
        previous_verses: Optional[List[Dict]] = None,
        cached_data: Optional[Dict[str, RapperCacheData]] = None
    ) -> SystemMessage:
        """
        Create a system message for the rapper agent.

        Args:
            rapper_name: Name of the rapper
            opponent_name: Name of the opponent
            style: Rap style
            round_number: Current round number
            previous_verses: Previous verses in the battle
            cached_data: Cached data for rappers

        Returns:
            SystemMessage: The created system message
        """
        # Create system content with biographical attack instructions as a standard feature
        system_content = f"""You are {rapper_name}, a skilled rapper in a rap battle against {opponent_name}.
Your task is to create an impressive rap verse in the style of {style} for round {round_number} of the battle.

Follow these guidelines:
1. Create a verse that incorporates elements of {style} and {rapper_name}'s persona
2. Include specific personal attacks and disses based on real facts about {opponent_name}'s life, career mistakes, controversies, or personal details.
3. Reference at least 2-3 specific biographical details about {opponent_name} in your disses.
4. Reference at least 2-3 specific facts about {rapper_name}'s life, career, or personal details to support your verse.
5. Make your disses clever, creative, and authentic to {style} rap style.
6. Keep the verse between 12-16 lines to allow room for detailed disses.
"""

        # Add cached biographical information if available
        if cached_data:
            rapper_key = rapper_name.lower().strip()
            opponent_key = opponent_name.lower().strip()

            if rapper_key in cached_data and cached_data[rapper_key].biographical_info:
                system_content += f"\n\nInformation about {rapper_name}:\n{cached_data[rapper_key].biographical_info}\n"

            if opponent_key in cached_data and cached_data[opponent_key].biographical_info:
                system_content += f"\nInformation about {opponent_name}:\n{cached_data[opponent_key].biographical_info}\n"
        else:
            # Fallback for first round when tools might be needed
            system_content += f"""
7. If this is the first round, research {rapper_name} style, background, and facts using the available search tools.
   Use any of these tools if they are available:
   - search_internet or search_wikipedia for general information
   - search_rapper_info or search_rapper_wikipedia specifically for rapper information
8. If this is the first round, research {opponent_name}'s biography, career, and personal life using search tools.
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
