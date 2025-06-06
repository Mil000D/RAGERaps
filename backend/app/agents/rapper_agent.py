"""
Rapper agent implementation using LangGraph.
"""

from typing import Annotated, Dict, List, Optional, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.config import settings
from app.services.prompt_service import prompt_service
from app.tools.artist_retrieval_tool import artist_retrieval_tool


class RapperState(TypedDict):
    """State for the rapper agent."""

    messages: Annotated[List[AnyMessage], add_messages]
    rapper_name: str
    opponent_name: str
    style: str
    round_number: int
    is_first_round: bool


class RapperAgent:
    """Agent for generating rap verses."""

    def __init__(self):
        """Initialize the rapper agent."""

        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.9,
            api_key=settings.openai_api_key,
            streaming=False,
        )

        self.memory = MemorySaver()

        self.tools = [artist_retrieval_tool]

        self.mcp_tools = []

        self.llm_with_tools = self.llm.bind_tools(self.tools)

        self.graph = None

        self._create_initial_graph()

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

            client = MultiServerMCPClient(
                {
                    "search": {
                        "url": server_url,
                        "transport": "streamable_http",
                    }
                }
            )

            print("Fetching tools from MCP server...")
            self.mcp_tools = await client.get_tools()
            print(f"Retrieved {len(self.mcp_tools)} tools from MCP server")

            if not self.mcp_tools:
                print("Warning: No tools were retrieved from the MCP server")
                return False

            self.tools.extend(self.mcp_tools)
            print(
                f"Added {len(self.mcp_tools)} MCP tools to rapper agent: {[getattr(tool, 'name', 'unknown') for tool in self.mcp_tools]}"
            )

            self.llm_with_tools = self.llm.bind_tools(self.tools)
            print(f"LLM now bound with {len(self.tools)} total tools")

            self.graph = self._create_graph()
            print(f"Graph recreated with {len(self.tools)} tools available to ToolNode")

            print("MCP tools successfully initialized and integrated")
            return True
        except Exception as e:
            print(f"Error initializing MCP tools: {str(e)}")
            print("The application will continue with style tools only")

            return False

    def _create_initial_graph(self):
        """Create initial graph with current tools for fallback."""
        if not self.graph:
            self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """
        Create the LangGraph for the rapper agent.

        Returns:
            StateGraph: The created graph
        """

        def rapper_node(state: RapperState):
            """Process the state and generate a response."""

            response = self.llm_with_tools.invoke(state["messages"])

            return {"messages": [response]}

        tool_node = ToolNode(tools=self.tools)

        graph_builder = StateGraph(RapperState)

        graph_builder.add_node("rapper", rapper_node)
        graph_builder.add_node("tools", tool_node)

        graph_builder.add_conditional_edges(
            "rapper",
            tools_condition,
            {"tools": "tools", END: END},
        )

        graph_builder.add_edge("tools", "rapper")

        graph_builder.set_entry_point("rapper")

        return graph_builder.compile(checkpointer=self.memory)

    def _get_thread_id(self, rapper_name: str, opponent_name: str, style: str) -> str:
        """
        Generate a consistent thread ID for conversation memory.

        Args:
            rapper_name: Name of the rapper
            opponent_name: Name of the opponent
            style: Rap style

        Returns:
            str: Thread ID for memory storage
        """

        battle_context = (
            f"{rapper_name.lower()}_{opponent_name.lower()}_{style.lower()}"
        )
        return f"battle_{hash(battle_context) % 1000000}"

    def _get_available_tools_info(self) -> str:
        """
        Get information about available tools for the LLM.

        Returns:
            str: Formatted string describing available tools
        """
        tool_descriptions = []

        tool_descriptions.append(
            "- retrieve_artist_data: Get artist lyrics and style data from vector store. "
            "IMPORTANT: Always pass the 'style' parameter when you know the rap style."
        )

        for tool in self.mcp_tools:
            tool_name = getattr(tool, "name", "unknown")
            tool_desc = getattr(tool, "description", "No description available")
            tool_descriptions.append(f"- {tool_name}: {tool_desc}")

        if tool_descriptions:
            tools_info = "\n".join(tool_descriptions)
            return f"You have access to the following tools:\n{tools_info}\n\nUse these tools to gather information about the rappers when needed. LangChain's caching will automatically handle repeated requests."

        return ""

    def get_current_tools_debug(self) -> str:
        """Debug method to show current tools available."""
        tool_list = []
        for tool in self.tools:
            tool_name = getattr(tool, "name", "unknown")
            tool_list.append(tool_name)
        return f"Current tools in self.tools: {tool_list} (Total: {len(self.tools)})"

    async def generate_verse(
        self,
        rapper_name: str,
        opponent_name: str,
        style: str,
        round_number: int,
        previous_verses: Optional[List[Dict]] = None,
    ) -> str:
        """
        Generate a rap verse using available tools for artist data retrieval.

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
            if self.graph is None:
                print("Graph not initialized. Creating graph with available tools...")

                self.graph = self._create_graph()

            is_first_round = round_number == 1

            thread_id = self._get_thread_id(rapper_name, opponent_name, style)
            config = {"configurable": {"thread_id": thread_id}}

            system_message = self._create_system_message(
                rapper_name,
                opponent_name,
                style,
                round_number,
                previous_verses,
                available_tools=self._get_available_tools_info(),
            )

            human_template = prompt_service.get_prompt(
                "rapper", "human_message", "template"
            )
            human_message = HumanMessage(
                content=human_template.format(
                    rapper_name=rapper_name, style=style, round_number=round_number
                )
            )

            initial_state = {
                "messages": [system_message, human_message],
                "rapper_name": rapper_name,
                "opponent_name": opponent_name,
                "style": style,
                "round_number": round_number,
                "is_first_round": is_first_round,
            }

            result = await self.graph.ainvoke(initial_state, config)

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
        available_tools: Optional[str] = None,
    ) -> SystemMessage:
        """
        Create a system message for the rapper agent using the prompt service.

        Args:
            rapper_name: Name of the rapper
            opponent_name: Name of the opponent
            style: Rap style
            round_number: Current round number
            previous_verses: Previous verses in the battle
            available_tools: Information about available tools

        Returns:
            SystemMessage: The created system message
        """

        has_biographical_info = False
        biographical_info = None
        opponent_biographical_info = None

        system_content = prompt_service.get_rapper_system_message(
            rapper_name=rapper_name,
            opponent_name=opponent_name,
            style=style,
            round_number=round_number,
            has_biographical_info=has_biographical_info,
            biographical_info=biographical_info,
            opponent_biographical_info=opponent_biographical_info,
            is_first_round=(round_number == 1),
            previous_verses=previous_verses,
        )

        if available_tools:
            system_content += f"\n\nAVAILABLE TOOLS:\n{available_tools}"

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
            last_message = messages[-1]

            content = last_message.content

            if "```" in content:
                verse_parts = content.split("```")
                if len(verse_parts) >= 3:
                    return verse_parts[1].strip()

            lines = content.split("\n")
            verse_lines = []
            in_verse = False

            for line in lines:
                if (
                    line.strip()
                    and not line.startswith("I'll")
                    and not line.startswith("Here's")
                    and not line.startswith("This is")
                ):
                    in_verse = True

                if in_verse:
                    verse_lines.append(line)

            extracted_verse = "\n".join(verse_lines).strip()

            if not extracted_verse:
                return content

            return extracted_verse
        except Exception:
            return "Error extracting verse."


rapper_agent = RapperAgent()


async def initialize_rapper_agent():
    """Initialize the rapper agent with MCP tools."""
    await rapper_agent._init_mcp_tools()
