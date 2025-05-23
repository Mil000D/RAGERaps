#!/usr/bin/env python
"""
Example of how to use LangGraph visualization in a Jupyter notebook or interactive environment.

This script demonstrates how to visualize LangGraph workflows in a Jupyter notebook
or other interactive environment.
"""
import sys
import os

# Add necessary directories to sys.path to allow running with uv run
visualization_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(visualization_dir, '..'))

# Add both the backend directory and the parent of backend to sys.path
sys.path.insert(0, backend_dir)  # For importing app module
sys.path.insert(0, os.path.dirname(backend_dir))  # For importing backend module

from IPython.display import Image, display

# Import statements for graphs - will be imported inside the function with error handling


def display_graph_visualization():
    """
    Display a visualization of the battle round graph.

    This function:
    1. Gets the Mermaid PNG from the graph
    2. Displays it using IPython's display function

    Returns:
        None
    """
    try:
        # Import the graph from the parallel workflow
        from app.agents.parallel_workflow import battle_round_graph

        # Get the PNG data from the graph
        png_data = battle_round_graph.get_graph().draw_mermaid_png()

        # Display the image
        display(Image(png_data))
    except Exception as e:
        print(f"Error displaying graph visualization: {e}")
        print("\nTo visualize graphs in a notebook without setting up API keys, you need to:")
        print("1. Set up the required API keys in your environment")
        print("2. Or use the CLI tool with a specific graph: uv run backend/visualization/cli.py --graph <graph_path>")


# Example usage in a Jupyter notebook:
#
# ```python
# from visualization.notebook_example import display_graph_visualization
#
# # Display the graph visualization
# display_graph_visualization()
# ```

if __name__ == "__main__":
    print("This script is intended to be imported in a Jupyter notebook or interactive environment.")
    print("Example usage:")
    print("from visualization.notebook_example import display_graph_visualization")
    print("display_graph_visualization()")
