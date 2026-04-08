"""Session-based CLI executor for action-taking debates."""

import subprocess
import logging
import time
import json
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
from .config import CLIResponse


logger = logging.getLogger(__name__)


class ActionRecord:
    """Record of an action taken by a CLI."""

    def __init__(self, action_type: str, details: Dict[str, Any]):
        self.action_type = action_type  # 'file_edit', 'bash_command', 'file_create', etc.
        self.details = details
        self.timestamp = time.time()

    def __repr__(self):
        return f"<Action: {self.action_type} - {self.details}>"


class SessionCLIExecutor:
    """Execute CLI commands in session mode with tool access and action tracking."""

    def __init__(self, cli_name: str, cli_path: str, timeout: int = 120,
                 session_id: Optional[str] = None, working_dir: Optional[Path] = None):
        """
        Initialize session-based CLI executor.

        Args:
            cli_name: Name of the CLI (e.g., 'claude', 'codex')
            cli_path: Full path to the CLI binary
            timeout: Timeout in seconds for each command
            session_id: Optional session ID for persistence
            working_dir: Working directory for the CLI
        """
        self.cli_name = cli_name
        self.cli_path = cli_path
        self.timeout = timeout
        self.session_id = session_id or str(uuid.uuid4())
        self.working_dir = working_dir or Path.cwd()
        self.actions: List[ActionRecord] = []

        logger.info(f"Initialized session executor for {cli_name} with session {self.session_id}")

    def execute(self, prompt: str, allow_tools: bool = True,
                permission_mode: str = "acceptEdits") -> CLIResponse:
        """
        Execute a prompt with tool access enabled.

        Args:
            prompt: The prompt to send to the CLI
            allow_tools: Whether to allow tool use (Edit, Bash, Read, etc.)
            permission_mode: Permission mode for Claude ("acceptEdits", "bypassPermissions", etc.)

        Returns:
            CLIResponse object with result and actions taken
        """
        start_time = time.time()

        # Build command based on CLI type
        cmd = self._build_session_command(prompt, allow_tools, permission_mode)

        logger.debug(f"Executing {self.cli_name} in session mode")
        logger.debug(f"Command: {' '.join(cmd[:3])} [prompt truncated]")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.working_dir),
                check=False
            )

            execution_time = time.time() - start_time

            if result.returncode == 0:
                # Parse output to extract actions
                output_text, actions = self._parse_output(result.stdout)
                self.actions.extend(actions)

                logger.info(f"{self.cli_name} completed with {len(actions)} actions in {execution_time:.2f}s")

                return CLIResponse(
                    success=True,
                    output=output_text,
                    execution_time=execution_time,
                    actions=actions  # Add actions to response
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

    def _build_session_command(self, prompt: str, allow_tools: bool,
                               permission_mode: str) -> List[str]:
        """
        Build the command for session-based execution.

        Args:
            prompt: The prompt
            allow_tools: Whether tools are enabled
            permission_mode: Permission mode

        Returns:
            Command as list of strings
        """
        if self.cli_name.lower() == "claude":
            cmd = [
                self.cli_path,
                prompt,
                "--session-id", self.session_id,
                "--output-format", "text",  # Could use "json" for structured output
            ]

            if allow_tools:
                # Enable all tools by default
                cmd.extend(["--tools", "default"])
                cmd.extend(["--permission-mode", permission_mode])
            else:
                # Disable tools
                cmd.extend(["--tools", ""])

            return cmd

        elif self.cli_name.lower() == "codex":
            # Codex session-based execution
            # For now, use exec mode - we'll enhance this later
            return [self.cli_path, "exec", prompt]

        else:
            raise ValueError(f"Unknown CLI name: {self.cli_name}")

    def _parse_output(self, output: str) -> tuple[str, List[ActionRecord]]:
        """
        Parse CLI output to extract text and actions taken.

        Args:
            output: Raw output from CLI

        Returns:
            Tuple of (text_output, list_of_actions)
        """
        # TODO: Parse structured output to identify actions
        # For now, return raw output with no actions
        # In the future, we can parse JSON output format or scan for action indicators

        actions = []

        # Simple heuristics for detecting actions (improve later)
        if "Writing" in output or "Created" in output:
            actions.append(ActionRecord("file_write", {"detected": True}))
        if "Editing" in output or "Modified" in output:
            actions.append(ActionRecord("file_edit", {"detected": True}))
        if "Running" in output or "Executing" in output:
            actions.append(ActionRecord("bash_command", {"detected": True}))

        return output, actions

    def _handle_timeout(self, execution_time: float) -> CLIResponse:
        """Handle timeout scenario."""
        return CLIResponse(
            success=False,
            output="",
            error=f"Command timed out after {self.timeout} seconds",
            execution_time=execution_time,
            timed_out=True
        )

    def _handle_error(self, error: Exception, execution_time: float) -> CLIResponse:
        """Handle execution error."""
        return CLIResponse(
            success=False,
            output="",
            error=str(error),
            execution_time=execution_time
        )

    def get_actions(self) -> List[ActionRecord]:
        """Get all actions taken in this session."""
        return self.actions

    def reset_session(self):
        """Reset session with a new ID."""
        self.session_id = str(uuid.uuid4())
        self.actions = []
        logger.info(f"Reset session to {self.session_id}")
