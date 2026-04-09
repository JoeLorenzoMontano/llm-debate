"""Pull Request context fetching and management."""

import logging
import subprocess
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PRContext:
    """Pull request context information."""

    pr_number: int
    title: str
    body: str
    state: str
    author: str
    base_branch: str
    head_branch: str
    url: str
    diff: str
    files_changed: int
    additions: int
    deletions: int
    comments: list
    repository: Optional[str] = None

    def format_for_debate(self) -> str:
        """
        Format PR context for inclusion in debate prompts.

        Returns:
            Formatted PR context string
        """
        context = f"""
# Pull Request Context

**PR #{self.pr_number}: {self.title}**
**URL:** {self.url}
**Author:** {self.author}
**Status:** {self.state}
**Branch:** {self.head_branch} → {self.base_branch}

## Description
{self.body or "(No description provided)"}

## Changes Summary
- **Files Changed:** {self.files_changed}
- **Additions:** +{self.additions}
- **Deletions:** -{self.deletions}

## Code Changes
```diff
{self.diff[:5000]}{"..." if len(self.diff) > 5000 else ""}
```
"""

        if self.comments:
            context += "\n## Review Comments\n"
            for comment in self.comments[:10]:  # Limit to first 10 comments
                context += f"\n**{comment.get('author', 'Unknown')}:** {comment.get('body', '')}\n"

        return context


class PRContextFetcher:
    """Fetch pull request context using GitHub CLI."""

    def __init__(self, gh_bin: str = "gh"):
        """
        Initialize PR context fetcher.

        Args:
            gh_bin: Path to gh CLI binary
        """
        self.gh_bin = gh_bin
        self._verify_gh_cli()

    def _verify_gh_cli(self):
        """Verify that gh CLI is installed and authenticated."""
        try:
            result = subprocess.run(
                [self.gh_bin, "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError(
                    "GitHub CLI is not authenticated. Run 'gh auth login' first."
                )
            logger.info("GitHub CLI authentication verified")
        except FileNotFoundError:
            raise RuntimeError(
                f"GitHub CLI not found at {self.gh_bin}. "
                "Install it from https://cli.github.com/"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("GitHub CLI auth check timed out")

    def fetch_pr_context(self, pr_identifier: str, repo: Optional[str] = None) -> PRContext:
        """
        Fetch PR context from GitHub.

        Args:
            pr_identifier: PR number or URL
            repo: Repository in format 'owner/repo' (optional if in repo directory)

        Returns:
            PRContext object with all PR information

        Raises:
            RuntimeError: If PR fetch fails
        """
        logger.info(f"Fetching PR context for: {pr_identifier}")

        # Extract PR number from URL if provided
        pr_number = self._extract_pr_number(pr_identifier)

        # Build gh pr view command
        cmd = [self.gh_bin, "pr", "view", str(pr_number), "--json",
               "number,title,body,state,author,baseRefName,headRefName,url,additions,deletions,files"]

        if repo:
            cmd.extend(["--repo", repo])

        try:
            # Fetch PR metadata
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            pr_data = json.loads(result.stdout)
            logger.debug(f"PR metadata fetched: {pr_data.get('title')}")

            # Fetch PR diff
            diff = self._fetch_pr_diff(pr_number, repo)

            # Fetch PR comments
            comments = self._fetch_pr_comments(pr_number, repo)

            # Create PRContext object
            return PRContext(
                pr_number=pr_data["number"],
                title=pr_data["title"],
                body=pr_data.get("body", ""),
                state=pr_data["state"],
                author=pr_data["author"]["login"],
                base_branch=pr_data["baseRefName"],
                head_branch=pr_data["headRefName"],
                url=pr_data["url"],
                diff=diff,
                files_changed=len(pr_data.get("files", [])),
                additions=pr_data.get("additions", 0),
                deletions=pr_data.get("deletions", 0),
                comments=comments,
                repository=repo
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to fetch PR: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("PR fetch timed out")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse PR data: {e}")
        except KeyError as e:
            raise RuntimeError(f"Unexpected PR data format: missing {e}")

    def _extract_pr_number(self, pr_identifier: str) -> int:
        """
        Extract PR number from identifier (number or URL).

        Args:
            pr_identifier: PR number or URL

        Returns:
            PR number as integer
        """
        # If it's already a number
        if pr_identifier.isdigit():
            return int(pr_identifier)

        # Extract from URL like https://github.com/owner/repo/pull/123
        if "github.com" in pr_identifier and "/pull/" in pr_identifier:
            parts = pr_identifier.rstrip("/").split("/")
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                raise ValueError(f"Could not extract PR number from URL: {pr_identifier}")

        raise ValueError(f"Invalid PR identifier: {pr_identifier}. Use PR number or GitHub URL.")

    def _fetch_pr_diff(self, pr_number: int, repo: Optional[str] = None) -> str:
        """
        Fetch PR diff using gh CLI.

        Args:
            pr_number: PR number
            repo: Repository in format 'owner/repo'

        Returns:
            Diff string
        """
        cmd = [self.gh_bin, "pr", "diff", str(pr_number)]
        if repo:
            cmd.extend(["--repo", repo])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            logger.debug(f"PR diff fetched: {len(result.stdout)} bytes")
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to fetch PR diff: {e.stderr}")
            return "(Diff unavailable)"
        except subprocess.TimeoutExpired:
            logger.warning("PR diff fetch timed out")
            return "(Diff fetch timed out)"

    def _fetch_pr_comments(self, pr_number: int, repo: Optional[str] = None) -> list:
        """
        Fetch PR review comments using gh CLI.

        Args:
            pr_number: PR number
            repo: Repository in format 'owner/repo'

        Returns:
            List of comment dictionaries
        """
        cmd = [self.gh_bin, "api", f"repos/{repo}/pulls/{pr_number}/comments" if repo else f"pulls/{pr_number}/comments"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            comments = json.loads(result.stdout)
            logger.debug(f"Fetched {len(comments)} PR comments")
            return [
                {
                    "author": c.get("user", {}).get("login", "Unknown"),
                    "body": c.get("body", ""),
                    "path": c.get("path", ""),
                    "line": c.get("line")
                }
                for c in comments
            ]
        except (subprocess.CalledProcessError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Failed to fetch PR comments: {e}")
            return []

    def checkout_pr_branch(self, pr_number: int, repo: Optional[str] = None) -> bool:
        """
        Checkout the PR branch locally using gh CLI.

        Args:
            pr_number: PR number
            repo: Repository in format 'owner/repo'

        Returns:
            True if successful, False otherwise
        """
        cmd = [self.gh_bin, "pr", "checkout", str(pr_number)]
        if repo:
            cmd.extend(["--repo", repo])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                check=True
            )
            logger.info(f"Successfully checked out PR #{pr_number}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to checkout PR branch: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("PR checkout timed out")
            return False
