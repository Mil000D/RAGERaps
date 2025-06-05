"""
Centralized prompt management service for RAGERaps application.
"""

import tomllib

from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache

from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    """Model for prompt templates with variable substitution."""

    template: str

    def format(self, **kwargs) -> str:
        """
        Format the template with provided variables.

        Args:
            **kwargs: Variables to substitute in the template

        Returns:
            str: Formatted template
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(
                f"Missing required variable '{missing_var}' for prompt template"
            )


class PromptConfig(BaseModel):
    """Configuration model for all prompts."""

    battle_prompts: Dict[str, Any] = Field(default_factory=dict)
    rapper_prompts: Dict[str, Any] = Field(default_factory=dict)
    evaluation_prompts: Dict[str, Any] = Field(default_factory=dict)
    system_prompts: Dict[str, Any] = Field(default_factory=dict)


class PromptService:
    """Service for managing and retrieving prompts from TOML configuration files."""

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize the prompt service.

        Args:
            prompts_dir: Directory containing TOML prompt files
        """
        self.prompts_dir = (
            prompts_dir or Path(__file__).parent.parent.parent / "prompts"
        )
        self._config: Optional[PromptConfig] = None
        self._load_prompts()

    def _load_prompts(self) -> None:
        """Load all prompt configurations from TOML files."""
        try:
            config_data = {}

            # Load each TOML file
            toml_files = {
                "battle_prompts": "battle_prompts.toml",
                "rapper_prompts": "rapper_prompts.toml",
                "evaluation_prompts": "evaluation_prompts.toml",
                "system_prompts": "system_prompts.toml",
            }

            for key, filename in toml_files.items():
                file_path = self.prompts_dir / filename
                if file_path.exists():
                    with open(file_path, "rb") as f:
                        config_data[key] = tomllib.load(f)
                else:
                    print(f"Warning: Prompt file {filename} not found at {file_path}")
                    config_data[key] = {}

            self._config = PromptConfig(**config_data)
            print(f"Successfully loaded prompts from {self.prompts_dir}")

        except Exception as e:
            print(f"Error loading prompt configurations: {e}")
            # Initialize with empty config as fallback
            self._config = PromptConfig()

    @lru_cache(maxsize=128)
    def get_prompt(
        self, category: str, key: str, subkey: Optional[str] = None
    ) -> PromptTemplate:
        """
        Get a prompt template by category and key.

        Args:
            category: Prompt category (battle, rapper, evaluation, system)
            key: Prompt key within the category
            subkey: Optional subkey for nested prompts

        Returns:
            PromptTemplate: The requested prompt template

        Raises:
            ValueError: If prompt is not found
        """
        if not self._config:
            raise ValueError("Prompt configuration not loaded")

        # Map category names to config attributes
        category_map = {
            "battle": self._config.battle_prompts,
            "rapper": self._config.rapper_prompts,
            "evaluation": self._config.evaluation_prompts,
            "system": self._config.system_prompts,
        }

        if category not in category_map:
            raise ValueError(f"Unknown prompt category: {category}")

        category_data = category_map[category]

        try:
            if subkey:
                template_data = category_data[key][subkey]
            else:
                template_data = category_data[key]

            # Handle both string templates and dict with template key
            if isinstance(template_data, str):
                return PromptTemplate(template=template_data)
            elif isinstance(template_data, dict) and "template" in template_data:
                return PromptTemplate(**template_data)
            else:
                raise ValueError(
                    f"Invalid template format for {category}.{key}.{subkey or ''}"
                )

        except KeyError:
            raise ValueError(f"Prompt not found: {category}.{key}.{subkey or ''}")

    def get_rapper_system_message(
        self,
        rapper_name: str,
        opponent_name: str,
        style: str,
        round_number: int,
        has_biographical_info: bool = False,
        biographical_info: Optional[str] = None,
        opponent_biographical_info: Optional[str] = None,
        is_first_round: bool = False,
        previous_verses: Optional[List[Dict]] = None,
    ) -> str:
        """
        Get a complete system message for the rapper agent.

        Args:
            rapper_name: Name of the rapper
            opponent_name: Name of the opponent
            style: Rap style
            round_number: Current round number
            has_biographical_info: Whether biographical info is available
            biographical_info: Biographical info about the rapper
            opponent_biographical_info: Biographical info about the opponent
            is_first_round: Whether this is the first round
            previous_verses: Previous verses in the battle

        Returns:
            str: Complete formatted system message
        """
        # Get base template
        base_template = self.get_prompt("rapper", "system_message", "base_template")
        system_content = base_template.format(
            rapper_name=rapper_name,
            opponent_name=opponent_name,
            style=style,
            round_number=round_number,
        )

        # Add biographical information if available
        if has_biographical_info and biographical_info and opponent_biographical_info:
            bio_template = self.get_prompt(
                "rapper", "system_message", "biographical_section"
            )
            system_content += bio_template.format(
                rapper_name=rapper_name,
                biographical_info=biographical_info,
                opponent_name=opponent_name,
                opponent_biographical_info=opponent_biographical_info,
            )
        elif is_first_round:
            # Add first round research instructions
            research_template = self.get_prompt(
                "rapper", "system_message", "first_round_research"
            )
            system_content += research_template.format(
                rapper_name=rapper_name, opponent_name=opponent_name
            )

        # Add common ending
        ending_template = self.get_prompt("rapper", "system_message", "common_ending")
        system_content += ending_template.template

        # Add previous verses context if available
        if previous_verses:
            context_template = self.get_prompt(
                "rapper", "system_message", "previous_verses_context"
            )

            # Format previous verses
            formatted_verses = []
            for verse in previous_verses:
                verse_format = self.get_prompt(
                    "system", "formatting", "rapper_verse_format"
                )
                formatted_verses.append(
                    verse_format.format(
                        rapper_name=verse["rapper_name"], content=verse["content"]
                    )
                )

            separator = self.get_prompt("system", "formatting", "verse_separator")
            previous_verses_formatted = separator.template.join(formatted_verses)

            system_content += context_template.format(
                previous_verses_formatted=previous_verses_formatted
            )

        return system_content

    def get_judge_system_prompt(self) -> str:
        """
        Get the system prompt for the judge agent.

        Returns:
            str: Judge system prompt
        """
        template = self.get_prompt("evaluation", "judge_system_prompt", "template")
        return template.template

    def get_judge_input_template(self, **kwargs) -> str:
        """
        Get formatted input template for judge.

        Args:
            **kwargs: Variables for template formatting

        Returns:
            str: Formatted judge input
        """
        template = self.get_prompt("evaluation", "judge_input_template", "template")
        return template.format(**kwargs)


# Create a global prompt service instance
prompt_service = PromptService()
