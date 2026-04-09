"""Devil's Advocate mode."""

from typing import List, Optional, TYPE_CHECKING
from .base import DebateMode

if TYPE_CHECKING:
    from ..orchestrator import Turn
    from ..pr_context import PRContext


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

    def get_initial_prompt(self, topic: str, cli_name: str, pr_context: Optional["PRContext"] = None) -> str:
        """Generate initial prompt based on role."""
        instructions = self.get_mode_instructions(cli_name)

        if cli_name.lower() == "claude":
            # Claude proposes first
            prompt = f"""{instructions}

**Topic:** {topic}
"""
            # Add PR context if available
            if pr_context:
                prompt += f"\n{pr_context.format_for_debate()}\n"

            prompt += "\nPresent your initial proposal or approach to this topic. Be specific and explain your reasoning."
            return prompt
        else:
            # Codex should not go first in this mode
            prompt = f"""{instructions}

**Topic:** {topic}
"""
            # Add PR context if available
            if pr_context:
                prompt += f"\n{pr_context.format_for_debate()}\n"

            prompt += "\nWait for the proposer to make their initial proposal, then provide your critique."
            return prompt

    def get_response_prompt(self, topic: str, cli_name: str, conversation_history: List["Turn"], pr_context: Optional["PRContext"] = None) -> str:
        """Generate response prompt based on role and history."""
        instructions = self.get_mode_instructions(cli_name)
        history = self.format_history(conversation_history)

        if cli_name.lower() == "claude":
            # Claude responds to critiques by refining proposals
            prompt = f"""{instructions}

**Topic:** {topic}
"""
            # Add PR context if available (only on first response)
            if pr_context and len(conversation_history) <= 2:
                prompt += f"\n{pr_context.format_for_debate()}\n"

            prompt += f"""
**Conversation So Far:**
{history}

**Your Turn:**
Respond to the criticism. You can:
- Address the concerns raised
- Refine your proposal based on valid feedback
- Defend aspects that you believe are sound
- Propose alternative approaches

Show how the critique has helped improve your thinking."""
            return prompt
        else:
            # Codex critiques the latest proposal
            prompt = f"""{instructions}

**Topic:** {topic}
"""
            # Add PR context if available (only on first response)
            if pr_context and len(conversation_history) <= 2:
                prompt += f"\n{pr_context.format_for_debate()}\n"

            prompt += f"""
**Conversation So Far:**
{history}

**Your Turn:**
Critically evaluate the latest proposal. Consider:
- What assumptions are being made?
- What edge cases might break this?
- What are potential weaknesses or limitations?
- How could this be improved?

Provide constructive criticism that helps strengthen the proposal."""
            return prompt
