"""Track actions and file changes during debates."""

import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    """Represents a file change."""

    path: Path
    change_type: str  # 'created', 'modified', 'deleted'
    timestamp: datetime = field(default_factory=datetime.now)
    diff: Optional[str] = None  # Git diff if available

    def __repr__(self):
        return f"<FileChange: {self.change_type} {self.path}>"


@dataclass
class TurnActions:
    """Actions taken during a single turn."""

    round_number: int
    cli_name: str
    file_changes: List[FileChange] = field(default_factory=list)
    bash_commands: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def summary(self) -> str:
        """Get a summary of actions taken."""
        parts = []
        if self.file_changes:
            parts.append(f"{len(self.file_changes)} file(s) changed")
        if self.bash_commands:
            parts.append(f"{len(self.bash_commands)} command(s) run")
        return ", ".join(parts) if parts else "No actions"


class ActionTracker:
    """Tracks file changes and actions during a debate."""

    def __init__(self, working_dir: Path):
        """
        Initialize action tracker.

        Args:
            working_dir: Working directory to monitor
        """
        self.working_dir = working_dir
        self.turn_actions: List[TurnActions] = []
        self._baseline_files: Set[Path] = set()
        self._capture_baseline()

        logger.info(f"Action tracker initialized in {working_dir}")

    def _capture_baseline(self):
        """Capture baseline state of files."""
        if self.working_dir.exists():
            self._baseline_files = set(self.working_dir.rglob("*"))
            logger.debug(f"Captured baseline: {len(self._baseline_files)} files")

    def start_turn(self, round_number: int, cli_name: str) -> TurnActions:
        """
        Start tracking a new turn.

        Args:
            round_number: The round number
            cli_name: Name of the CLI

        Returns:
            TurnActions object for this turn
        """
        turn = TurnActions(round_number=round_number, cli_name=cli_name)
        self.turn_actions.append(turn)
        logger.debug(f"Started tracking turn: round {round_number}, {cli_name}")
        return turn

    def detect_file_changes(self) -> List[FileChange]:
        """
        Detect file changes since last check using git.

        Returns:
            List of FileChange objects
        """
        changes = []

        try:
            # Use git status to detect changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.working_dir),
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if len(line) < 4:
                        continue

                    status = line[:2].strip()
                    filepath = Path(line[3:])

                    change_type = self._parse_git_status(status)
                    if change_type:
                        # Get diff for this file
                        diff = self._get_file_diff(filepath)
                        changes.append(FileChange(
                            path=filepath,
                            change_type=change_type,
                            diff=diff
                        ))

            logger.debug(f"Detected {len(changes)} file changes")

        except Exception as e:
            logger.warning(f"Failed to detect file changes: {e}")

        return changes

    def _parse_git_status(self, status: str) -> Optional[str]:
        """Parse git status code to change type."""
        if 'M' in status:
            return 'modified'
        elif 'A' in status or '?' in status:
            return 'created'
        elif 'D' in status:
            return 'deleted'
        return None

    def _get_file_diff(self, filepath: Path) -> Optional[str]:
        """Get git diff for a file."""
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD", str(filepath)],
                cwd=str(self.working_dir),
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout:
                return result.stdout

            # If no diff from HEAD, try working directory diff
            result = subprocess.run(
                ["git", "diff", str(filepath)],
                cwd=str(self.working_dir),
                capture_output=True,
                text=True,
                timeout=5
            )

            return result.stdout if result.returncode == 0 else None

        except Exception as e:
            logger.debug(f"Failed to get diff for {filepath}: {e}")
            return None

    def finalize_turn(self, turn: TurnActions):
        """
        Finalize a turn by detecting and recording file changes.

        Args:
            turn: The turn to finalize
        """
        # Detect file changes
        changes = self.detect_file_changes()
        turn.file_changes = changes

        logger.info(f"Finalized turn {turn.round_number}: {turn.summary()}")

    def get_all_changes(self) -> List[FileChange]:
        """Get all file changes across all turns."""
        all_changes = []
        for turn in self.turn_actions:
            all_changes.extend(turn.file_changes)
        return all_changes

    def get_turn_summary(self, round_number: int) -> Optional[TurnActions]:
        """Get actions for a specific turn."""
        for turn in self.turn_actions:
            if turn.round_number == round_number:
                return turn
        return None

    def generate_report(self) -> str:
        """Generate a summary report of all actions."""
        lines = ["Action Tracker Report", "=" * 60, ""]

        total_changes = 0
        total_commands = 0

        for turn in self.turn_actions:
            lines.append(f"Round {turn.round_number} - {turn.cli_name.upper()}")
            lines.append(f"  {turn.summary()}")

            if turn.file_changes:
                lines.append("  File Changes:")
                for change in turn.file_changes:
                    lines.append(f"    - {change.change_type.upper()}: {change.path}")
                total_changes += len(turn.file_changes)

            if turn.bash_commands:
                lines.append("  Commands:")
                for cmd in turn.bash_commands:
                    lines.append(f"    - {cmd}")
                total_commands += len(turn.bash_commands)

            lines.append("")

        lines.append("=" * 60)
        lines.append(f"Total: {total_changes} file changes, {total_commands} commands")

        return "\n".join(lines)
