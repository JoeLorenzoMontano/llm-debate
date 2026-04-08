"""Stream output handler for real-time console output."""

from typing import TYPE_CHECKING
from .base import OutputHandler

if TYPE_CHECKING:
    from ..config import DebateConfig
    from ..orchestrator import Turn, DebateResult

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback to no color
    class Fore:
        BLUE = ""
        GREEN = ""
        YELLOW = ""
        RED = ""
        CYAN = ""
        MAGENTA = ""

    class Style:
        RESET_ALL = ""
        BRIGHT = ""


class StreamHandler(OutputHandler):
    """Outputs debate progress in real-time to console with colors."""

    def __init__(self):
        """Initialize stream handler."""
        self.use_color = COLORAMA_AVAILABLE

    def on_debate_start(self, config: "DebateConfig"):
        """Display debate start information."""
        print(f"\n{Style.BRIGHT}{Fore.CYAN}{'=' * 80}")
        print(f"{Style.BRIGHT}{Fore.CYAN}CLI DEBATE")
        print(f"{Style.BRIGHT}{Fore.CYAN}{'=' * 80}")
        print(f"\n{Fore.YELLOW}Topic: {Style.BRIGHT}{config.topic}")
        print(f"{Fore.YELLOW}Mode: {Style.BRIGHT}{config.mode}")
        print(f"{Fore.YELLOW}Max Rounds: {Style.BRIGHT}{config.max_rounds}")
        print(f"{Fore.YELLOW}Convergence: {Style.BRIGHT}{'Enabled' if config.enable_convergence else 'Disabled'}")
        if config.enable_convergence:
            print(f"{Fore.YELLOW}Convergence Threshold: {Style.BRIGHT}{config.convergence_threshold}")
        print(f"\n{Style.BRIGHT}{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")

    def on_turn_start(self, turn: "Turn"):
        """Display turn start information."""
        cli_color = Fore.BLUE if turn.cli_name.lower() == "claude" else Fore.GREEN
        print(f"\n{Style.BRIGHT}[Round {turn.round_number}] {cli_color}{turn.cli_name.upper()}{Style.RESET_ALL} is responding...")

    def on_turn_complete(self, turn: "Turn"):
        """Display turn completion with response."""
        cli_color = Fore.BLUE if turn.cli_name.lower() == "claude" else Fore.GREEN

        if not turn.success:
            print(f"{Fore.RED}[ERROR] Response failed or timed out{Style.RESET_ALL}")
            if turn.response:
                print(f"{Fore.RED}{turn.response}{Style.RESET_ALL}")
        else:
            print(f"\n{cli_color}{turn.response}{Style.RESET_ALL}")

        # Show execution time
        print(f"\n{Fore.MAGENTA}⏱ Execution time: {turn.execution_time:.2f}s{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 80}{Style.RESET_ALL}")

    def on_debate_complete(self, result: "DebateResult"):
        """Display debate completion summary."""
        print(f"\n{Style.BRIGHT}{Fore.CYAN}{'=' * 80}")
        print(f"{Style.BRIGHT}{Fore.CYAN}DEBATE COMPLETE")
        print(f"{Style.BRIGHT}{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Total Rounds: {Style.BRIGHT}{result.total_rounds}")
        print(f"{Fore.YELLOW}End Reason: {Style.BRIGHT}{result.end_reason}")

        if result.converged:
            print(f"{Fore.GREEN}{Style.BRIGHT}✓ Convergence Detected!")
            print(f"{Fore.GREEN}Reason: {result.convergence_reason}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No convergence detected{Style.RESET_ALL}")

        print(f"\n{Style.BRIGHT}{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
