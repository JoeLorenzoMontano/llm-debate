# Contributing to CLI Debate Tool

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/cli-debate.git
   cd cli-debate
   ```
3. **Install in development mode**:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

### Setting Up Your Environment

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines below

3. **Write tests** for your changes in the `tests/` directory

4. **Run tests** to ensure everything works:
   ```bash
   pytest
   ```

5. **Commit your changes** with clear, descriptive messages:
   ```bash
   git add .
   git commit -m "Add feature: description of what you added"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request** on GitHub with:
   - Clear description of the changes
   - Reference to any related issues
   - Screenshots/examples if applicable

## Code Style Guidelines

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints where possible
- Write docstrings for all public functions/classes
- Keep functions focused and under ~50 lines
- Use meaningful variable and function names

### Example Code Style

```python
"""Module docstring describing the purpose."""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class MyClass:
    """Class docstring describing the class."""

    def __init__(self, param: str):
        """
        Initialize the class.

        Args:
            param: Description of parameter
        """
        self.param = param
        logger.info(f"Initialized with {param}")

    def my_method(self, input_data: List[str]) -> Optional[str]:
        """
        Method docstring.

        Args:
            input_data: List of input strings

        Returns:
            Processed string or None if empty
        """
        if not input_data:
            return None
        return " ".join(input_data)
```

## Testing Guidelines

- Write unit tests for new functionality
- Ensure tests are fast (mock external CLIs)
- Use meaningful test names: `test_convergence_detection_with_agreement_phrases`
- Aim for >80% code coverage

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cli_debate

# Run specific test file
pytest tests/test_orchestrator.py

# Run with verbose output
pytest -v
```

## Adding New Features

### New Debate Mode

1. Create new file in `cli_debate/modes/`
2. Inherit from `DebateMode` base class
3. Implement required methods
4. Add to mode registry in `orchestrator.py`
5. Add tests in `tests/test_modes.py`
6. Update README with examples

### New Output Handler

1. Create new file in `cli_debate/output/`
2. Inherit from `OutputHandler` base class
3. Implement event methods
4. Add to handler creation in `main.py`
5. Add tests
6. Update README

## Commit Message Guidelines

Use clear, descriptive commit messages:

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes
- **test**: Adding or updating tests
- **refactor**: Code refactoring
- **style**: Code style changes (formatting, etc.)
- **chore**: Maintenance tasks

### Examples

```
feat: Add support for multi-agent debates (3+ CLIs)
fix: Convergence detection not triggering on agreement phrases
docs: Update README with action mode examples
test: Add integration tests for git safety
refactor: Extract prompt building into separate module
```

## Pull Request Process

1. **Update documentation** if you've added features
2. **Add tests** for new functionality
3. **Ensure all tests pass**
4. **Update CHANGELOG.md** with your changes
5. **Get review** from at least one maintainer
6. **Address feedback** and push updates
7. **Squash commits** if requested before merging

## Reporting Bugs

When reporting bugs, please include:

- **Description** of the bug
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Environment** (OS, Python version, CLI versions)
- **Logs** (if applicable)

### Bug Report Template

```markdown
**Description**
A clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. Run `cli-debate ...`
2. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.10]
- Claude Code: [e.g., 1.2.3]
- Codex: [e.g., 0.5.0]

**Logs**
```
[Paste relevant logs]
```
```

## Feature Requests

Feature requests are welcome! Please:

- **Check existing issues** first
- **Describe the use case** clearly
- **Explain the benefit** to users
- **Consider implementation** complexity

## Questions?

- Open an issue with the `question` label
- Start a discussion in GitHub Discussions
- Check existing documentation first

## Code of Conduct

- Be respectful and inclusive
- Assume good intentions
- Provide constructive feedback
- Focus on the code, not the person
- Help create a welcoming community

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing!** 🎉
