"""Configuration dataclasses for CLI Debate Tool."""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class DebateConfig:
    """Configuration for debate orchestration."""

    # Core settings
    topic: str
    mode: str = "adversarial"  # adversarial, collaborative, devils_advocate
    max_rounds: int = 10
    timeout_per_round: int = 120  # seconds

    # Convergence settings
    convergence_threshold: float = 0.85  # 0.0-1.0
    enable_convergence: bool = True

    # Output settings
    output_handlers: List[str] = field(default_factory=lambda: ["stream"])
    markdown_output_path: Optional[Path] = None

    # CLI paths
    claude_bin: str = "/home/jolomoadmin/.local/bin/claude"
    codex_bin: str = "/home/jolomoadmin/.npm-global/bin/codex"

    # Logging
    log_level: str = "INFO"
    log_file: str = "debate.log"

    # Action mode settings
    enable_actions: bool = False  # Enable tool use and file modifications
    permission_mode: str = "acceptEdits"  # Claude permission mode
    git_branch: Optional[str] = None  # Git branch for debate (auto-created if None)
    auto_commit: bool = True  # Commit changes after each turn
    allow_rollback: bool = True  # Allow rolling back failed debates

    # PR context settings
    pr_number: Optional[str] = None  # PR number or URL to review
    pr_repo: Optional[str] = None  # Repository in format 'owner/repo'
    pr_checkout: bool = False  # Checkout PR branch before debate
    gh_bin: str = "gh"  # Path to GitHub CLI

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate mode
        valid_modes = ["adversarial", "collaborative", "devils_advocate"]
        if self.mode not in valid_modes:
            raise ValueError(f"Invalid mode '{self.mode}'. Must be one of: {valid_modes}")

        # Validate convergence threshold
        if not 0.0 <= self.convergence_threshold <= 1.0:
            raise ValueError(f"Convergence threshold must be between 0.0 and 1.0, got {self.convergence_threshold}")

        # Validate max_rounds
        if self.max_rounds < 1:
            raise ValueError(f"max_rounds must be at least 1, got {self.max_rounds}")

        # Validate timeout
        if self.timeout_per_round < 1:
            raise ValueError(f"timeout_per_round must be at least 1, got {self.timeout_per_round}")

        # Validate output handlers
        valid_outputs = ["stream", "summary", "markdown"]
        for handler in self.output_handlers:
            if handler not in valid_outputs:
                raise ValueError(f"Invalid output handler '{handler}'. Must be one of: {valid_outputs}")

        # If markdown output is enabled, require path
        if "markdown" in self.output_handlers and not self.markdown_output_path:
            raise ValueError("markdown_output_path is required when 'markdown' output handler is enabled")

        # Convert markdown path to Path object if string
        if self.markdown_output_path and isinstance(self.markdown_output_path, str):
            self.markdown_output_path = Path(self.markdown_output_path)

        # Validate CLI binaries exist
        self._validate_cli_binary(self.claude_bin, "Claude")
        self._validate_cli_binary(self.codex_bin, "Codex")

    def _validate_cli_binary(self, path: str, name: str):
        """Validate that a CLI binary exists and is executable."""
        bin_path = Path(path)
        if not bin_path.exists():
            raise FileNotFoundError(f"{name} CLI not found at {path}")
        if not bin_path.is_file():
            raise ValueError(f"{name} CLI path {path} is not a file")
        # Note: Executable check on Linux/Unix
        import os
        if not os.access(path, os.X_OK):
            raise PermissionError(f"{name} CLI at {path} is not executable")


@dataclass
class CLIResponse:
    """Response from a CLI execution."""

    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    timed_out: bool = False
    actions: List = field(default_factory=list)  # Actions taken (for session mode)

    def __str__(self):
        if self.success:
            return self.output
        return f"Error: {self.error}"
