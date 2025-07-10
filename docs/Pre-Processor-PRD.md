# AI Link Pre-processor - Product Requirements Document

## Project Overview

### Vision
Create an AI-powered pre-processing system that intelligently generates and manages wikilinks across existing note collections. The system analyzes note content, titles, references, and file paths to automatically create meaningful connections between notes, transforming legacy note collections into well-structured knowledge graphs.

### Problem Statement
Many knowledge workers have accumulated thousands of notes over years with inconsistent linking and tagging practices:
- **Legacy notes lack connections**: Older notes predate current organizational systems
- **Inconsistent tagging**: Folder-based organization creates redundant or overly specific tags
- **Missing relationships**: Related concepts across notes remain disconnected
- **Manual linking is impractical**: Retroactively linking thousands of notes is humanly impossible
- **Broken link proliferation**: AI systems create infinite new links that point to nothing

### Solution Approach
An intelligent pre-processor that:
1. **Analyzes existing vault structure** to understand available link targets
2. **Uses LLMs to suggest contextually relevant links** based on multiple note signals
3. **Applies constraints** to prevent link explosion and maintain quality
4. **Manages tag hierarchy** to reduce redundancy while preserving specificity
5. **Validates all suggestions** against existing note structure

## Core Features

### 1. Intelligent Link Generation
- **Multi-signal analysis**: Process title, content, file path, existing tags, and reference URLs
- **Contextual understanding**: LLM interprets note meaning to suggest relevant connections
- **Constraint-based generation**: Maximum 10 new wikilinks per note
- **Existing link preservation**: Content-based links don't count toward generation limit
- **Quality over quantity**: Focus on meaningful connections rather than exhaustive linking

### 2. Vault Structure Analysis
- **Link inventory**: Build comprehensive dictionary of all existing wikilinks
- **Constraint enforcement**: Only suggest links that point to existing notes
- **Broken link detection**: Identify and report links that point to non-existent notes
- **Hierarchy mapping**: Understand folder structure and note relationships

### 3. Tag Management System
- **Folder-based tag extraction**: Automatically tag notes based on directory structure
- **Tag decomposition**: Break compound tags (e.g., "Exploitation - Windows" → "Exploitation" + "Windows")
- **Hierarchy normalization**: Reduce redundant specific tags in favor of broader concepts
- **Progressive refinement**: Start with broad tagging, refine as RAG system matures

### 4. Quality Assurance
- **Link validation**: Ensure all suggested links point to existing notes
- **Duplicate prevention**: Avoid suggesting links that already exist
- **Context relevance**: Verify suggestions make sense within note context
- **User review workflow**: Present suggestions for approval before implementation

## Technical Architecture

### Tech Stack
- **Language**: Python
- **LLM Framework**: LangChain (consistent with main RAG system)
- **Processing Model**: TBD (focused on text understanding and classification)
- **Data Storage**: File-based processing with JSON output for review

### Processing Pipeline
```python
# Phase 1: Vault Analysis
vault_links = extract_all_wikilinks(vault)
folder_structure = analyze_directory_hierarchy(vault)
broken_links = detect_broken_links(vault)

# Phase 2: Note Processing
for note in notes:
    context = {
        "title": note.title,
        "content": note.content,
        "file_path": note.path,
        "existing_tags": note.wikilinks,
        "references": note.urls,
        "folder_context": extract_folder_tags(note.path)
    }
    
    suggestions = llm.generate_links(
        context=context,
        available_links=vault_links,
        max_suggestions=10,
        exclude_existing=note.wikilinks
    )
    
    validated_suggestions = validate_suggestions(suggestions, vault_links)
    
# Phase 3: Review & Implementation
present_suggestions_for_review(all_suggestions)
apply_approved_suggestions(approved_suggestions)
```

### Data Structures
```python
# Link Suggestion
{
    "note_path": str,
    "suggested_links": [
        {
            "link": str,
            "confidence": float,
            "reasoning": str,
            "source_signal": str  # "title", "content", "folder", "reference"
        }
    ],
    "folder_tags": List[str],
    "decomposed_tags": List[str]
}

# Vault Analysis
{
    "total_notes": int,
    "existing_links": Set[str],
    "broken_links": List[Tuple[str, str]],
    "folder_hierarchy": Dict[str, List[str]],
    "link_frequency": Dict[str, int]
}
```

