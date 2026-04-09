"""CLI executor for running Claude Code and Codex commands."""

import subprocess
import logging
import time
from typing import List
from .config import CLIResponse


logger = logging.getLogger(__name__)


class CLIExecutor:
    """Execute CLI commands with timeout and error handling."""

    def __init__(self, cli_name: str, cli_path: str, timeout: int = 120):
        """
        Initialize CLI executor.

        Args:
            cli_name: Name of the CLI (e.g., 'claude', 'codex')
            cli_path: Full path to the CLI binary
            timeout: Timeout in seconds for each command
        """
        self.cli_name = cli_name
        self.cli_path = cli_path
        self.timeout = timeout
        logger.info(f"Initialized {cli_name} executor at {cli_path} with {timeout}s timeout")

    def execute(self, prompt: str) -> CLIResponse:
        """
        Execute a prompt with the CLI.

        Args:
            prompt: The prompt to send to the CLI

        Returns:
            CLIResponse object with result
        """
        start_time = time.time()
        cmd = self._build_command(prompt)

        logger.debug(f"Executing {self.cli_name} command: {' '.join(cmd[:2])} [prompt truncated]")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False  # Don't raise on non-zero exit code
            )

            execution_time = time.time() - start_time

            if result.returncode == 0:
                logger.info(f"{self.cli_name} completed successfully in {execution_time:.2f}s")
                return CLIResponse(
                    success=True,
                    output=result.stdout.strip(),
                    execution_time=execution_time
                )
            else:
                logger.warning(f"{self.cli_name} returned non-zero exit code: {result.returncode}")
                return CLIResponse(
                    success=False,
                    output=result.stdout.strip() if result.stdout else "",
                    error=result.stderr.strip() if result.stderr else f"Exit code: {result.returncode}",
                    execution_time=execution_time
                )

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            logger.warning(f"{self.cli_name} timed out after {self.timeout}s")
            return self._handle_timeout(execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{self.cli_name} execution failed: {str(e)}")
            return self._handle_error(e, execution_time)

    def _build_command(self, prompt: str) -> List[str]:
        """
        Build the command list for subprocess.

        Args:
            prompt: The prompt to send

        Returns:
            Command as list of strings
        """
        if self.cli_name.lower() == "claude":
            # Claude Code: claude -p "prompt"
            return [self.cli_path, "-p", prompt]
        elif self.cli_name.lower() == "codex":
            # Codex: codex exec "prompt" --skip-git-repo-check
            # Skip git repo check for Docker/non-git environments
            return [self.cli_path, "exec", prompt, "--skip-git-repo-check"]
        else:
            raise ValueError(f"Unknown CLI name: {self.cli_name}")

    def _handle_timeout(self, execution_time: float) -> CLIResponse:
        """
        Handle timeout scenario.

        Args:
            execution_time: Time elapsed before timeout

        Returns:
            CLIResponse indicating timeout
        """
        return CLIResponse(
            success=False,
            output="",
            error=f"Command timed out after {self.timeout} seconds",
            execution_time=execution_time,
            timed_out=True
        )

    def _handle_error(self, error: Exception, execution_time: float) -> CLIResponse:
        """
        Handle execution error.

        Args:
            error: The exception that occurred
            execution_time: Time elapsed before error

        Returns:
            CLIResponse indicating error
        """
        return CLIResponse(
            success=False,
            output="",
            error=str(error),
            execution_time=execution_time
        )

    def test_availability(self) -> bool:
        """
        Test if the CLI is available and working.

        Returns:
            True if CLI responds, False otherwise
        """
        test_prompt = "Say 'test' and nothing else."
        try:
            response = self.execute(test_prompt)
            return response.success
        except Exception as e:
            logger.error(f"CLI availability test failed: {e}")
            return False
