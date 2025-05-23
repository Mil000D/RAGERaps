#!/usr/bin/env python
"""
Example of how to use LangGraph visualization in a Jupyter notebook or interactive environment.

This script demonstrates how to visualize LangGraph workflows in a Jupyter notebook
or other interactive environment.
"""
import sys
import os

# Add the parent directory to sys.path to allow running with uv run
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from IPython.display import Image, display

# Import the graph from the parallel workflow
from app.agents.parallel_workflow import battle_round_graph


def display_graph_visualization():
    """
    Display a visualization of the battle round graph.

    This function:
    1. Gets the Mermaid PNG from the graph
    2. Displays it using IPython's display function

    Returns:
        None
    """
    # Get the PNG data from the graph
    png_data = battle_round_graph.get_graph().draw_mermaid_png()

    # Display the image
    display(Image(png_data))


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
