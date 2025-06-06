"""
MCP Server for RAGERaps application.

This server provides tools for Wikipedia and Tavily search capabilities.
It uses python-dotenv to load environment variables from a .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_tavily import TavilySearch


env_path = Path(".") / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    env_path = Path("..") / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)


mcp = FastMCP("RAGERaps Search Tools", port=8888)


wikipedia_wrapper = WikipediaAPIWrapper(top_k_results=5, doc_content_chars_max=4000)
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
        result = wikipedia_tool.run(query)

        if not result or result.strip() == "":
            return f"No information found on Wikipedia for: {query}"

        return result
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"


tavily_search = TavilySearch(
    max_results=3,
    topic="general",
    include_raw_content=True,
    include_domains=None,
    exclude_domains=None,
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
        result = await tavily_search.ainvoke({"query": query})

        if not result:
            return f"No information found for: {query}"

        result_str = str(result)

        max_chars = 10000
        if len(result_str) > max_chars:
            result_str = (
                result_str[:max_chars] + "... [Content truncated due to length]"
            )

        return result_str
    except Exception as e:
        return f"Error searching the internet: {str(e)}"


if __name__ == "__main__":
    if not os.environ.get("TAVILY_API_KEY"):
        print("Warning: TAVILY_API_KEY environment variable is not set.")
        print("The Tavily search tools will not work without an API key.")

    mcp.run(transport="streamable-http")
