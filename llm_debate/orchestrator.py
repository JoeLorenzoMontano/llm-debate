"""Main orchestrator for debate management."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from .config import DebateConfig
from .cli_executor import CLIExecutor
from .modes.adversarial import AdversarialMode
from .modes.collaborative import CollaborativeMode
from .modes.devils_advocate import DevilsAdvocateMode
from .pr_context import PRContextFetcher, PRContext


logger = logging.getLogger(__name__)


@dataclass
class Turn:
    """Represents a single turn in the debate."""

    round_number: int
    cli_name: str
    prompt_sent: str
    response: str
    timestamp: datetime
    execution_time: float
    success: bool = True


@dataclass
class DebateResult:
    """Results from a complete debate."""

    topic: str
    mode: str
    turns: List[Turn]
    total_rounds: int
    converged: bool
    convergence_reason: Optional[str] = None
    end_reason: str = ""  # "max_rounds", "converged", "error"


class DebateOrchestrator:
    """Orchestrates debates between Claude Code and Codex CLIs."""

    def __init__(self, config: DebateConfig):
        """
        Initialize the orchestrator.

        Args:
            config: Debate configuration
        """
        self.config = config
        self.conversation_history: List[Turn] = []
        self.pr_context: Optional[PRContext] = None

        # Initialize CLI executors
        self.claude_executor = CLIExecutor("claude", config.claude_bin, config.timeout_per_round)
        self.codex_executor = CLIExecutor("codex", config.codex_bin, config.timeout_per_round)

        # Initialize debate mode
        self.mode = self._create_mode(config.mode)

        # Output handlers will be set by main.py
        self.output_handlers = []

        logger.info(f"Orchestrator initialized for {config.mode} mode on topic: {config.topic}")

    def _create_mode(self, mode_name: str):
        """Create debate mode instance."""
        modes = {
            "adversarial": AdversarialMode(),
            "collaborative": CollaborativeMode(),
            "devils_advocate": DevilsAdvocateMode()
        }
        return modes[mode_name]

    def add_output_handler(self, handler):
        """Add an output handler to notify on events."""
        self.output_handlers.append(handler)

    def run_debate(self) -> DebateResult:
        """
        Run the complete debate.

        Returns:
            DebateResult with complete debate information
        """
        logger.info(f"Starting debate on topic: {self.config.topic}")

        # Fetch PR context if requested
        if self.config.pr_number:
            try:
                logger.info(f"Fetching PR context for: {self.config.pr_number}")
                fetcher = PRContextFetcher(self.config.gh_bin)
                self.pr_context = fetcher.fetch_pr_context(
                    self.config.pr_number,
                    self.config.pr_repo
                )
                logger.info(f"PR context fetched: PR #{self.pr_context.pr_number} - {self.pr_context.title}")

                # Checkout PR branch if requested
                if self.config.pr_checkout:
                    logger.info("Checking out PR branch...")
                    success = fetcher.checkout_pr_branch(
                        self.pr_context.pr_number,
                        self.config.pr_repo
                    )
                    if success:
                        logger.info("PR branch checked out successfully")
                    else:
                        logger.warning("Failed to checkout PR branch, continuing anyway")

            except Exception as e:
                logger.error(f"Failed to fetch PR context: {e}")
                # Continue debate without PR context
                logger.warning("Continuing debate without PR context")

        # Notify handlers of debate start
        for handler in self.output_handlers:
            handler.on_debate_start(self.config)

        converged = False
        convergence_reason = None
        end_reason = "max_rounds"

        # Main debate loop
        for round_num in range(1, self.config.max_rounds + 1):
            logger.info(f"Starting round {round_num}/{self.config.max_rounds}")

            # Determine which CLI goes in this round (alternating, Claude starts)
            # Round 1: Claude, Round 2: Codex, Round 3: Claude, etc.
            if round_num % 2 == 1:
                cli_name = "claude"
                executor = self.claude_executor
            else:
                cli_name = "codex"
                executor = self.codex_executor

            # Generate prompt for this turn
            if round_num == 1:
                prompt = self.mode.get_initial_prompt(self.config.topic, cli_name, self.pr_context)
            else:
                prompt = self.mode.get_response_prompt(
                    self.config.topic,
                    cli_name,
                    self.conversation_history,
                    self.pr_context
                )

            # Create turn record
            turn = Turn(
                round_number=round_num,
                cli_name=cli_name,
                prompt_sent=prompt,
                response="",
                timestamp=datetime.now(),
                execution_time=0.0,
                success=False
            )

            # Notify handlers of turn start
            for handler in self.output_handlers:
                handler.on_turn_start(turn)

            # Execute CLI
            logger.debug(f"Executing {cli_name} for round {round_num}")
            response = executor.execute(prompt)

            # Update turn with response
            turn.response = response.output
            turn.execution_time = response.execution_time
            turn.success = response.success

            if not response.success:
                logger.warning(f"Round {round_num} failed: {response.error}")
                # Try to continue with error message as response
                if response.timed_out:
                    turn.response = "[Previous response timed out - continuing based on earlier context]"
                else:
                    turn.response = f"[Error occurred: {response.error}]"

            # Add to history
            self.conversation_history.append(turn)

            # Notify handlers of turn completion
            for handler in self.output_handlers:
                handler.on_turn_complete(turn)

            # Check for convergence (only if enabled and we have enough history)
            if self.config.enable_convergence and len(self.conversation_history) >= 4:
                # Import here to avoid circular dependency
                from .convergence.detector import ConvergenceDetector
                detector = ConvergenceDetector(self.config.convergence_threshold)
                convergence_result = detector.check_convergence(self.conversation_history)

                if convergence_result.is_converged:
                    logger.info(f"Convergence detected: {convergence_result.reason}")
                    converged = True
                    convergence_reason = convergence_result.reason
                    end_reason = "converged"
                    break

            # Emergency brake: check for identical repetitions
            if self._check_emergency_brake():
                logger.warning("Emergency brake triggered - identical repetitions detected")
                end_reason = "repetition"
                break

        # Create result
        result = DebateResult(
            topic=self.config.topic,
            mode=self.config.mode,
            turns=self.conversation_history,
            total_rounds=len(self.conversation_history),
            converged=converged,
            convergence_reason=convergence_reason,
            end_reason=end_reason
        )

        # Notify handlers of debate completion
        for handler in self.output_handlers:
            handler.on_debate_complete(result)

        logger.info(f"Debate completed: {result.total_rounds} rounds, reason: {end_reason}")
        return result

    def _check_emergency_brake(self) -> bool:
        """
        Check for emergency brake condition (identical repetitions).

        Returns:
            True if emergency brake should trigger
        """
        if len(self.conversation_history) < 5:
            return False

        # Get last 5 responses
        last_responses = [turn.response for turn in self.conversation_history[-5:]]

        # Check if they're all very similar (>95% similar using simple comparison)
        from difflib import SequenceMatcher
        similarities = []
        for i in range(len(last_responses) - 1):
            ratio = SequenceMatcher(None, last_responses[i], last_responses[i + 1]).ratio()
            similarities.append(ratio)

        # If all consecutive pairs are >95% similar, trigger brake
        if all(s > 0.95 for s in similarities):
            logger.warning("Emergency brake: Last 5 responses are nearly identical")
            return True

        return False
