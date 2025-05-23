#!/usr/bin/env python
"""
Visualization script for LangGraph workflows.

This script generates Mermaid diagram visualizations of the LangGraph workflows
and saves them as PNG files in the visualization directory.
"""
import os
import asyncio
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow running with uv run
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_core.runnables.graph_mermaid import draw_mermaid_png, MermaidDrawMethod

# Import the graph from the parallel workflow
from app.agents.parallel_workflow import battle_round_graph
from app.agents.rapper_agent import RapperAgent


async def generate_graph_visualizations():
    """
    Generate visualizations for all LangGraph workflows in the project.

    This function:
    1. Gets the Mermaid syntax from each graph
    2. Generates PNG visualizations using draw_mermaid_png
    3. Saves the visualizations to the visualization directory
    """
    # Create visualization directory if it doesn't exist
    visualization_dir = Path(__file__).parent
    os.makedirs(visualization_dir, exist_ok=True)

    # Generate visualization for battle round graph
    print("Generating visualization for battle round graph...")

    # Get the Mermaid syntax from the graph
    mermaid_syntax = battle_round_graph.get_graph().to_mermaid()

    # Generate the PNG visualization
    png_data = draw_mermaid_png(
        mermaid_syntax=mermaid_syntax,
        output_file_path=str(visualization_dir / "battle_round_graph.png"),
        draw_method=MermaidDrawMethod.API,
        background_color="white",
        padding=10,
        max_retries=3,
        retry_delay=1.0,
    )

    print(f"Battle round graph visualization saved to {visualization_dir / 'battle_round_graph.png'}")

    # Initialize rapper agent to get its graph
    rapper_agent = RapperAgent()

    # Check if rapper agent has a graph
    if hasattr(rapper_agent, "graph") and rapper_agent.graph:
        print("Generating visualization for rapper agent graph...")

        # Get the Mermaid syntax from the graph
        rapper_mermaid_syntax = rapper_agent.graph.get_graph().to_mermaid()

        # Generate the PNG visualization
        rapper_png_data = draw_mermaid_png(
            mermaid_syntax=rapper_mermaid_syntax,
            output_file_path=str(visualization_dir / "rapper_agent_graph.png"),
            draw_method=MermaidDrawMethod.API,
            background_color="white",
            padding=10,
            max_retries=3,
            retry_delay=1.0,
        )

        print(f"Rapper agent graph visualization saved to {visualization_dir / 'rapper_agent_graph.png'}")


if __name__ == "__main__":
    # Run the async function
    asyncio.run(generate_graph_visualizations())
