# RAGERaps MCP Server

This directory contains an MCP (Model, Completion, and Prompt) server implementation for the RAGERaps application. The server provides tools for Wikipedia and Tavily search capabilities that can be used by LangChain agents.

## Features

- **Wikipedia Search**: Search Wikipedia for information about topics and rappers
- **Tavily Search**: Search the internet for general information and rapper-specific details

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your API keys:

```bash
# For Tavily search
export TAVILY_API_KEY=your_tavily_api_key
```

## Running the Server

Start the MCP server:

```bash
python server.py
```

By default, the server runs on port 3000. You can specify a different port using the `--port` argument:

```bash
python server.py --port 8000
```

## Using with LangChain

To use this MCP server with LangChain, you'll need to connect to it using the `MultiServerMCPClient` from the `langchain-mcp-adapters` package:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

client = MultiServerMCPClient(
    {
        "search": {
            "url": "http://localhost:3000/mcp",
            "transport": "streamable_http",
        }
    }
)
tools = await client.get_tools()
agent = create_react_agent("openai:gpt-4o", tools)
```

## Available Tools

1. `search_wikipedia`: Search Wikipedia for information about a topic
2. `search_rapper_wikipedia`: Search Wikipedia specifically for information about a rapper
3. `search_internet`: Search the internet for information using Tavily
4. `search_rapper_info`: Search the internet for information about a specific rapper using Tavily
