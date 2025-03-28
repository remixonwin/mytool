# MyTool

A Python project using uv package manager for dependency management and virtual environments.

## Setup

This project uses `uv` for package management and virtual environments. Follow these steps to get started:

1. Activate the virtual environment:
```bash
source .venv/bin/activate
```

2. Install development dependencies:
```bash
uv pip install pytest
```

## Development

The project structure is:
- `src/`: Source code directory
- `tests/`: Test files directory

## Testing

Run tests using:
```bash
pytest
```

## Documentation

Generate API documentation:
```bash
uv pip install pdoc && pdoc -o docs/ src/
```

Serve documentation locally:
```bash
open docs/index.html```
