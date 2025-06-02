"""
Parallel execution workflow for rap battle agents using LangGraph with tool-based RAG integration.
"""
from typing import Annotated, Dict, List, Optional, TypedDict
import operator

from langgraph.graph import END, StateGraph

from app.agents.rapper_agent import rapper_agent
from app.services.data_cache_service import RapperCacheData


class BattleRoundState(TypedDict):
    """State for a battle round with parallel verse generation."""
    round_id: str
    rapper1_name: str
    rapper2_name: str
    style1: str
    style2: str
    round_number: int
    previous_verses: Optional[List[Dict]]
    # Use operator.add to combine results from parallel execution
    verses: Annotated[List[Dict], operator.add]
    cached_data: Optional[Dict[str, RapperCacheData]]


async def rapper1_verse_node(state: BattleRoundState) -> BattleRoundState:
    """Generate a verse for rapper 1."""
    try:
        verse_content = await rapper_agent.generate_verse(
            rapper_name=state["rapper1_name"],
            opponent_name=state["rapper2_name"],
            style=state["style1"],
            round_number=state["round_number"],
            previous_verses=state["previous_verses"],
            cached_data=state.get("cached_data")
        )
    except Exception:
        # If there's an error, use a default verse
        verse_content = "Error generating verse."

    # Return the verse in the format expected by the verses list
    return {
        "verses": [
            {
                "rapper_name": state["rapper1_name"],
                "content": verse_content
            }
        ]
    }


async def rapper2_verse_node(state: BattleRoundState) -> BattleRoundState:
    """Generate a verse for rapper 2."""
    try:
        verse_content = await rapper_agent.generate_verse(
            rapper_name=state["rapper2_name"],
            opponent_name=state["rapper1_name"],
            style=state["style2"],
            round_number=state["round_number"],
            previous_verses=state["previous_verses"],
            cached_data=state.get("cached_data")
        )
    except Exception:
        # If there's an error, use a default verse
        verse_content = "Error generating verse."


    # Return the verse in the format expected by the verses list
    return {
        "verses": [
            {
                "rapper_name": state["rapper2_name"],
                "content": verse_content
            }
        ]
    }


# Removed judge_round_node - battles now end after verse generation
# Users can manually judge rounds using the API endpoints


def create_battle_round_graph() -> StateGraph:
    """
    Create a StateGraph for parallel execution of a battle round with tool-based RAG integration.

    This graph executes the rapper verse generation in parallel (with each agent able to use
    retrieval tools), and then ends. Users can manually judge rounds using the API endpoints.

    Returns:
        StateGraph: The compiled graph for battle round execution
    """
    # Create the graph
    graph = StateGraph(BattleRoundState)

    # Add nodes for verse generation only
    graph.add_node("rapper1_verse", rapper1_verse_node)
    graph.add_node("rapper2_verse", rapper2_verse_node)

    # Set up parallel execution of rapper verse generation
    # Both rapper1_verse and rapper2_verse run in parallel from the START node
    graph.set_entry_point("rapper1_verse")
    graph.set_entry_point("rapper2_verse")

    # Both rapper nodes end directly (no automatic judging)
    graph.add_edge("rapper1_verse", END)
    graph.add_edge("rapper2_verse", END)

    # Compile the graph
    return graph.compile()


# Create a singleton instance of the battle round graph
battle_round_graph = create_battle_round_graph()


async def execute_battle_round_parallel(
    round_id: str,
    rapper1_name: str,
    rapper2_name: str,
    style1: str,
    style2: str,
    round_number: int,
    previous_verses: Optional[List[Dict]] = None,
    cached_data: Optional[Dict[str, RapperCacheData]] = None
) -> Dict:
    """
    Execute a battle round with parallel agent execution and tool-based RAG integration.

    This function generates verses for both rappers in parallel but does not automatically
    judge the round. Users can manually judge rounds using the API endpoints.

    Args:
        round_id: ID of the round
        rapper1_name: Name of the first rapper
        rapper2_name: Name of the second rapper
        style1: Style of the first rapper
        style2: Style of the second rapper
        round_number: Round number
        previous_verses: Previous verses for context
        cached_data: Cached data for rappers to avoid redundant API calls

    Returns:
        Dict: The final state with verses (no automatic judgment)
    """
    # Initialize the state
    initial_state = {
        "round_id": round_id,
        "rapper1_name": rapper1_name,
        "rapper2_name": rapper2_name,
        "style1": style1,
        "style2": style2,
        "round_number": round_number,
        "previous_verses": previous_verses,
        "verses": [],
        "cached_data": cached_data
    }

    # Execute the graph
    # Use the ainvoke method for asynchronous execution
    final_state = await battle_round_graph.ainvoke(initial_state)

    # Ensure cached data is preserved in the final state
    if cached_data and "cached_data" not in final_state:
        final_state["cached_data"] = cached_data

    return final_state
