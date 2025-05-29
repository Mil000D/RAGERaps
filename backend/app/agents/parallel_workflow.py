"""
Parallel execution workflow for rap battle agents using LangGraph.
"""
from typing import Annotated, Dict, List, Optional, TypedDict
import operator

from langgraph.graph import END, StateGraph

from app.agents.judge_agent import judge_agent
from app.agents.rapper_agent import rapper_agent
from app.services.data_cache_service import RapperCacheData


class RapperVerseState(TypedDict):
    """State for a rapper's verse generation."""
    rapper_name: str
    opponent_name: str
    style: str
    round_number: int
    previous_verses: Optional[List[Dict]]
    verse_content: Optional[str]


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
    judgment: Optional[Dict]
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
        verse_content = f"""Yo, I'm {state["rapper1_name"]}, stepping to the mic,
Facing off with {state["rapper2_name"]}, gonna win this fight.
Round {state["round_number"]}, and I'm bringing the heat,
My rhymes are fire, can't be beat.

This {state["style1"]} flow is what I do best,
Put your skills to the ultimate test.
When it comes to rap, I'm at the top,
Watch me shine while your flow flops."""

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
        verse_content = f"""I'm {state["rapper2_name"]}, the best in the game,
After this battle, nothing will be the same.
{state["rapper1_name"]} thinks they can step to me?
But my {state["style2"]} skills are legendary.

Round {state["round_number"]}, I'm bringing my A-game,
When I'm done, you'll remember my name.
My flow is smooth, my rhymes are tight,
This battle is mine, I'll win tonight."""

    # Return the verse in the format expected by the verses list
    return {
        "verses": [
            {
                "rapper_name": state["rapper2_name"],
                "content": verse_content
            }
        ]
    }


async def judge_round_node(state: BattleRoundState) -> BattleRoundState:
    """Judge the round based on both verses."""
    # Extract verses for both rappers
    rapper1_verse = None
    rapper2_verse = None

    for verse in state["verses"]:
        if verse["rapper_name"] == state["rapper1_name"]:
            rapper1_verse = verse["content"]
        elif verse["rapper_name"] == state["rapper2_name"]:
            rapper2_verse = verse["content"]

    # Ensure we have both verses
    if not rapper1_verse or not rapper2_verse:
        raise ValueError("Missing verses for judgment")

    try:
        # Judge the round
        winner, feedback = await judge_agent.judge_round(
            rapper1_name=state["rapper1_name"],
            rapper1_verse=rapper1_verse,
            rapper1_style=state["style1"],
            rapper2_name=state["rapper2_name"],
            rapper2_verse=rapper2_verse,
            rapper2_style=state["style2"]
        )
    except Exception:
        # If there's an error, use a default judgment
        import random
        winner = state["rapper1_name"] if random.random() < 0.5 else state["rapper2_name"]
        feedback = f"""
Analysis of {state["rapper1_name"]}'s verse:
{state["rapper1_name"]} delivered a verse with interesting wordplay and flow.

Analysis of {state["rapper2_name"]}'s verse:
{state["rapper2_name"]} showed creativity and technical skill in their delivery.

Comparison:
Both rappers showed skill, but {winner} had slightly better delivery and impact.

Winner: {winner}
{winner} wins this round with a more impressive overall performance.
"""

    # Return the judgment
    return {
        "judgment": {
            "winner": winner,
            "feedback": feedback
        }
    }


def create_battle_round_graph() -> StateGraph:
    """
    Create a StateGraph for parallel execution of a battle round.

    This graph executes the rapper verse generation in parallel and then
    judges the round once both verses are available.

    Returns:
        StateGraph: The compiled graph for battle round execution
    """
    # Create the graph
    graph = StateGraph(BattleRoundState)

    # Add nodes
    graph.add_node("rapper1_verse", rapper1_verse_node)
    graph.add_node("rapper2_verse", rapper2_verse_node)
    graph.add_node("judge_round", judge_round_node)

    # Set up parallel execution of rapper verse generation
    # Both rapper1_verse and rapper2_verse run in parallel from the START node
    graph.set_entry_point("rapper1_verse")
    graph.set_entry_point("rapper2_verse")

    # Add edges from both rapper nodes to the judge node
    # The judge node will only execute when both rapper nodes have completed
    graph.add_edge("rapper1_verse", "judge_round")
    graph.add_edge("rapper2_verse", "judge_round")

    # Add edge from judge to END
    graph.add_edge("judge_round", END)

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
    Execute a battle round with parallel agent execution.

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
        Dict: The final state with verses and judgment
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
        "judgment": None,
        "cached_data": cached_data
    }

    # Execute the graph
    # Use the ainvoke method for asynchronous execution
    final_state = await battle_round_graph.ainvoke(initial_state)

    # Ensure cached data is preserved in the final state
    if cached_data and "cached_data" not in final_state:
        final_state["cached_data"] = cached_data

    return final_state
