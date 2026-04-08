"""Summary output handler - shows final summary only."""

from typing import TYPE_CHECKING
from .base import OutputHandler

if TYPE_CHECKING:
    from ..config import DebateConfig
    from ..orchestrator import Turn, DebateResult


class SummaryHandler(OutputHandler):
    """Outputs minimal information during debate, comprehensive summary at end."""

    def __init__(self):
        """Initialize summary handler."""
        self.rounds_completed = 0

    def on_debate_start(self, config: "DebateConfig"):
        """Display minimal start information."""
        print(f"\nStarting {config.mode} debate on: {config.topic}")
        print(f"Running up to {config.max_rounds} rounds...\n")

    def on_turn_start(self, turn: "Turn"):
        """Display minimal turn start info."""
        # Just show progress indicator
        print(f"Round {turn.round_number}... ", end="", flush=True)

    def on_turn_complete(self, turn: "Turn"):
        """Mark turn completion."""
        print("✓")
        self.rounds_completed = turn.round_number

    def on_debate_complete(self, result: "DebateResult"):
        """Display comprehensive summary."""
        print("\n" + "=" * 80)
        print("DEBATE SUMMARY")
        print("=" * 80)
        print(f"\nTopic: {result.topic}")
        print(f"Mode: {result.mode}")
        print(f"Total Rounds: {result.total_rounds}")
        print(f"End Reason: {result.end_reason}")

        if result.converged:
            print(f"\n✓ CONVERGED: {result.convergence_reason}")
        else:
            print("\n○ No convergence detected")

        # Show key points from each CLI
        print("\n" + "-" * 80)
        print("KEY POINTS")
        print("-" * 80)

        # Get first and last response from each CLI
        claude_turns = [t for t in result.turns if t.cli_name.lower() == "claude" and t.success]
        codex_turns = [t for t in result.turns if t.cli_name.lower() == "codex" and t.success]

        if claude_turns:
            print(f"\nCLAUDE:")
            print(f"Opening: {self._truncate(claude_turns[0].response, 200)}")
            if len(claude_turns) > 1:
                print(f"Final: {self._truncate(claude_turns[-1].response, 200)}")

        if codex_turns:
            print(f"\nCODEX:")
            print(f"Opening: {self._truncate(codex_turns[0].response, 200)}")
            if len(codex_turns) > 1:
                print(f"Final: {self._truncate(codex_turns[-1].response, 200)}")

        # Show final consensus or conclusion
        if result.converged and len(result.turns) >= 2:
            print("\n" + "-" * 80)
            print("FINAL POSITION")
            print("-" * 80)
            last_turn = result.turns[-1]
            print(f"\n{last_turn.cli_name.upper()}'s final response:")
            print(f"{last_turn.response}")

        print("\n" + "=" * 80 + "\n")

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
