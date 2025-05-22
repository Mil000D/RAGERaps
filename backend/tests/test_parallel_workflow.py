"""
Test the parallel workflow implementation.
"""
import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the settings before importing modules that use it
sys.modules['app.core.config'] = MagicMock()
sys.modules['app.core.config'].settings = MagicMock(
    openai_api_key="test_openai_key",
    tavily_api_key="test_tavily_key"
)

from app.agents.parallel_workflow import execute_battle_round_parallel


class TestParallelWorkflow(unittest.TestCase):
    """Test the parallel workflow implementation."""

    @patch('app.agents.rapper_agent.rapper_agent.generate_verse')
    @patch('app.agents.judge_agent.judge_agent.judge_round')
    async def test_parallel_execution(self, mock_judge_round, mock_generate_verse):
        """Test that the parallel execution works correctly."""
        # Mock the rapper agent's generate_verse method
        mock_generate_verse.side_effect = AsyncMock(side_effect=[
            "Rapper 1 verse content",  # First rapper's verse
            "Rapper 2 verse content"   # Second rapper's verse
        ])

        # Mock the judge agent's judge_round method
        mock_judge_round.return_value = AsyncMock(return_value=("Rapper 1", "Judgment feedback"))

        # Execute the parallel workflow
        result = await execute_battle_round_parallel(
            round_id="test_round_id",
            rapper1_name="Rapper 1",
            rapper2_name="Rapper 2",
            style1="Style 1",
            style2="Style 2",
            round_number=1,
            previous_verses=None
        )

        # Verify the result structure
        self.assertIn("verses", result)
        self.assertIn("judgment", result)

        # Verify that both verses were generated
        verses = result["verses"]
        self.assertEqual(len(verses), 2)

        # Find rapper1's verse
        rapper1_verse = next((v for v in verses if v["rapper_name"] == "Rapper 1"), None)
        self.assertIsNotNone(rapper1_verse)
        self.assertEqual(rapper1_verse["content"], "Rapper 1 verse content")

        # Find rapper2's verse
        rapper2_verse = next((v for v in verses if v["rapper_name"] == "Rapper 2"), None)
        self.assertIsNotNone(rapper2_verse)
        self.assertEqual(rapper2_verse["content"], "Rapper 2 verse content")

        # Verify judgment
        judgment = result["judgment"]
        self.assertEqual(judgment["winner"], "Rapper 1")
        self.assertEqual(judgment["feedback"], "Judgment feedback")


def run_async_test(test_case):
    """Run an async test case."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_case)


if __name__ == "__main__":
    # Run the test
    test = TestParallelWorkflow()
    run_async_test(test.test_parallel_execution())
    print("All tests passed!")
