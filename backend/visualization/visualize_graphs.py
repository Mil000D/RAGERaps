"""
Visualization script for LangGraph workflows.

This script provides functions to visualize any LangGraph workflow as a Mermaid diagram
and save it as a PNG file.
"""
import os
import asyncio
from pathlib import Path
from typing import Optional

from langchain_core.runnables.graph_mermaid import draw_mermaid_png, MermaidDrawMethod
from langgraph.graph import StateGraph


def visualize_graph(
    graph: StateGraph,
    output_filename: str,
    output_dir: Optional[str] = None,
    background_color: str = "white",
    padding: int = 10,
) -> str:
    """
    Visualize a LangGraph StateGraph and save it as a PNG file.
    
    Args:
        graph: The LangGraph StateGraph to visualize
        output_filename: The filename for the output PNG (without extension)
        output_dir: The directory to save the PNG to (defaults to visualization directory)
        background_color: Background color of the image (default: "white")
        padding: Padding around the image (default: 10)
        
    Returns:
        str: The path to the saved PNG file
    """
    # Determine the output directory
    if output_dir is None:
        output_dir = Path(__file__).parent
    else:
        output_dir = Path(output_dir)
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Full output path
    output_path = output_dir / f"{output_filename}.png"
    
    # Get the Mermaid syntax from the graph
    mermaid_syntax = graph.get_graph().to_mermaid()
    
    # Generate the PNG visualization
    png_data = draw_mermaid_png(
        mermaid_syntax=mermaid_syntax,
        output_file_path=str(output_path),
        draw_method=MermaidDrawMethod.API,
        background_color=background_color,
        padding=padding,
        max_retries=3,
        retry_delay=1.0,
    )
    
    print(f"Graph visualization saved to {output_path}")
    return str(output_path)


async def visualize_all_graphs():
    """
    Visualize all LangGraph workflows in the project.
    
    This function imports all graphs from the project and generates
    visualizations for each one.
    """
    # Import the graphs
    from app.agents.parallel_workflow import battle_round_graph
    
    # Visualize the battle round graph
    visualize_graph(
        graph=battle_round_graph,
        output_filename="battle_round_graph"
    )
    
    # Try to import and visualize rapper agent graph if it exists
    try:
        from app.agents.rapper_agent import rapper_agent
        if hasattr(rapper_agent, "graph") and rapper_agent.graph:
            visualize_graph(
                graph=rapper_agent.graph,
                output_filename="rapper_agent_graph"
            )
    except (ImportError, AttributeError):
        print("Rapper agent graph not available for visualization")


if __name__ == "__main__":
    # Run the async function
    asyncio.run(visualize_all_graphs())
