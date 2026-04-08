"""Git safety features for debate sessions."""

import logging
import subprocess
from pathlib import Path
from typing import Optional, List
from datetime import datetime


logger = logging.getLogger(__name__)


class GitSafetyError(Exception):
    """Exception for git safety operations."""
    pass


class GitSafety:
    """Manages git safety features for debates."""

    def __init__(self, working_dir: Path, branch_name: Optional[str] = None):
        """
        Initialize git safety manager.

        Args:
            working_dir: Working directory (should be a git repo)
            branch_name: Branch name for debate (auto-generated if None)
        """
        self.working_dir = working_dir
        self.original_branch: Optional[str] = None
        self.debate_branch: Optional[str] = branch_name
        self.commits: List[str] = []

        # Verify git repo
        if not self._is_git_repo():
            raise GitSafetyError(f"{working_dir} is not a git repository")

        logger.info(f"Git safety initialized in {working_dir}")

    def _is_git_repo(self) -> bool:
        """Check if working directory is a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=str(self.working_dir),
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_git_command(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """
        Run a git command safely.

        Args:
            args: Git command arguments
            check: Whether to raise on non-zero exit

        Returns:
            CompletedProcess result
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=str(self.working_dir),
                capture_output=True,
                text=True,
                timeout=30,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            raise GitSafetyError(f"Git command failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise GitSafetyError("Git command timed out")

    def get_current_branch(self) -> str:
        """Get the current git branch."""
        result = self._run_git_command(["branch", "--show-current"])
        return result.stdout.strip()

    def create_debate_branch(self, base_name: str = "debate") -> str:
        """
        Create and checkout a new branch for the debate.

        Args:
            base_name: Base name for the branch

        Returns:
            Name of created branch
        """
        # Save original branch
        self.original_branch = self.get_current_branch()
        logger.info(f"Original branch: {self.original_branch}")

        # Generate branch name with timestamp
        if not self.debate_branch:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.debate_branch = f"{base_name}-{timestamp}"

        # Create and checkout new branch
        try:
            self._run_git_command(["checkout", "-b", self.debate_branch])
            logger.info(f"Created debate branch: {self.debate_branch}")
            return self.debate_branch
        except GitSafetyError as e:
            # Branch might already exist, try to checkout
            try:
                self._run_git_command(["checkout", self.debate_branch])
                logger.info(f"Checked out existing branch: {self.debate_branch}")
                return self.debate_branch
            except GitSafetyError:
                raise GitSafetyError(f"Failed to create or checkout branch: {e}")

    def commit_turn(self, round_number: int, cli_name: str, message: Optional[str] = None) -> Optional[str]:
        """
        Commit changes from a turn.

        Args:
            round_number: The round number
            cli_name: Name of the CLI
            message: Optional custom commit message

        Returns:
            Commit SHA if committed, None if no changes
        """
        # Check if there are changes to commit
        status = self._run_git_command(["status", "--porcelain"], check=False)
        if not status.stdout.strip():
            logger.debug("No changes to commit")
            return None

        # Stage all changes
        self._run_git_command(["add", "-A"])

        # Create commit message
        if not message:
            message = f"Round {round_number} - {cli_name} changes"

        # Commit
        try:
            self._run_git_command(["commit", "-m", message])

            # Get commit SHA
            result = self._run_git_command(["rev-parse", "HEAD"])
            commit_sha = result.stdout.strip()

            self.commits.append(commit_sha)
            logger.info(f"Committed turn {round_number}: {commit_sha[:8]}")

            return commit_sha

        except GitSafetyError as e:
            logger.warning(f"Failed to commit turn: {e}")
            return None

    def rollback_to_commit(self, commit_sha: str, hard: bool = False):
        """
        Rollback to a specific commit.

        Args:
            commit_sha: Commit SHA to rollback to
            hard: Whether to do a hard reset (loses uncommitted changes)
        """
        reset_type = "--hard" if hard else "--soft"
        try:
            self._run_git_command(["reset", reset_type, commit_sha])
            logger.info(f"Rolled back to commit: {commit_sha[:8]}")
        except GitSafetyError as e:
            raise GitSafetyError(f"Failed to rollback: {e}")

    def rollback_turns(self, num_turns: int):
        """
        Rollback a specific number of turns.

        Args:
            num_turns: Number of turns to rollback
        """
        if num_turns > len(self.commits):
            raise GitSafetyError(f"Cannot rollback {num_turns} turns, only {len(self.commits)} commits exist")

        if num_turns == 0:
            return

        # Get target commit (go back num_turns commits)
        target_commit = self.commits[-(num_turns + 1)] if num_turns < len(self.commits) else self.commits[0]
        self.rollback_to_commit(target_commit, hard=True)

        # Remove rolled-back commits from tracking
        self.commits = self.commits[:-num_turns]

    def return_to_original_branch(self, delete_debate_branch: bool = False):
        """
        Return to the original branch.

        Args:
            delete_debate_branch: Whether to delete the debate branch
        """
        if not self.original_branch:
            logger.warning("No original branch recorded")
            return

        try:
            # Checkout original branch
            self._run_git_command(["checkout", self.original_branch])
            logger.info(f"Returned to original branch: {self.original_branch}")

            # Optionally delete debate branch
            if delete_debate_branch and self.debate_branch:
                try:
                    self._run_git_command(["branch", "-D", self.debate_branch])
                    logger.info(f"Deleted debate branch: {self.debate_branch}")
                except GitSafetyError as e:
                    logger.warning(f"Failed to delete debate branch: {e}")

        except GitSafetyError as e:
            logger.error(f"Failed to return to original branch: {e}")
            raise

    def get_diff_summary(self) -> str:
        """Get a summary of all changes on the debate branch."""
        if not self.original_branch:
            return "No original branch to compare against"

        try:
            result = self._run_git_command(["diff", "--stat", self.original_branch], check=False)
            return result.stdout if result.stdout else "No changes"
        except GitSafetyError:
            return "Failed to get diff summary"

    def merge_to_original(self, squash: bool = True) -> bool:
        """
        Merge debate branch back to original branch.

        Args:
            squash: Whether to squash commits

        Returns:
            True if successful, False otherwise
        """
        if not self.original_branch or not self.debate_branch:
            logger.error("Cannot merge: missing branch information")
            return False

        try:
            # Checkout original branch
            self._run_git_command(["checkout", self.original_branch])

            # Merge debate branch
            if squash:
                self._run_git_command(["merge", "--squash", self.debate_branch])
                # Need to manually commit after squash merge
                self._run_git_command(["commit", "-m", f"Merge debate from {self.debate_branch}"])
            else:
                self._run_git_command(["merge", self.debate_branch, "-m", f"Merge debate from {self.debate_branch}"])

            logger.info(f"Merged {self.debate_branch} into {self.original_branch}")
            return True

        except GitSafetyError as e:
            logger.error(f"Failed to merge: {e}")
            return False
