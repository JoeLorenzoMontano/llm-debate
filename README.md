# LLM Debate Tool

> Orchestrate debates and discussions between Claude Code and Codex CLIs with configurable interaction modes, convergence detection, and real-time action-taking.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Non-Commercial](https://img.shields.io/badge/License-Non--Commercial-red.svg)](LICENSE)

## Overview

The LLM Debate Tool enables two AI CLIs to engage in:
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
git clone https://github.com/yourusername/llm-debate.git
cd llm-debate
pip install -e .
```

### Verify Installation

```bash
llm-debate --help
```

## Quick Start

### Basic Debate (Discussion Only)

```bash
# Adversarial debate
llm-debate "Is Python better than JavaScript for web development?"

# Collaborative exploration (5 rounds)
llm-debate -m collaborative -r 5 "Design patterns for microservices"

# Devil's advocate
llm-debate -m devils_advocate "Implement caching strategy for our API"
```

### Action Mode (Code Changes)

```bash
# Collaborative refactoring with real code changes
llm-debate --action-mode \
    -m collaborative -r 5 \
    "Refactor the error handling in cli_executor.py"

# Adversarial code review with changes
llm-debate --action-mode \
    --git-branch review-session \
    -m adversarial \
    "Review and improve the convergence detection algorithm"
```

## Usage

### Command-Line Options

```bash
llm-debate [OPTIONS] "topic"
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
llm-debate -m adversarial -r 5 \
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
llm-debate -m collaborative -o stream markdown \
    --markdown-path architecture-discussion.md \
    -r 8 \
    "How should we structure error handling in microservices?"
```

This will:
1. Display real-time streaming output
2. Export complete transcript to `architecture-discussion.md`

#### Example 3: Action Mode - Real Code Refactoring

```bash
llm-debate --action-mode \
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
  ✏️  Modified: llm_debate/cli_executor.py
    - Extracted ExecutorInterface
    - Added dependency injection
    + 45 lines, - 12 lines

  📝 Created: llm_debate/executor_interface.py
    - Defined abstract interface
    + 28 lines

  ✅ Committed: a3f2c1b "Round 1 - claude changes"
```

## Web UI 🌐

### NEW: Real-Time Web Interface

Experience debates with a beautiful, real-time web interface!

**Features:**
- 🎨 Modern, responsive UI
- ⚡ Real-time WebSocket streaming
- 📊 Live progress tracking
- 💾 Export transcripts to markdown
- 🎛️ Easy configuration
- 📱 Mobile-friendly

### Quick Start

**Option 1: Using the startup script**
```bash
./run-web.sh
```

**Option 2: Manual start**
```bash
# Install web dependencies
pip install -r web/requirements.txt

# Start the server
uvicorn web.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Option 3: Docker**
```bash
docker-compose up
```

Then open your browser to: **http://localhost:8000**

### Using the Web UI

1. **Configure Your Debate**
   - Enter your debate topic
   - Select mode (Adversarial, Collaborative, or Devil's Advocate)
   - Adjust max rounds and timeout
   - Enable/disable convergence detection
   - Toggle action mode for real code changes

2. **Start the Debate**
   - Click "Start Debate"
   - Watch the real-time conversation unfold
   - See color-coded responses (Claude in blue, Codex in green)

3. **Export Results**
   - Click "Export Transcript" to download markdown
   - Automatically includes all turns with timestamps

### Screenshots

**Main Interface:**
```
┌─────────────────────────────────────────────────────────┐
│  🎛️ Configuration Panel    │  💬 Live Debate View      │
│  ┌──────────────────────┐  │  ┌───────────────────────┐│
│  │ Debate Topic         │  │  │ Round 1 - CLAUDE      ││
│  │ Mode: Collaborative  │  │  │ [Blue] Response...    ││
│  │ Max Rounds: 5        │  │  │                       ││
│  │ [Start Debate]       │  │  │ Round 2 - CODEX       ││
│  └──────────────────────┘  │  │ [Green] Response...   ││
└─────────────────────────────────────────────────────────┘
```

### API Endpoints

The web UI also exposes a REST API:

**Start a debate:**
```bash
curl -X POST http://localhost:8000/api/debates/start \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Your debate topic",
    "mode": "collaborative",
    "max_rounds": 5
  }'
```

**Get debate status:**
```bash
curl http://localhost:8000/api/debates/{debate_id}/status
```

**Health check:**
```bash
curl http://localhost:8000/health
```

## Using from Claude Code

You can invoke debates directly from Claude Code! Just ask naturally:

```
"Can you run a debate on whether we should use Docker for this project?"

"Start a collaborative discussion about our error handling patterns"

"Run a devil's advocate session on the new API design"
```

Claude Code will recognize the `llm-debate` command and execute it for you.

## Architecture

```
llm-debate/
├── llm_debate/
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
pytest --cov=llm_debate
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
llm-debate --claude-bin /path/to/claude --codex-bin /path/to/codex "topic"
```

### Timeout Issues

```bash
# Increase timeout (in seconds)
llm-debate -t 300 "topic"
```

### Action Mode: Permission Denied

```bash
# Use bypass permissions mode (careful!)
llm-debate --action-mode --permission-mode bypassPermissions "topic"
```

### Git Not a Repository

Action mode requires a git repository:

```bash
cd your-project
git init  # If not already a git repo
llm-debate --action-mode "refactor this code"
```

## License

**Non-Commercial License** - This software is licensed for personal, educational, and research use only. Commercial use is prohibited.

See [LICENSE](LICENSE) file for full terms. For commercial licensing inquiries, please contact the copyright holders.

## Credits

Built with:
- [Claude Code](https://claude.ai/claude-code) by Anthropic
- [Codex](https://codex.anthropic.com) by Anthropic

## Citation

If you use this tool in your research or project, please cite:

```bibtex
@software{llm_debate_tool,
  title = {LLM Debate Tool: Multi-Agent AI Debates with Action-Taking},
  year = {2026},
  url = {https://github.com/yourusername/llm-debate}
}
```

---

**Made with ❤️ for the AI agent community**
