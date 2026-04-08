"""Base class for output handlers."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import DebateConfig
    from ..orchestrator import Turn, DebateResult


class OutputHandler(ABC):
    """Abstract base class for output handlers."""

    @abstractmethod
    def on_debate_start(self, config: "DebateConfig"):
        """Called when debate starts."""
        pass

    @abstractmethod
    def on_turn_start(self, turn: "Turn"):
        """Called when a turn starts."""
        pass

    @abstractmethod
    def on_turn_complete(self, turn: "Turn"):
        """Called when a turn completes."""
        pass

    @abstractmethod
    def on_debate_complete(self, result: "DebateResult"):
        """Called when debate completes."""
        pass
