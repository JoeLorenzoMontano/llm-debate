#!/usr/bin/env python3
"""Main entry point for CLI Debate Tool."""

import argparse
import logging
import sys
from pathlib import Path

from .config import DebateConfig
from .orchestrator import DebateOrchestrator
from .output.stream import StreamHandler
from .output.summary import SummaryHandler
from .output.markdown import MarkdownHandler


def setup_logging(log_level: str, log_file: str):
    """
    Setup logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure logging with both file and console handlers
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stderr)  # Log to stderr to keep stdout clean
        ]
    )


def create_parser() -> argparse.ArgumentParser:
    """
    Create argument parser for CLI.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Orchestrate debates between Claude Code and Codex CLIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Adversarial debate with streaming output
  cli-debate -m adversarial -r 8 "Is Python better than JavaScript for web development?"

  # Collaborative exploration with markdown export
  cli-debate -m collaborative -o stream markdown --markdown-path debate.md \\
      "Design patterns for microservices architecture"

  # Devil's advocate with summary only
  cli-debate -m devils_advocate -o summary -r 5 "Implement caching strategy"
        """
    )

    # Required arguments
    parser.add_argument(
        'topic',
        type=str,
        help='The debate topic or goal'
    )

    # Mode selection
    parser.add_argument(
        '-m', '--mode',
        choices=['adversarial', 'collaborative', 'devils_advocate'],
        default='adversarial',
        help='Debate interaction mode (default: adversarial)'
    )

    # Round limits
    parser.add_argument(
        '-r', '--max-rounds',
        type=int,
        default=10,
        help='Maximum number of debate rounds (default: 10)'
    )

    # Timeout
    parser.add_argument(
        '-t', '--timeout',
        type=int,
        default=120,
        help='Timeout per CLI call in seconds (default: 120)'
    )

    # Convergence settings
    parser.add_argument(
        '-c', '--convergence-threshold',
        type=float,
        default=0.85,
        help='Similarity threshold for convergence detection, 0.0-1.0 (default: 0.85)'
    )

    parser.add_argument(
        '--disable-convergence',
        action='store_true',
        help='Disable convergence detection (always run max rounds)'
    )

    # Output handlers
    parser.add_argument(
        '-o', '--output',
        nargs='+',
        choices=['stream', 'summary', 'markdown'],
        default=['stream'],
        help='Output handlers to use (default: stream)'
    )

    parser.add_argument(
        '--markdown-path',
        type=str,
        help='Path for markdown export (required if markdown output enabled)'
    )

    # CLI paths
    parser.add_argument(
        '--claude-bin',
        type=str,
        default='/home/jolomoadmin/.local/bin/claude',
        help='Path to claude CLI (default: /home/jolomoadmin/.local/bin/claude)'
    )

    parser.add_argument(
        '--codex-bin',
        type=str,
        default='/home/jolomoadmin/.npm-global/bin/codex',
        help='Path to codex CLI (default: /home/jolomoadmin/.npm-global/bin/codex)'
    )

    # Logging
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--log-file',
        type=str,
        default='debate.log',
        help='Path to log file (default: debate.log)'
    )

    return parser


def validate_args(args: argparse.Namespace) -> None:
    """
    Validate command-line arguments.

    Args:
        args: Parsed arguments

    Raises:
        ValueError: If validation fails
    """
    # Validate markdown output
    if 'markdown' in args.output and not args.markdown_path:
        raise ValueError("--markdown-path is required when 'markdown' output is enabled")

    # Validate convergence threshold
    if not 0.0 <= args.convergence_threshold <= 1.0:
        raise ValueError(f"Convergence threshold must be between 0.0 and 1.0, got {args.convergence_threshold}")

    # Validate max rounds
    if args.max_rounds < 1:
        raise ValueError(f"max-rounds must be at least 1, got {args.max_rounds}")

    # Validate timeout
    if args.timeout < 1:
        raise ValueError(f"timeout must be at least 1, got {args.timeout}")


def create_output_handlers(args: argparse.Namespace) -> list:
    """
    Create output handlers based on arguments.

    Args:
        args: Parsed arguments

    Returns:
        List of output handler instances
    """
    handlers = []

    for handler_name in args.output:
        if handler_name == 'stream':
            handlers.append(StreamHandler())
        elif handler_name == 'summary':
            handlers.append(SummaryHandler())
        elif handler_name == 'markdown':
            markdown_path = Path(args.markdown_path)
            handlers.append(MarkdownHandler(markdown_path))

    return handlers


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Validate arguments
        validate_args(args)

        # Setup logging
        setup_logging(args.log_level, args.log_file)
        logger = logging.getLogger(__name__)
        logger.info("CLI Debate Tool starting")

        # Create configuration
        config = DebateConfig(
            topic=args.topic,
            mode=args.mode,
            max_rounds=args.max_rounds,
            timeout_per_round=args.timeout,
            convergence_threshold=args.convergence_threshold,
            enable_convergence=not args.disable_convergence,
            output_handlers=args.output,
            markdown_output_path=Path(args.markdown_path) if args.markdown_path else None,
            claude_bin=args.claude_bin,
            codex_bin=args.codex_bin,
            log_level=args.log_level,
            log_file=args.log_file
        )

        logger.info(f"Configuration created: mode={config.mode}, topic={config.topic}")

        # Create orchestrator
        orchestrator = DebateOrchestrator(config)

        # Add output handlers
        handlers = create_output_handlers(args)
        for handler in handlers:
            orchestrator.add_output_handler(handler)

        logger.info(f"Added {len(handlers)} output handler(s)")

        # Run debate
        result = orchestrator.run_debate()

        logger.info(f"Debate completed: {result.total_rounds} rounds, {result.end_reason}")

        # Exit with success
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nDebate interrupted by user.")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
