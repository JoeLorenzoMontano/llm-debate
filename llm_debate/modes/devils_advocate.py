"""Devil's Advocate mode."""

from typing import List, TYPE_CHECKING
from .base import DebateMode

if TYPE_CHECKING:
    from ..orchestrator import Turn


class DevilsAdvocateMode(DebateMode):
    """Devil's Advocate mode where one proposes and the other critiques."""

    def get_mode_instructions(self, cli_name: str) -> str:
        """Get role-specific instructions."""
        if cli_name.lower() == "claude":
            return """You are the PROPOSER in a devil's advocate discussion.
Your role is to:
- Propose ideas, solutions, and approaches
- Present your reasoning clearly
- Respond to critiques by refining your proposals
- Acknowledge valid concerns and improve your ideas

Be thoughtful but willing to defend your proposals."""
        else:  # codex
            return """You are the CRITIC (devil's advocate) in this discussion.
Your role is to:
- Critically evaluate proposals
- Find weaknesses, edge cases, and potential problems
- Challenge assumptions
- Suggest improvements and alternatives

Be constructive in your criticism - the goal is to strengthen ideas, not just tear them down."""

    def get_initial_prompt(self, topic: str, cli_name: str) -> str:
        """Generate initial prompt based on role."""
        instructions = self.get_mode_instructions(cli_name)

        if cli_name.lower() == "claude":
            # Claude proposes first
            return f"""{instructions}

**Topic:** {topic}

Present your initial proposal or approach to this topic. Be specific and explain your reasoning."""
        else:
            # Codex should not go first in this mode
            return f"""{instructions}

**Topic:** {topic}

Wait for the proposer to make their initial proposal, then provide your critique."""

    def get_response_prompt(self, topic: str, cli_name: str, conversation_history: List["Turn"]) -> str:
        """Generate response prompt based on role and history."""
        instructions = self.get_mode_instructions(cli_name)
        history = self.format_history(conversation_history)

        if cli_name.lower() == "claude":
            # Claude responds to critiques by refining proposals
            return f"""{instructions}

**Topic:** {topic}

**Conversation So Far:**
{history}

**Your Turn:**
Respond to the criticism. You can:
- Address the concerns raised
- Refine your proposal based on valid feedback
- Defend aspects that you believe are sound
- Propose alternative approaches

Show how the critique has helped improve your thinking."""
        else:
            # Codex critiques the latest proposal
            return f"""{instructions}

**Topic:** {topic}

**Conversation So Far:**
{history}

**Your Turn:**
Critically evaluate the latest proposal. Consider:
- What assumptions are being made?
- What edge cases might break this?
- What are potential weaknesses or limitations?
- How could this be improved?

Provide constructive criticism that helps strengthen the proposal."""
