# LangGraph Visualization Tools

This directory contains tools for visualizing LangGraph workflows in the RAGERaps project.

## Available Scripts

### 1. `visualize_graphs.py`

A utility module that provides functions to visualize LangGraph StateGraphs and save them as PNG files.

**Usage as a module:**

```python
from visualization.visualize_graphs import visualize_graph
from app.agents.parallel_workflow import battle_round_graph

# Visualize a specific graph
visualize_graph(
    graph=battle_round_graph,
    output_filename="my_graph"
)
```

**Usage as a script:**

```bash
# Using uv run
uv run backend/visualization/visualize_graphs.py

# Or using python directly
python -m visualization.visualize_graphs
```

This will visualize all known graphs in the project.

### 2. `generate_graph.py`

A script that specifically visualizes the battle round graph from the parallel workflow.

**Usage:**

```bash
# Using uv run
uv run backend/visualization/generate_graph.py

# Or using python directly
python -m visualization.generate_graph
```

### 3. `cli.py`

A command-line interface for visualizing specific graphs.

**Usage:**

```bash
# Using uv run - Visualize a specific graph
uv run backend/visualization/cli.py --graph app.agents.parallel_workflow.battle_round_graph

# Using uv run - Visualize a specific graph with custom options
uv run backend/visualization/cli.py --graph app.agents.parallel_workflow.battle_round_graph --output custom_name --bg-color lightblue --padding 20

# Using uv run - Visualize all known graphs
uv run backend/visualization/cli.py --all

# Or using python directly
python -m visualization.cli --graph app.agents.parallel_workflow.battle_round_graph
```

## Examples

To visualize the battle round graph:

```bash
# Using uv run
uv run backend/visualization/cli.py --graph app.agents.parallel_workflow.battle_round_graph

# Or using python directly
python -m visualization.cli --graph app.agents.parallel_workflow.battle_round_graph
```

This will generate a PNG file in the visualization directory named `battle_round_graph.png`.

## Requirements

These scripts require the following dependencies:

- langchain-core
- langgraph

These dependencies are already included in the project's requirements.

## Using Without API Keys

If you want to visualize graphs without setting up API keys, you can use the mock graph:

```bash
# Visualize a mock graph
uv run backend/visualization/mock_graph.py
```

This will generate a visualization of a mock battle round graph that has the same structure as the real one but doesn't require any API keys or environment variables.
