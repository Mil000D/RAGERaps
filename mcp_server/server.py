"""
MCP Server for RAGERaps application.

This server provides tools for Wikipedia and Tavily search capabilities.
It uses python-dotenv to load environment variables from a .env file.
"""
import os
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_tavily import TavilySearch

# Load environment variables from .env file
# First try to load from the current directory
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Try to load from the parent directory (project root)
    env_path = Path('..') / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)


# Create the MCP server
mcp = FastMCP("RAGERaps Search Tools", port=8888)

# Initialize Wikipedia tool
wikipedia_wrapper = WikipediaAPIWrapper(
    top_k_results=5,
    doc_content_chars_max=4000
)
wikipedia_tool = WikipediaQueryRun(api_wrapper=wikipedia_wrapper)

@mcp.tool()
async def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia for information about a topic.

    Args:
        query: The search query

    Returns:
        str: Information from Wikipedia about the query
    """
    try:
        # Use the Wikipedia tool to search
        result = wikipedia_tool.run(query)

        if not result or result.strip() == "":
            return f"No information found on Wikipedia for: {query}"

        return result
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"

@mcp.tool()
async def search_rapper_wikipedia(rapper_name: str) -> str:
    """
    Search Wikipedia specifically for information about a rapper.

    Args:
        rapper_name: Name of the rapper

    Returns:
        str: Biographical information about the rapper from Wikipedia
    """
    try:
        # Construct a more specific query for rappers
        query = f"{rapper_name} rapper hip hop artist biography"

        # Use the Wikipedia tool to search
        result = wikipedia_tool.run(query)

        if not result or result.strip() == "":
            return f"No information found on Wikipedia for rapper: {rapper_name}"

        return result
    except Exception as e:
        return f"Error searching Wikipedia for rapper: {str(e)}"

# Initialize Tavily search tool
tavily_search = TavilySearch(
    max_results=3,  # Reduced from 5 to 3 to limit results
    topic="general",
    include_raw_content=True,
    include_domains=None,
    exclude_domains=None
)

@mcp.tool()
async def search_internet(query: str) -> str:
    """
    Search the internet for information using Tavily.

    Args:
        query: The search query

    Returns:
        str: Search results from the internet
    """
    try:
        # Use the Tavily tool to search
        result = await tavily_search.ainvoke({"query": query})

        if not result:
            return f"No information found for: {query}"

        # Process the result to limit token count
        # Convert to string if it's not already
        result_str = str(result)

        # Limit the result to approximately 8000 tokens (roughly 32000 characters)
        max_chars = 10000
        if len(result_str) > max_chars:
            result_str = result_str[:max_chars] + "... [Content truncated due to length]"

        return result_str
    except Exception as e:
        return f"Error searching the internet: {str(e)}"

@mcp.tool()
async def search_rapper_info(rapper_name: str) -> str:
    """
    Search the internet for information about a specific rapper using Tavily.

    Args:
        rapper_name: Name of the rapper

    Returns:
        str: Information about the rapper from the internet
    """
    try:
        # Construct a more specific query for rappers
        query = f"{rapper_name} rapper biography facts style"

        # Use the Tavily tool to search
        result = await tavily_search.ainvoke({"query": query})

        if not result:
            return f"No information found for rapper: {rapper_name}"

        # Process the result to limit token count
        # Convert to string if it's not already
        result_str = str(result)

        # Limit the result to approximately 8000 tokens (roughly 32000 characters)
        max_chars = 10000
        if len(result_str) > max_chars:
            result_str = result_str[:max_chars] + "... [Content truncated due to length]"

        return result_str
    except Exception as e:
        return f"Error searching for rapper information: {str(e)}"

if __name__ == "__main__":
    # Check if Tavily API key is set
    if not os.environ.get("TAVILY_API_KEY"):
        print("Warning: TAVILY_API_KEY environment variable is not set.")
        print("The Tavily search tools will not work without an API key.")

    # Run the MCP server with streamable-http transport
    mcp.run(transport="streamable-http")
