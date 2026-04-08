"""Adversarial debate mode."""

from typing import List, TYPE_CHECKING
from .base import DebateMode

if TYPE_CHECKING:
    from ..orchestrator import Turn


class AdversarialMode(DebateMode):
    """Adversarial debate mode where CLIs argue opposing viewpoints."""

    def get_mode_instructions(self, cli_name: str) -> str:
        """Get adversarial instructions based on CLI."""
        if cli_name.lower() == "claude":
            return """You are participating in an adversarial debate. Your role is to argue FOR the proposition.
Be rigorous, challenge opposing viewpoints, and strengthen your arguments.
Focus on logic, evidence, and finding weaknesses in the opposing position."""
        else:  # codex
            return """You are participating in an adversarial debate. Your role is to argue AGAINST the proposition.
Be rigorous, challenge opposing viewpoints, and strengthen your arguments.
Focus on logic, evidence, and finding weaknesses in the opposing position."""

    def get_initial_prompt(self, topic: str, cli_name: str) -> str:
        """Generate initial prompt for the first speaker."""
        instructions = self.get_mode_instructions(cli_name)
        position = "FOR" if cli_name.lower() == "claude" else "AGAINST"

        return f"""{instructions}

**Proposition:** {topic}

**Your Position:** {position}

Present your opening argument. Be clear, concise, and persuasive. Make your strongest points upfront."""

    def get_response_prompt(self, topic: str, cli_name: str, conversation_history: List["Turn"]) -> str:
        """Generate response prompt with conversation context."""
        instructions = self.get_mode_instructions(cli_name)
        position = "FOR" if cli_name.lower() == "claude" else "AGAINST"
        history = self.format_history(conversation_history)

        # Get last opposing argument
        last_turn = conversation_history[-1] if conversation_history else None
        opponent_name = "your opponent" if not last_turn else last_turn.cli_name.title()

        return f"""{instructions}

**Proposition:** {topic}

**Your Position:** {position}

**Conversation So Far:**
{history}

**Your Turn:**
Respond to {opponent_name}'s latest argument. Challenge their points, present counter-evidence, and reinforce your position.
Keep your response focused and persuasive."""
