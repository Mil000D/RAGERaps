#!/usr/bin/env python
"""
Mock LangGraph for visualization without requiring API keys.

This script provides a mock LangGraph that can be used for visualization
without requiring API keys or other environment variables.
"""
import sys
import os
from pathlib import Path

# Add necessary directories to sys.path to allow running with uv run
visualization_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(visualization_dir, '..'))

# Add both the backend directory and the parent of backend to sys.path
sys.path.insert(0, backend_dir)  # For importing app module
sys.path.insert(0, os.path.dirname(backend_dir))  # For importing backend module

from typing import Dict, List, Optional, TypedDict, Annotated
import operator
from langgraph.graph import END, StateGraph


class MockRapperVerseState(TypedDict):
    """State for a rapper's verse generation."""
    rapper_name: str
    opponent_name: str
    style: str
    round_number: int
    previous_verses: Optional[List[Dict]]
    verse_content: Optional[str]


class MockBattleRoundState(TypedDict):
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


async def mock_rapper1_verse_node(state: MockBattleRoundState) -> MockBattleRoundState:
    """Generate a verse for rapper 1."""
    return {
        "verses": [
            {
                "rapper_name": state["rapper1_name"],
                "content": "Mock verse content for rapper 1"
            }
        ]
    }


async def mock_rapper2_verse_node(state: MockBattleRoundState) -> MockBattleRoundState:
    """Generate a verse for rapper 2."""
    return {
        "verses": [
            {
                "rapper_name": state["rapper2_name"],
                "content": "Mock verse content for rapper 2"
            }
        ]
    }


async def mock_judge_round_node(state: MockBattleRoundState) -> MockBattleRoundState:
    """Judge the round based on both verses."""
    return {
        "judgment": {
            "winner": state["rapper1_name"],
            "feedback": "Mock judgment feedback"
        }
    }


def create_mock_battle_round_graph() -> StateGraph:
    """
    Create a mock StateGraph for visualization purposes.

    This graph mimics the structure of the battle round graph but doesn't
    require any API keys or environment variables.

    Returns:
        StateGraph: The compiled graph for visualization
    """
    # Create the graph
    graph = StateGraph(MockBattleRoundState)

    # Add nodes
    graph.add_node("rapper1_verse", mock_rapper1_verse_node)
    graph.add_node("rapper2_verse", mock_rapper2_verse_node)
    graph.add_node("judge_round", mock_judge_round_node)

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


# Create a singleton instance of the mock battle round graph
mock_battle_round_graph = create_mock_battle_round_graph()


if __name__ == "__main__":
    # Import visualization tools
    from visualization.visualize_graphs import visualize_graph
    
    # Visualize the mock graph
    output_path = visualize_graph(
        graph=mock_battle_round_graph,
        output_filename="mock_battle_round_graph"
    )
    
    print(f"Mock graph visualization saved to {output_path}")
