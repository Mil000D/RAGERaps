"""
Tool for retrieving rap styles from the database.
"""
from typing import Dict, List, Optional

from langchain_core.tools import tool

from app.db.repositories.style_repo import style_repository


class StyleTool:
    """Tool for retrieving rap styles."""
    
    @tool
    async def get_style(self, style_name: str) -> str:
        """
        Get information about a specific rap style.

        Args:
            style_name: Name of the rap style

        Returns:
            str: Information about the rap style
        """
        style_data = await style_repository.get_style_by_name(style_name)

        if not style_data:
            raise ValueError(f"Rap style '{style_name}' not found.")

        return self._format_style(style_data)

    @tool
    async def search_styles(self, query: str) -> str:
        """
        Search for rap styles based on a query.

        Args:
            query: Search query

        Returns:
            str: Matching rap styles
        """
        styles = await style_repository.search_styles(query)

        if not styles:
            return f"No rap styles found matching: {query}"

        formatted_styles = "### Matching Rap Styles\n\n"
        for style in styles:
            formatted_styles += self._format_style(style) + "\n\n"

        return formatted_styles

    def _format_style(self, style_data: Dict) -> str:
        """
        Format style data into a readable string.

        Args:
            style_data: Style data

        Returns:
            str: Formatted style information
        """
        style_name = style_data.get("style_name", "Unknown Style")
        description = style_data.get("description", "No description available")
        examples = style_data.get("examples", [])

        formatted_text = f"**{style_name}**\n\n"
        formatted_text += f"{description}\n\n"

        if examples:
            formatted_text += "**Examples:**\n"
            for i, example in enumerate(examples, 1):
                formatted_text += f"{i}. {example}\n"

        return formatted_text


# Create a style tool instance
style_tool = StyleTool()
