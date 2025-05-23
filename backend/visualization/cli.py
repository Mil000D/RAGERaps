"""
Command-line interface for visualizing LangGraph workflows.

This script provides a command-line interface to generate visualizations
for LangGraph workflows in the project.
"""
import argparse
import asyncio
import importlib
from pathlib import Path

from visualize_graphs import visualize_graph


async def main():
    """
    Main entry point for the CLI.
    """
    parser = argparse.ArgumentParser(
        description="Generate visualizations for LangGraph workflows"
    )
    
    parser.add_argument(
        "--graph",
        type=str,
        help="The module path to the graph to visualize (e.g., app.agents.parallel_workflow.battle_round_graph)",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="The filename for the output PNG (without extension)",
    )
    
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="The directory to save the PNG to (defaults to visualization directory)",
    )
    
    parser.add_argument(
        "--bg-color",
        type=str,
        default="white",
        help="Background color of the image (default: white)",
    )
    
    parser.add_argument(
        "--padding",
        type=int,
        default=10,
        help="Padding around the image (default: 10)",
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Visualize all known graphs in the project",
    )
    
    args = parser.parse_args()
    
    if args.all:
        # Import and run the visualize_all_graphs function
        from visualize_graphs import visualize_all_graphs
        await visualize_all_graphs()
        return
    
    if not args.graph:
        parser.error("Either --graph or --all must be specified")
    
    # Import the graph from the specified module
    module_path, attr_name = args.graph.rsplit(".", 1)
    module = importlib.import_module(module_path)
    graph = getattr(module, attr_name)
    
    # Determine the output filename
    output_filename = args.output or attr_name
    
    # Visualize the graph
    visualize_graph(
        graph=graph,
        output_filename=output_filename,
        output_dir=args.dir,
        background_color=args.bg_color,
        padding=args.padding,
    )


if __name__ == "__main__":
    asyncio.run(main())
