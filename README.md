# Python Project Boilerplate with UV

A modern Python project template using `uv` for package management and virtual environments, with comprehensive testing, documentation, and code quality tools pre-configured.

## Prerequisites

### System Requirements
- Python 3.8 or higher
- Git

### Required Tools
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- [pre-commit](https://pre-commit.com/) - Git hook manager

## Installation & Setup

1. **Install uv**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and Navigate to Project**
   ```bash
   git clone <your-repository-url>
   cd <project-directory>
   ```

3. **Create and Activate Virtual Environment**
   ```bash
   uv venv
   source .venv/bin/activate  # On Unix/macOS
   # .venv\Scripts\activate    # On Windows
   ```

4. **Install Dependencies**
   ```bash
   uv pip install -e .          # Install project in editable mode
   uv pip install pre-commit    # Install pre-commit
   pre-commit install           # Setup git hooks
   ```

## Development Workflow

### Code Style and Quality Tools

This project uses several tools to maintain code quality:

- **Black** - Code formatting
- **Ruff** - Fast Python linter
- **pre-commit hooks** for:
  - YAML validation
  - Large file checks
  - Trailing whitespace removal
  - Debug statement checks

### Pre-commit Configuration

The project includes pre-commit hooks for:
```yaml
- Code formatting (black)
- Linting (ruff)
- YAML validation
- Documentation checks
- Test coverage verification
- Project tracking updates
```

To run all checks manually:
```bash
pre-commit run --all-files
```

## Testing & Quality

### Running Tests
```bash
pytest
```

Tests are automatically run with coverage reporting. The project requires:
- Minimum 90% test coverage
- Branch coverage enabled
- Coverage reports in both terminal and XML formats

### Coverage Reports
```bash
pytest --cov=src --cov-report=term-missing --cov-report=xml
```

## Documentation

### Generate API Documentation
```bash
uv pip install pdoc
pdoc -o docs/ src/
```

### View Documentation
```bash
open docs/index.html
```

Documentation is automatically checked before commits using a custom pre-commit hook.

## Project Structure

```
project/
├── bin/                # Scripts and executable files
├── docs/              # Generated documentation
├── hooks/             # Custom git hooks
│   ├── check_docs.py          # Documentation verification
│   └── update_project_tracker.py # Project tracking
├── src/               # Source code
│   └── main.py              # Main application code
├── tests/             # Test files
├── .gitignore        # Git ignore rules
├── .pre-commit-config.yaml # Pre-commit hook configuration
├── LICENSE           # Project license
├── pyproject.toml   # Project configuration and dependencies
├── README.md        # This file
└── ruff.toml       # Ruff linter configuration
```

## Custom Hooks

### Project Tracker
- Automatically updates project metadata after commits
- Requirements: PyYAML, jsonschema

### Documentation Checker
- Verifies documentation is up to date
- Runs before commits
- Requirements: pdoc

## Contributing Guidelines

1. **Fork and Clone**
   - Fork the repository
   - Clone your fork locally

2. **Setup Development Environment**
   - Follow the installation steps above
   - Ensure all pre-commit hooks are installed

3. **Development Workflow**
   - Create a new branch for your feature
   - Write tests for your changes
   - Ensure documentation is updated
   - Make your changes
   - Run tests and ensure coverage requirements are met
   - Commit your changes (pre-commit hooks will run automatically)

4. **Code Standards**
   - Follow Black code style
   - Maintain test coverage above 90%
   - Update documentation for any new features
   - Ensure all pre-commit hooks pass

5. **Submit Pull Request**
   - Push changes to your fork
   - Create a pull request with a clear description
   - Ensure all checks pass
