"""
Web search tool using Tavily.
"""
from typing import Dict, List, Optional

from langchain_core.tools import tool
from tavily import TavilyClient

from app.core.config import settings


class SearchTool:
    """Web search tool using Tavily."""
    
    def __init__(self):
        """Initialize the search tool."""
        self.client = TavilyClient(api_key=settings.tavily_api_key)
    
    @tool
    async def search(self, query: str) -> str:
        """
        Search the web for information about a rapper or style.
        
        Args:
            query: Search query
            
        Returns:
            str: Search results as a formatted string
        """
        # Execute search
        response = await self._async_search(query)
        
        # Format results
        formatted_results = self._format_results(response.get("results", []))
        
        return formatted_results
    
    async def _async_search(self, query: str) -> Dict:
        """
        Execute an asynchronous search.
        
        Args:
            query: Search query
            
        Returns:
            Dict: Search response
        """
        # Use the Tavily client to search
        response = self.client.search(query=query, search_depth="advanced", max_results=5)
        return response
    
    def _format_results(self, results: List[Dict]) -> str:
        """
        Format search results into a readable string.
        
        Args:
            results: List of search result items
            
        Returns:
            str: Formatted results
        """
        if not results:
            return "No information found."
        
        formatted_text = "### Search Results\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            content = result.get("content", "No content")
            url = result.get("url", "No URL")
            
            formatted_text += f"**{i}. {title}**\n"
            formatted_text += f"{content}\n"
            formatted_text += f"Source: {url}\n\n"
        
        return formatted_text
    
    @tool
    async def get_rapper_info(self, rapper_name: str) -> str:
        """
        Get information about a specific rapper.
        
        Args:
            rapper_name: Name of the rapper
            
        Returns:
            str: Information about the rapper
        """
        query = f"{rapper_name} rapper biography facts style"
        response = await self._async_search(query)
        
        # Format results
        formatted_results = self._format_results(response.get("results", []))
        
        return formatted_results


# Create a search tool instance
search_tool = SearchTool()
