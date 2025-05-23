#!/usr/bin/env python
"""
Visualization script for LangGraph workflows.

This script generates and saves Mermaid diagram images of LangGraph workflows.
It uses LangGraph's built-in visualization capabilities to create PNG images
with customizable settings.

Dependencies:
    - langchain-core>=0.3.0
    - langgraph (if not already installed: uv add langgraph)

Usage:
    uv run visualize_graph.py [--output FILENAME]

Example:
    uv run visualize_graph.py --output custom_graph_name
"""

import os
import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

# Check for required dependencies
try:
    from langchain_core.runnables.graph_mermaid import draw_mermaid_png, MermaidDrawMethod
except ImportError:
    print("Error: Required dependencies not found.")
    print("Please install the required packages:")
    print("  uv add langchain-core>=0.3.0 langgraph")
    sys.exit(1)

# Import the graph from the existing implementation
try:
    from backend.app.agents.parallel_workflow import battle_round_graph, create_battle_round_graph
except ImportError as e:
    print(f"Error importing graph: {e}")
    print("Make sure you're running this script from the project root directory.")
    print("If the module is not found, check that the backend package is in your PYTHONPATH.")
    print("You can add it with: export PYTHONPATH=$PYTHONPATH:$(pwd)")
    sys.exit(1)


def check_graph_visualization_support(graph) -> bool:
    """
    Check if the graph supports visualization methods.

    Args:
        graph: The LangGraph to check

    Returns:
        bool: True if the graph supports visualization, False otherwise
    """
    try:
        # Check if the graph has the necessary methods for visualization
        mermaid_graph = graph.get_graph()
        _ = mermaid_graph.to_mermaid()
        return True
    except (AttributeError, TypeError) as e:
        print(f"Error: The graph does not support visualization: {e}")
        print("Make sure you're using a compatible version of LangGraph.")
        return False


def create_visualization_dir() -> Path:
    """
    Create a visualization directory if it doesn't exist.

    Returns:
        Path: Path to the visualization directory
    """
    vis_dir = Path("visualization")
    vis_dir.mkdir(exist_ok=True)
    return vis_dir


def save_graph_visualization(
    graph,
    output_filename: str = "battle_round_graph",
    background_color: str = "white",
    padding: int = 10,
) -> Optional[Path]:
    """
    Generate and save a Mermaid diagram of the graph.

    Args:
        graph: The LangGraph to visualize
        output_filename: Base filename for the output (without extension)
        background_color: Background color for the diagram
        padding: Padding around the diagram in pixels

    Returns:
        Optional[Path]: Path to the saved image file, or None if visualization failed
    """
    # Check if the graph supports visualization
    if not check_graph_visualization_support(graph):
        return None

    vis_dir = create_visualization_dir()
    output_path = vis_dir / f"{output_filename}.png"

    try:
        # Get the Mermaid syntax from the graph
        mermaid_syntax = graph.get_graph().to_mermaid()

        # Generate and save the PNG
        draw_mermaid_png(
            mermaid_syntax=mermaid_syntax,
            output_file_path=str(output_path),
            draw_method=MermaidDrawMethod.API,
            background_color=background_color,
            padding=padding,
            max_retries=3,
            retry_delay=1.0,
        )

        print(f"Graph visualization saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error generating graph visualization: {e}")
        print("This might be due to missing dependencies or network issues.")
        print("Make sure you have an internet connection for the Mermaid API.")
        return None


async def main(output_filename: Optional[str] = None):
    """
    Main function to generate and save graph visualizations.

    Args:
        output_filename: Custom filename for the output (without extension)

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    success = False

    try:
        # Use the existing graph instance
        filename = output_filename or "battle_round_graph"
        print(f"Generating visualization for battle_round_graph...")
        output_path = save_graph_visualization(
            graph=battle_round_graph,
            output_filename=filename,
            background_color="white",
            padding=10,
        )

        if output_path:
            print(f"✅ Successfully generated graph visualization: {output_path}")
            success = True
        else:
            print("❌ Failed to generate graph visualization for battle_round_graph")

        # Optionally, create a new graph instance and visualize it
        # This can be useful if you want to visualize different configurations
        print("\nGenerating visualization of a fresh graph instance...")
        fresh_graph = create_battle_round_graph()
        fresh_output_path = save_graph_visualization(
            graph=fresh_graph,
            output_filename=f"{filename}_fresh",
            background_color="white",
            padding=10,
        )

        if fresh_output_path:
            print(f"✅ Successfully generated fresh graph visualization: {fresh_output_path}")
            success = True
        else:
            print("❌ Failed to generate graph visualization for fresh graph instance")

    except Exception as e:
        print(f"❌ Error in visualization process: {e}")
        return 1

    if success:
        print("\n✨ Visualization process completed with at least one successful generation.")
        return 0
    else:
        print("\n❌ Visualization process failed. No visualizations were generated.")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate LangGraph visualizations")
    parser.add_argument(
        "--output",
        type=str,
        help="Custom filename for the output (without extension)",
        default=None
    )

    args = parser.parse_args()

    # Run the async main function
    exit_code = asyncio.run(main(args.output))
    exit(exit_code)
