"""Collaborative exploration mode."""

from typing import List, Optional, TYPE_CHECKING
from .base import DebateMode

if TYPE_CHECKING:
    from ..orchestrator import Turn
    from ..pr_context import PRContext


class CollaborativeMode(DebateMode):
    """Collaborative mode where CLIs build on each other's ideas."""

    def get_mode_instructions(self, cli_name: str) -> str:
        """Get collaborative instructions (same for both CLIs)."""
        return """You are participating in a collaborative exploration. Your goal is to work together with your partner to:
- Explore the topic from multiple angles
- Build on previous contributions
- Find common ground and synthesize ideas
- Expand understanding through constructive dialogue

Be thoughtful, open-minded, and add complementary insights."""

    def get_initial_prompt(self, topic: str, cli_name: str, pr_context: Optional["PRContext"] = None) -> str:
        """Generate initial prompt for collaborative exploration."""
        instructions = self.get_mode_instructions(cli_name)

        prompt = f"""{instructions}

**Topic for Exploration:** {topic}
"""

        # Add PR context if available
        if pr_context:
            prompt += f"\n{pr_context.format_for_debate()}\n"

        prompt += "\nBegin the collaborative exploration. Share your initial thoughts, perspectives, and questions about this topic.\nSet a constructive tone for the discussion."

        return prompt

    def get_response_prompt(self, topic: str, cli_name: str, conversation_history: List["Turn"], pr_context: Optional["PRContext"] = None) -> str:
        """Generate response prompt with collaborative framing."""
        instructions = self.get_mode_instructions(cli_name)
        history = self.format_history(conversation_history)

        # Get last contribution
        last_turn = conversation_history[-1] if conversation_history else None
        partner_name = "your partner" if not last_turn else last_turn.cli_name.title()

        prompt = f"""{instructions}

**Topic for Exploration:** {topic}
"""

        # Add PR context if available (only on first response)
        if pr_context and len(conversation_history) <= 2:
            prompt += f"\n{pr_context.format_for_debate()}\n"

        prompt += f"""
**Conversation So Far:**
{history}

**Your Turn:**
Build on {partner_name}'s contribution. You might:
- Expand on their ideas with additional perspectives
- Make connections to related concepts
- Ask clarifying questions that deepen understanding
- Synthesize what has been discussed so far
- Introduce complementary viewpoints

Keep the collaborative spirit and add meaningful value to the exploration."""

        return prompt