## User Experience

### Processing Workflow
1. **Initial Analysis**: System scans vault and reports structure statistics
2. **Batch Processing**: Process notes in batches with progress indication
3. **Review Interface**: Present suggestions organized by confidence and type
4. **Selective Application**: User can approve/reject suggestions at note or link level
5. **Incremental Updates**: Re-run on modified notes without full reprocessing

### Quality Control
- **Confidence scoring**: Higher confidence for multi-signal matches
- **Reasoning transparency**: Show why each link was suggested
- **Batch operations**: Accept/reject similar suggestions across multiple notes
- **Rollback capability**: Undo changes if results are unsatisfactory

## Success Metrics

### Functional Requirements
- [ ] Extract and inventory all existing wikilinks in vault
- [ ] Generate contextually relevant link suggestions with <10 per note
- [ ] Decompose folder-based tags into component concepts
- [ ] Validate all suggestions against existing note structure
- [ ] Provide clear reasoning for each suggested link
- [ ] Enable selective application of suggestions

### Quality Metrics
- **Precision**: >80% of suggested links deemed relevant by user
- **Coverage**: Suggest links for >90% of notes that could benefit
- **Constraint adherence**: Never suggest links to non-existent notes
- **Processing efficiency**: Handle 3000+ notes without performance degradation

### User Experience Goals
- **Transparency**: Users understand why each link was suggested
- **Control**: Users can easily accept/reject suggestions
- **Incremental improvement**: Vault connectivity improves without overwhelming changes
- **Maintainability**: System can be re-run as vault evolves

## Implementation Phases

### Phase 1: Foundation (MVP)
- Vault structure analysis and link inventory
- Basic LLM-powered link suggestion
- Simple validation against existing links
- Manual review and application workflow

### Phase 2: Intelligence Enhancement
- Multi-signal analysis (title + content + folder + references)
- Confidence scoring and reasoning
- Tag decomposition and hierarchy management
- Batch processing and progress tracking

### Phase 3: Advanced Features
- Incremental processing for modified notes
- Integration with main RAG system for feedback
- Advanced quality metrics and reporting
- Automated suggestion refinement based on user patterns

## Risk Assessment

### Technical Risks
- **LLM accuracy**: Suggestions may be irrelevant or low-quality
- **Performance**: Processing 3000+ notes may be slow or expensive
- **Complexity**: Multi-signal analysis adds significant complexity
- **Integration**: Coordination with main RAG system pipeline

### Product Risks
- **User overwhelm**: Too many suggestions may be counterproductive
- **Quality degradation**: Automated linking may reduce overall vault quality
- **Maintenance burden**: System requires ongoing tuning and refinement

### Mitigation Strategies
- **Conservative constraints**: Start with strict limits on suggestions
- **Extensive validation**: Multiple quality checkpoints before application
- **Iterative approach**: Small batches with user feedback
- **Rollback capability**: Easy to undo changes if results are poor

## Success Criteria

This project succeeds when:
1. **Legacy notes gain meaningful connections** without manual intervention
2. **Vault navigation improves** through better link density
3. **Tag consistency increases** while maintaining useful specificity
4. **User effort decreases** for maintaining note relationships
5. **Integration readiness** with main RAG system is achieved

The pre-processor transforms a collection of individual notes into a connected knowledge graph, setting the foundation for the advanced retrieval capabilities of the main RAG system.

## Relationship to Main RAG System

### Dependencies
- **Shared infrastructure**: Common note parsing and wikilink extraction
- **Consistent data formats**: Compatible note object structures
- **Coordinated processing**: Pre-processor runs before RAG embedding generation

### Integration Points
- **Enhanced metadata**: Pre-processor output enriches RAG system metadata
- **Improved search**: Better-connected notes provide more context for retrieval
- **Feedback loop**: RAG system usage patterns can inform pre-processor improvements

### Sequencing
1. **Pre-processor**: Enhances existing note collection with links and tags
2. **RAG System**: Embeds enhanced notes with rich metadata and connections
3. **Iterative refinement**: Both systems improve based on user interaction patterns
