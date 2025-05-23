# RAGERaps Battle Graph Visualization

This tool visualizes the battle workflow graph from the RAGERaps application.

## Requirements

- Python 3.8+
- uv (Python package manager)
- IPython
- LangGraph

## Installation

No installation is required. The script uses the existing codebase.

## Usage

You can run the visualization script using `uv run`:

```bash
uv run visualize_battle_graph.py
```

This will:
1. Generate a visualization of the battle graph
2. Display it (if running in an environment that supports IPython display)
3. Save the image to `battle_graph.png` in the current directory

## Alternative Usage

You can also run the script as a module using:

```bash
uv run -m visualize_battle_graph
```

## How It Works

The script uses LangGraph's built-in Mermaid visualization capabilities to generate a PNG image of the battle workflow graph. It accesses the `battle_round_graph` from the `backend.app.agents.parallel_workflow` module and calls the `get_graph().draw_mermaid_png()` method to generate the visualization.
