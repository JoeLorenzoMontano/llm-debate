# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Web UI with real-time streaming** 🎉
  - FastAPI backend with WebSocket support
  - Beautiful, responsive frontend with Tailwind CSS
  - Live debate visualization with color-coded responses
  - Real-time progress tracking
  - Markdown export functionality
  - Docker support for easy deployment
- Session-based CLI executor for action mode
- Action tracking module for monitoring file changes
- Git safety features (branching, auto-commit, rollback)
- Action mode configuration settings
- REST API endpoints for programmatic access

## [0.1.0] - 2026-04-08

### Added
- Initial release of LLM Debate Tool
- Three debate modes: adversarial, collaborative, devils_advocate
- Automatic convergence detection
  - Semantic similarity analysis
  - Agreement phrase detection
  - Repetition detection
- Multiple output handlers
  - Real-time streaming with colored output
  - Summary-only mode
  - Markdown export
- CLI executor with timeout and error handling
- Orchestrator with debate loop management
- Configuration validation
- Emergency brake for infinite loop prevention
- Context management (last 3 rounds)
- Comprehensive logging
- Command-line interface with argparse
- Package installation via setup.py
- Complete documentation

### Features
- Debate between Claude Code and Codex CLIs
- Configurable round limits
- Convergence threshold tuning
- Custom CLI binary paths
- Session persistence via CLI session IDs
- Git-based safety for code changes

### Documentation
- README with installation and usage examples
- Contributing guidelines
- MIT License
- Architecture overview
- Troubleshooting guide

## Development Phases

### Phase 1: Core Debate System ✅
- Basic orchestration
- Three debate modes
- Convergence detection
- Output handling

### Phase 2: Action Mode 🚧 (In Progress)
- Session-based execution
- File change tracking
- Git safety integration
- Real-time code modifications

### Phase 3: Future Enhancements 🎯
- Web UI with streaming
- Docker containerization
- Multi-agent support (3+ CLIs)
- Additional CLI integrations
- Advanced metrics and scoring
- Session replay capability
- REST API

---

[Unreleased]: https://github.com/yourusername/llm-debate/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/llm-debate/releases/tag/v0.1.0
