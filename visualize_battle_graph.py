#!/usr/bin/env python
"""
Battle Graph Visualization Script

This script visualizes the battle graph from the RAGERaps application.
It uses the LangGraph's built-in Mermaid visualization capabilities to generate
an image of the battle workflow graph.
"""
import argparse
from IPython.display import Image, display
import sys
from pathlib import Path

# Add the project root to the Python path to allow importing from the app
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.app.agents.parallel_workflow import battle_round_graph


def visualize_battle_graph():
    """
    Visualize the battle graph using Mermaid.
    
    This function generates a PNG image of the battle workflow graph
    and displays it using IPython's display functionality.
    """
    # Get the graph and generate a Mermaid PNG image
    graph_image = battle_round_graph.get_graph().draw_mermaid_png()
    
    # Display the image
    display(Image(graph_image))
    
    # Save the image to a file
    with open("battle_graph.png", "wb") as f:
        f.write(graph_image)
    
    print("Battle graph visualization saved to 'battle_graph.png'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize the RAGERaps battle graph")
    args = parser.parse_args()
    
    visualize_battle_graph()
