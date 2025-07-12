
# RAG Micro-Agent for Personal Knowledge Management

This project implements a specialized RAG (Retrieval-Augmented Generation) micro-agent designed to provide a parent Language Model with precise, structured context from a personal knowledge base (like an Obsidian vault).

## Getting Started

This project uses `uv` for virtual environment and dependency management.

### Prerequisites
- Python 3.10+
- `uv` installed (`pip install uv`)

### Setup & Installation

1.  **Create and activate the virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    The project's dependencies are defined in `pyproject.toml`. Use `uv` to sync your environment with the locked dependencies in `uv.lock`.
    ```bash
    uv pip sync
    ```

### Running Tests

To run the test suite, use the following command from the project's root directory:

```bash
uv run python -m unittest discover obsidian-rag-project/tests
```

## Project Overview

See the [Product Requirements Document (PRD.md)](PRD.md) for a detailed overview of the project's vision, problem statement, and solution approach.

## Technical Details

For a breakdown of the modules, functions, and data structures, refer to the [Technical Specification](technical-spec.md).

## Development Plan

The project is being developed across three key milestones, as outlined in the [Roadmap](roadmap.md).
