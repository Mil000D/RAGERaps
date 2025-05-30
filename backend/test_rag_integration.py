#!/usr/bin/env python3
"""
Test script for tool-based RAG integration in the parallel workflow system.
"""
import asyncio
import logging
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.parallel_workflow import execute_battle_round_parallel
from app.tools.artist_retrieval_tool import artist_retrieval_tool
from app.services.vector_store_service import vector_store_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_artist_retrieval_tool():
    """Test the artist retrieval tool functionality."""
    logger.info("Testing artist retrieval tool...")

    try:
        # Test collection info
        collection_info = await vector_store_service.get_collection_info()
        logger.info(f"Collection info: {collection_info}")

        if not collection_info.get("exists", False):
            logger.warning("Artists collection does not exist. Please run the data pipeline first.")
            return False

        # Test artist retrieval tool
        result = await artist_retrieval_tool._arun(
            artist_name="Eminem",
            style="hardcore rap",
            k=3,
            include_similar=True
        )

        logger.info("Artist retrieval tool test completed")
        logger.info(f"Result length: {len(result)} characters")
        logger.info(f"Result preview: {result[:200]}...")

        # Test with a different artist
        result2 = await artist_retrieval_tool._arun(
            artist_name="Jay-Z",
            style="east coast rap",
            k=2,
            include_similar=False
        )

        logger.info("Second artist retrieval test completed")
        logger.info(f"Result2 length: {len(result2)} characters")

        return True

    except Exception as e:
        logger.error(f"Error testing artist retrieval tool: {str(e)}")
        return False


async def test_parallel_workflow_with_tools():
    """Test the parallel workflow with tool-based RAG integration."""
    logger.info("Testing parallel workflow with tool-based RAG...")

    try:
        # Test the tool-based approach
        result = await execute_battle_round_parallel(
            round_id="test_round_1",
            rapper1_name="Eminem",
            rapper2_name="Jay-Z",
            style1="hardcore rap",
            style2="east coast rap",
            round_number=1
        )

        logger.info("Tool-based RAG battle completed successfully!")
        logger.info(f"Verses generated: {len(result.get('verses', []))}")
        logger.info(f"Judgment available: {'judgment' in result}")

        # Print verse samples
        for i, verse in enumerate(result.get('verses', []), 1):
            rapper = verse.get('rapper_name', f'Rapper {i}')
            content = verse.get('verse_content', '')[:100] + "..."
            logger.info(f"{rapper} verse preview: {content}")

        # Print judgment
        judgment = result.get('judgment', {})
        if judgment:
            winner = judgment.get('winner', 'Unknown')
            logger.info(f"Battle winner: {winner}")

        return True

    except Exception as e:
        logger.error(f"Error testing parallel workflow: {str(e)}")
        return False


async def main():
    """Main test function."""
    logger.info("Starting tool-based RAG integration tests...")

    # Test artist retrieval tool
    tool_test_passed = await test_artist_retrieval_tool()

    if tool_test_passed:
        # Test parallel workflow
        workflow_test_passed = await test_parallel_workflow_with_tools()

        if workflow_test_passed:
            logger.info("All tests passed! Tool-based RAG integration is working correctly.")
        else:
            logger.error("Parallel workflow test failed.")
    else:
        logger.error("Artist retrieval tool test failed.")

    logger.info("Test completed.")


if __name__ == "__main__":
    asyncio.run(main())
