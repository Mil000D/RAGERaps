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
python -m visualization.visualize_graphs
```

This will visualize all known graphs in the project.

### 2. `generate_graph.py`

A script that specifically visualizes the battle round graph from the parallel workflow.

**Usage:**

```bash
python -m visualization.generate_graph
```

### 3. `cli.py`

A command-line interface for visualizing specific graphs.

**Usage:**

```bash
# Visualize a specific graph
python -m visualization.cli --graph app.agents.parallel_workflow.battle_round_graph

# Visualize a specific graph with custom options
python -m visualization.cli --graph app.agents.parallel_workflow.battle_round_graph --output custom_name --bg-color lightblue --padding 20

# Visualize all known graphs
python -m visualization.cli --all
```

## Examples

To visualize the battle round graph:

```bash
python -m visualization.cli --graph app.agents.parallel_workflow.battle_round_graph
```

This will generate a PNG file in the visualization directory named `battle_round_graph.png`.

## Requirements

These scripts require the following dependencies:

- langchain-core
- langgraph

These dependencies are already included in the project's requirements.
