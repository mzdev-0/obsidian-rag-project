# RAG Sub-Agent CLI Implementation Plan

Based on my analysis of the current codebase and requirements, here's a comprehensive implementation plan for the new main.py CLI entrypoint:

## 1. CLI Architecture Overview

### Design Philosophy
- **Git-style CLI**: Commands organized by function with clear subcommands
- **Progressive disclosure**: Simple commands for basic use, advanced options for power users
- **Fail-fast validation**: Validate inputs early with clear error messages
- **Consistent UX**: Uniform patterns across all commands

### CLI Structure
```
rag-agent [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGUMENTS...]
```

## 2. Command Structure

### Global Options
```bash
--config PATH          # Configuration file path
--collection NAME      # Collection name (default: obsidian_notes)
--verbose, -v          # Verbose logging
--quiet, -q            # Suppress non-error output
--json                 # JSON output format
--dry-run              # Show what would be done
--profile NAME         # Configuration profile
```

### Core Commands

#### `collection` - Collection Management
```bash
rag-agent collection create [NAME] [--force]          # Create new collection
rag-agent collection delete [NAME] [--force]          # Delete collection
rag-agent collection stats [NAME] [--detailed]        # Show statistics
rag-agent collection validate [NAME] [--fix]          # Validate integrity
rag-agent collection optimize [NAME] [--vacuum]       # Optimize performance
rag-agent collection list                             # List all collections
```

#### `index` - Indexing Operations
```bash
rag-agent index add PATH... [--recursive] [--pattern "*.md"] [--batch-size N]
rag-agent index update PATH... [--force] [--dry-run]
rag-agent index remove PATH... [--dry-run]
rag-agent index reindex [--clean] [--parallel N]
rag-agent index status                                # Show indexing status
rag-agent index validate                              # Validate indexed documents
```

#### `query` - Query Operations
```bash
rag-agent query search "natural language query" [--limit N] [--format json|table]
rag-agent query find --tag project --after 2024-01-01 [--limit N]
rag-agent query explain "query"                       # Show query plan without executing
```

#### `config` - Configuration Management
```bash
rag-agent config show [--key KEY]                     # Show configuration
rag-agent config validate                             # Validate configuration
rag-agent config set KEY VALUE [--profile NAME]
rag-agent config get KEY [--profile NAME]
rag-agent config profiles                             # List profiles
```

#### `doctor` - Diagnostics
```bash
rag-agent doctor check                                # Run all diagnostics
rag-agent doctor connectivity                         # Test connections
rag-agent doctor permissions                          # Check file permissions
rag-agent doctor models                               # Validate models
```

## 3. Implementation Architecture

### Layer Structure
```
┌─────────────────────────────────────────┐
│              CLI Layer                   │
│  (Click commands, argument parsing)      │
├─────────────────────────────────────────┤
│            Service Layer                 │
│   (Command implementations, business   │
│    logic orchestration)                 │
├─────────────────────────────────────────┤
│           Adapter Layer                  │
│  (Bridge between CLI and core modules)  │
├─────────────────────────────────────────┤
│            Core Modules                  │
│  (Existing query_planner, retriever,   │
│   ingestion, vector_manager)            │
└─────────────────────────────────────────┘
```

### Key Classes

#### `CLIContext`
```python
@dataclass
class CLIContext:
    """Shared context for all CLI commands."""
    config: LLMConfig
    vector_manager: VectorStoreManager
    logger: logging.Logger
    console: Console  # Rich console for output
    is_dry_run: bool = False
    output_format: str = "human"
```

#### `CommandRegistry`
```python
class CommandRegistry:
    """Registry for CLI commands with validation and execution."""
    
    def register(self, command: BaseCommand) -> None
    def validate(self, args: Any) -> ValidationResult
    def execute(self, args: Any) -> CommandResult
```

#### `ProgressTracker`
```python
class ProgressTracker:
    """Track progress for long-running operations."""
    
    def start_task(self, name: str, total: int) -> None
    def update(self, increment: int = 1) -> None
    def finish(self) -> None
    def add_error(self, error: str) -> None
```

