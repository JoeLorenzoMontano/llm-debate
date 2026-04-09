"""Base class for debate modes."""

from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..orchestrator import Turn
    from ..pr_context import PRContext


class DebateMode(ABC):
    """Abstract base class for debate interaction modes."""

    @abstractmethod
    def get_initial_prompt(self, topic: str, cli_name: str, pr_context: Optional["PRContext"] = None) -> str:
        """
        Generate the initial prompt for the first CLI.

        Args:
            topic: The debate topic
            cli_name: Name of the CLI (claude or codex)
            pr_context: Optional PR context to include

        Returns:
            Initial prompt string
        """
        pass

    @abstractmethod
    def get_response_prompt(self, topic: str, cli_name: str, conversation_history: List["Turn"], pr_context: Optional["PRContext"] = None) -> str:
        """
        Generate prompt for responding to previous turns.

        Args:
            topic: The debate topic
            cli_name: Name of the CLI
            conversation_history: List of previous turns
            pr_context: Optional PR context to include

        Returns:
            Response prompt string
        """
        pass

    @abstractmethod
    def get_mode_instructions(self, cli_name: str) -> str:
        """
        Get mode-specific instructions for this CLI.

        Args:
            cli_name: Name of the CLI

        Returns:
            Mode instructions string
        """
        pass

    def format_history(self, history: List["Turn"], max_rounds: int = 3) -> str:
        """
        Format conversation history for inclusion in prompts.

        Args:
            history: List of turns
            max_rounds: Maximum number of rounds to include

        Returns:
            Formatted history string
        """
        if not history:
            return ""

        # Get last N rounds (each round has 2 turns)
        recent_turns = history[-(max_rounds * 2):]

        formatted = []
        for turn in recent_turns:
            formatted.append(f"Round {turn.round_number} - {turn.cli_name.title()}: {turn.response}")

        return "\n\n".join(formatted)
