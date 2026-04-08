# CLI Debate Tool

> Orchestrate debates and discussions between Claude Code and Codex CLIs with configurable interaction modes, convergence detection, and real-time action-taking.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

The CLI Debate Tool enables two AI CLIs to engage in:
- **Adversarial debates** - Opposing viewpoints, rigorous argumentation
- **Collaborative explorations** - Building on each other's ideas
- **Devil's advocate discussions** - One proposes, one critiques

**New:** Action Mode (Phase 2) - CLIs can actually make changes, edit code, and take actions during debates!

## Features

### Core Debate Features
- ✅ Three debate modes (adversarial, collaborative, devil's advocate)
- ✅ Automatic convergence detection
- ✅ Configurable round limits to prevent infinite loops
- ✅ Multiple output formats (streaming, summary, markdown export)
- ✅ Timeout handling and error recovery
- ✅ Detailed logging
- ✅ Colored console output

### Action Mode Features (Phase 2)
- 🔥 Real-time code editing and refactoring
- 🔥 Git safety with automatic branching
- 🔥 Action tracking (file changes, diffs, commands)
- 🔥 Auto-commit per turn with rollback capability
- 🔥 Session-based execution with full tool access

## Use Cases

- Multi-perspective analysis of technical decisions
- Code review and refactoring with AI pair programming
- Brainstorming and ideation
- Exploring complex topics from different angles
- Automated code improvements with safety guarantees

## Installation

### Prerequisites

- Python 3.8 or higher
- [Claude Code CLI](https://docs.claude.ai/claude-code) installed and configured
- [Codex CLI](https://codex.anthropic.com) installed and configured
- Git (for action mode)

### Install from Source

```bash
git clone https://github.com/yourusername/cli-debate.git
cd cli-debate
pip install -e .
```

### Verify Installation

```bash
cli-debate --help
```

## Quick Start

### Basic Debate (Discussion Only)

```bash
# Adversarial debate
cli-debate "Is Python better than JavaScript for web development?"

# Collaborative exploration (5 rounds)
cli-debate -m collaborative -r 5 "Design patterns for microservices"

# Devil's advocate
cli-debate -m devils_advocate "Implement caching strategy for our API"
```

### Action Mode (Code Changes)

```bash
# Collaborative refactoring with real code changes
cli-debate --action-mode \
    -m collaborative -r 5 \
    "Refactor the error handling in cli_executor.py"

# Adversarial code review with changes
cli-debate --action-mode \
    --git-branch review-session \
    -m adversarial \
    "Review and improve the convergence detection algorithm"
```

## Usage

### Command-Line Options

```bash
cli-debate [OPTIONS] "topic"
```

**Required:**
- `topic` - The debate topic or question

**Mode Selection:**
- `-m, --mode` - Debate mode: `adversarial`, `collaborative`, `devils_advocate` (default: adversarial)

**Round Limits:**
- `-r, --max-rounds` - Maximum number of rounds (default: 10)
- `-t, --timeout` - Timeout per CLI call in seconds (default: 120)

**Convergence:**
- `-c, --convergence-threshold` - Similarity threshold 0.0-1.0 (default: 0.85)
- `--disable-convergence` - Disable convergence detection

**Output:**
- `-o, --output` - Output handlers: `stream`, `summary`, `markdown` (default: stream)
- `--markdown-path` - Path for markdown export

**Action Mode (Phase 2):**
- `--action-mode` - Enable real-time code changes and tool use
- `--git-branch` - Custom git branch name (auto-generated if omitted)
- `--permission-mode` - Claude permission mode (default: acceptEdits)
- `--no-auto-commit` - Disable auto-commit per turn

**Logging:**
- `--log-level` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `--log-file` - Path to log file (default: debate.log)

### Examples

#### Example 1: Quick Adversarial Debate

```bash
cli-debate -m adversarial -r 5 \
    "Microservices are better than monoliths"
```

**Output:**
```
================================================================================
CLI DEBATE
================================================================================

Topic: Microservices are better than monoliths
Mode: adversarial
Max Rounds: 5

[Round 1] CLAUDE is responding...
[Claude argues FOR microservices...]

[Round 2] CODEX is responding...
[Codex argues AGAINST microservices...]

...

✓ Convergence Detected!
Reason: Agreement detected in recent responses
```

#### Example 2: Collaborative Exploration with Export

```bash
cli-debate -m collaborative -o stream markdown \
    --markdown-path architecture-discussion.md \
    -r 8 \
    "How should we structure error handling in microservices?"
```

This will:
1. Display real-time streaming output
2. Export complete transcript to `architecture-discussion.md`

#### Example 3: Action Mode - Real Code Refactoring

```bash
cli-debate --action-mode \
    --git-branch refactor-experiment \
    -m collaborative -r 5 \
    "Refactor the CLI executor module to improve testability"
```

**What happens:**
1. Creates git branch `refactor-experiment-20260408-123456`
2. Claude and Codex take turns making actual code changes
3. Each turn auto-commits changes
4. File diffs shown in output
5. If successful → merge to main
6. If fails → rollback all changes

**Output:**
```
[Round 1] CLAUDE is responding...

Analyzing cli_executor.py... I'll extract interfaces for better testability.

ACTIONS TAKEN:
  ✏️  Modified: cli_debate/cli_executor.py
    - Extracted ExecutorInterface
    - Added dependency injection
    + 45 lines, - 12 lines

  📝 Created: cli_debate/executor_interface.py
    - Defined abstract interface
    + 28 lines

  ✅ Committed: a3f2c1b "Round 1 - claude changes"
```

## Using from Claude Code

You can invoke debates directly from Claude Code! Just ask naturally:

```
"Can you run a debate on whether we should use Docker for this project?"

"Start a collaborative discussion about our error handling patterns"

"Run a devil's advocate session on the new API design"
```

Claude Code will recognize the `cli-debate` command and execute it for you.

## Architecture

```
cli-debate/
├── cli_debate/
│   ├── main.py                 # CLI entry point
│   ├── config.py               # Configuration classes
│   ├── orchestrator.py         # Main debate loop
│   ├── cli_executor.py         # Basic CLI subprocess wrapper
│   ├── session_executor.py     # Session-based executor (action mode)
│   ├── action_tracker.py       # Track file changes and actions
│   ├── git_safety.py           # Git branching and rollback
│   ├── modes/                  # Debate modes
│   │   ├── adversarial.py
│   │   ├── collaborative.py
│   │   └── devils_advocate.py
│   ├── convergence/            # Convergence detection
│   │   └── detector.py
│   └── output/                 # Output handlers
│       ├── stream.py
│       ├── summary.py
│       └── markdown.py
├── tests/
├── requirements.txt
├── setup.py
├── LICENSE
└── README.md
```

## How It Works

### Discussion Mode

1. **Initialization**: CLIs are configured with timeout settings
2. **Debate Loop**: For each round (up to max-rounds):
   - Generate appropriate prompt based on mode and history
   - Execute CLI (alternating: Claude → Codex → Claude...)
   - Store response in conversation history
   - Check for convergence
3. **Convergence Detection**:
   - Agreement phrases ("I agree", "consensus", etc.)
   - Semantic similarity using difflib
   - Repetition detection
4. **Emergency Brake**: If last 5 responses >95% identical, force exit

### Action Mode

1. **Git Safety**: Creates debate branch, saves original
2. **Turn Execution**: CLI runs with full tool access
3. **Action Tracking**: Monitors file changes via git
4. **Auto-Commit**: Commits changes after each turn
5. **Convergence**: Can rollback if debate fails
6. **Merge or Rollback**: User decides whether to keep changes

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=cli_debate
```

### Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

### Completed ✅
- [x] Core debate orchestration
- [x] Three debate modes
- [x] Convergence detection
- [x] Multiple output handlers
- [x] Session-based execution
- [x] Git safety features
- [x] Action tracking

### In Progress 🚧
- [ ] Output handlers for action display
- [ ] Full integration of action mode
- [ ] Comprehensive testing

### Future 🎯
- [ ] Web UI with real-time streaming
- [ ] Docker containerization
- [ ] Support for additional CLIs (GPT-4, Gemini, etc.)
- [ ] Multi-agent debates (3+ participants)
- [ ] Custom scoring/evaluation metrics
- [ ] Session persistence and replay
- [ ] API for programmatic access

## Troubleshooting

### CLI Not Found

```bash
# Verify CLI paths
which claude
which codex

# Specify custom paths
cli-debate --claude-bin /path/to/claude --codex-bin /path/to/codex "topic"
```

### Timeout Issues

```bash
# Increase timeout (in seconds)
cli-debate -t 300 "topic"
```

### Action Mode: Permission Denied

```bash
# Use bypass permissions mode (careful!)
cli-debate --action-mode --permission-mode bypassPermissions "topic"
```

### Git Not a Repository

Action mode requires a git repository:

```bash
cd your-project
git init  # If not already a git repo
cli-debate --action-mode "refactor this code"
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Built with:
- [Claude Code](https://claude.ai/claude-code) by Anthropic
- [Codex](https://codex.anthropic.com) by Anthropic

## Citation

If you use this tool in your research or project, please cite:

```bibtex
@software{cli_debate_tool,
  title = {CLI Debate Tool: Multi-Agent AI Debates with Action-Taking},
  year = {2026},
  url = {https://github.com/yourusername/cli-debate}
}
```

---

**Made with ❤️ for the AI agent community**