## 4. Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Set up Click CLI framework
- [ ] Implement configuration management
- [ ] Create base command classes
- [ ] Add logging infrastructure with Rich
- [ ] Implement global options handling

### Phase 2: Core Commands (Week 2)
- [ ] Implement `collection` commands
- [ ] Implement `index add` with progress reporting
- [ ] Implement basic `query search`
- [ ] Add validation and error handling
- [ ] Create comprehensive tests

### Phase 3: Advanced Features (Week 3)
- [ ] Add batch processing capabilities
- [ ] Implement dry-run modes
- [ ] Add parallel processing options
- [ ] Implement configuration profiles
- [ ] Add performance optimization

### Phase 4: Polish & Documentation (Week 4)
- [ ] Add interactive features
- [ ] Create comprehensive documentation
- [ ] Add examples and tutorials
- [ ] Performance benchmarking
- [ ] User acceptance testing

## 5. Detailed Command Specifications

### `index add` Command
```bash
rag-agent index add [OPTIONS] PATH...

Options:
  --recursive, -r           Process directories recursively
  --pattern TEXT            File pattern (default: *.md)
  --batch-size INTEGER      Documents per batch (default: 100)
  --parallel INTEGER        Parallel processing threads (default: 4)
  --dry-run                 Show what would be indexed
  --force                   Re-index existing files
  --progress                Show progress bar
  --exclude TEXT            Exclude patterns (can be used multiple times)
  --include-hidden          Include hidden files
  --follow-symlinks         Follow symbolic links
```

### `query search` Command
```bash
rag-agent query search [OPTIONS] QUERY

Options:
  --limit INTEGER           Maximum results (default: 10)
  --format [json|table|yaml] Output format
  --explain                 Show query plan
  --save PATH               Save results to file
  --context [metadata|full] Response context level
```

## 6. Error Handling Strategy

### Error Categories
1. **Configuration Errors**: Invalid settings, missing dependencies
2. **Connection Errors**: Database, LLM, embedding model connectivity
3. **Validation Errors**: Invalid inputs, file permissions
4. **Processing Errors**: Document parsing, indexing failures
5. **Runtime Errors**: Unexpected system issues

### Error Recovery
- **Retry mechanisms** for transient failures
- **Graceful degradation** when optional features fail
- **Detailed error messages** with suggested fixes
- **Rollback capabilities** for failed operations

## 7. Output Formats

### Human-Readable Output
- Rich tables with colors
- Progress bars for long operations
- Clear status messages
- Error highlighting

### JSON Output
```json
{
  "command": "index.add",
  "status": "success",
  "timestamp": "2024-01-15T10:30:00Z",
  "results": {
    "files_processed": 150,
    "documents_indexed": 450,
    "errors": [],
    "duration_seconds": 12.5
  }
}
```

## 8. Configuration Management

### Configuration Files
- **Global**: `~/.config/rag-agent/config.yaml`
- **Project**: `./.rag-agent.yaml`
- **Environment**: Environment variables
- **Profiles**: Support for multiple named configurations

### Configuration Schema
```yaml
# Example configuration
default_collection: "obsidian_notes"
qdrant:
  url: "http://localhost:6333"
  api_key: null
llm:
  provider: "openrouter"
  model: "qwen3:8b"
embedding:
  model_path: "./models/Qwen3-Embedding-0.6B-f16.gguf"
  use_gpu: true
indexing:
  batch_size: 100
  parallel_workers: 4
  exclude_patterns: [".git", ".obsidian", "drafts"]
```

## 9. Testing Strategy

### Unit Tests
- Command parsing and validation
- Configuration management
- Error handling scenarios
- Output formatting

### Integration Tests
- End-to-end indexing workflows
- Query processing pipelines
- Configuration file handling
- Error recovery scenarios

### Performance Tests
- Large collection indexing
- Concurrent query handling
- Memory usage profiling
- Database connection pooling

## 10. Migration Plan

### Backward Compatibility
- Support existing command-line arguments via compatibility layer
- Provide migration guide for users
- Maintain existing environment variable support
- Gradual deprecation warnings

### Rollback Strategy
- Versioned configuration files
- Backup collections before destructive operations
- Atomic operations where possible
- Clear rollback procedures