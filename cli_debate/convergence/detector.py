"""Convergence detection for debates."""

import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..orchestrator import Turn


logger = logging.getLogger(__name__)


@dataclass
class ConvergenceResult:
    """Result of convergence detection."""

    is_converged: bool
    reason: str
    confidence: float


class ConvergenceDetector:
    """Detects when a debate has converged or reached conclusion."""

    # Agreement phrases to look for
    AGREEMENT_PHRASES = [
        r"\bI agree\b",
        r"\byou'?re right\b",
        r"\bthat'?s correct\b",
        r"\bwe can conclude\b",
        r"\bin conclusion\b",
        r"\bconsensus\b",
        r"\bwe both agree\b",
        r"\byou make a good point\b",
        r"\bI concur\b",
        r"\bexactly\b",
        r"\bprecisely\b",
        r"\bI accept that\b",
        r"\byou'?ve convinced me\b"
    ]

    def __init__(self, threshold: float = 0.85):
        """
        Initialize convergence detector.

        Args:
            threshold: Similarity threshold (0.0-1.0) for convergence
        """
        self.threshold = threshold
        logger.debug(f"Convergence detector initialized with threshold {threshold}")

    def check_convergence(self, history: List["Turn"]) -> ConvergenceResult:
        """
        Check if the debate has converged.

        Args:
            history: List of turns

        Returns:
            ConvergenceResult indicating whether convergence detected
        """
        if len(history) < 2:
            return ConvergenceResult(False, "Not enough history", 0.0)

        # Check for agreement phrases first (highest priority)
        agreement_result = self._detect_agreement_phrases(history)
        if agreement_result.is_converged:
            logger.info(f"Convergence detected via agreement: {agreement_result.reason}")
            return agreement_result

        # Check for repetition (medium priority)
        repetition_result = self._detect_repetition(history)
        if repetition_result.is_converged:
            logger.info(f"Convergence detected via repetition: {repetition_result.reason}")
            return repetition_result

        # Check for semantic similarity (lower priority)
        similarity_result = self._detect_similarity(history)
        if similarity_result.is_converged:
            logger.info(f"Convergence detected via similarity: {similarity_result.reason}")
            return similarity_result

        return ConvergenceResult(False, "No convergence detected", 0.0)

    def _detect_agreement_phrases(self, history: List["Turn"]) -> ConvergenceResult:
        """
        Detect explicit agreement phrases in recent responses.

        Args:
            history: List of turns

        Returns:
            ConvergenceResult
        """
        # Check last 2-4 responses
        recent_turns = history[-4:]

        agreement_count = 0
        total_checked = 0

        for turn in recent_turns:
            if not turn.success:
                continue

            response_lower = turn.response.lower()
            for pattern in self.AGREEMENT_PHRASES:
                if re.search(pattern, response_lower, re.IGNORECASE):
                    agreement_count += 1
                    logger.debug(f"Agreement phrase found in {turn.cli_name} response: {pattern}")
                    break  # Count each turn only once

            total_checked += 1

        # If 50%+ of recent responses contain agreement phrases
        if total_checked > 0 and agreement_count / total_checked >= 0.5:
            confidence = agreement_count / total_checked
            return ConvergenceResult(
                True,
                f"Agreement detected in {agreement_count}/{total_checked} recent responses",
                confidence
            )

        return ConvergenceResult(False, "No agreement phrases detected", 0.0)

    def _detect_repetition(self, history: List["Turn"]) -> ConvergenceResult:
        """
        Detect repetitive responses indicating circular argument.

        Args:
            history: List of turns

        Returns:
            ConvergenceResult
        """
        if len(history) < 3:
            return ConvergenceResult(False, "Not enough history for repetition check", 0.0)

        # Get last 3 successful responses
        recent_successful = [t for t in history[-6:] if t.success]
        if len(recent_successful) < 3:
            return ConvergenceResult(False, "Not enough successful responses", 0.0)

        last_three = recent_successful[-3:]
        responses = [turn.response for turn in last_three]

        # Calculate pairwise similarities
        similarities = []
        for i in range(len(responses) - 1):
            ratio = self._calculate_similarity(responses[i], responses[i + 1])
            similarities.append(ratio)

        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0

        # If last 3 responses are >90% similar, it's likely repetition
        if avg_similarity > 0.90:
            return ConvergenceResult(
                True,
                f"Repetition detected - last 3 responses {avg_similarity:.2%} similar",
                avg_similarity
            )

        return ConvergenceResult(False, "No repetition detected", avg_similarity)

    def _detect_similarity(self, history: List["Turn"]) -> ConvergenceResult:
        """
        Detect semantic similarity between recent responses from each CLI.

        Args:
            history: List of turns

        Returns:
            ConvergenceResult
        """
        if len(history) < 4:
            return ConvergenceResult(False, "Not enough history for similarity check", 0.0)

        # Get last response from each CLI
        claude_responses = [t for t in history if t.cli_name.lower() == "claude" and t.success]
        codex_responses = [t for t in history if t.cli_name.lower() == "codex" and t.success]

        if not claude_responses or not codex_responses:
            return ConvergenceResult(False, "Missing responses from one or both CLIs", 0.0)

        # Compare last response from each
        last_claude = claude_responses[-1].response
        last_codex = codex_responses[-1].response

        similarity = self._calculate_similarity(last_claude, last_codex)

        logger.debug(f"Similarity between last Claude and Codex responses: {similarity:.2%}")

        if similarity >= self.threshold:
            return ConvergenceResult(
                True,
                f"High similarity ({similarity:.2%}) between CLI responses",
                similarity
            )

        return ConvergenceResult(False, f"Similarity {similarity:.2%} below threshold", similarity)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity ratio between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity ratio (0.0-1.0)
        """
        # Use SequenceMatcher from difflib (stdlib)
        matcher = SequenceMatcher(None, text1.lower(), text2.lower())
        return matcher.ratio()
