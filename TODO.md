# TODO: Logging and Debug Implementation

## Phase 1: Critical Debug Features (Do Now)

### Ingestion Pipeline (src/core/ingestion/)
- [ ] **Note loading failures** - Add error logging in `Note.from_file()` when file can't be loaded
- [ ] **Empty note detection** - Log when notes produce zero sections
- [ ] **Section parsing** - Log number of sections found per note
- [ ] **Content validation** - Warn when note has no parsable content

### Query Planning (src/core/query_planner.py)
- [ ] **Query parsing failures** - Log when natural language queries can't be parsed
- [ ] **Empty results warning** - Log when queries return zero documents

## Phase 2: Useful Diagnostics (Later)
- Timing metrics
- Performance profiling
- Interactive debug modes
- Vector store statistics
- Configuration dumps
- Model capability reports

## Phase 3: Advanced Features (Much Later)
- Structured logging
- Debug visualization
- Traacing IDs
- Machine-readable formats