# AGENTS.md

## Build/Lint/Test Commands
```bash
# Single test: python -m unittest tests.unit.test_note -v
# All tests: python -m unittest tests.unit.test_*.py -v
# Lint: ruff check src/
# Format: ruff format src/
# Type check: pyright
```

## Project Context
**RAG Micro-Agent** - 3-stage pipeline: Query Planning → Context Retrieval → Packaging. Status: ⚠️ WIP - components work but pipeline incomplete. Missing embedding generation and ChromaDB population.

## Code Style Guidelines
- **Imports**: Standard lib → third-party → first-party (isort enforced)
- **Formatting**: 88 char line limit, double quotes, 4-space indent (ruff)
- **Types**: Use type hints, prefer `list[str]` over `List[str]` (PEP 604)
- **Naming**: snake_case functions/vars, PascalCase classes, UPPER_SNAKE_CASE constants
- **Error handling**: Use specific exceptions, avoid bare except, log with context
- **Docstrings**: Google style, required for public functions/classes
- **Tests**: Place in tests/unit/ or tests/integration/, use unittest.TestCase