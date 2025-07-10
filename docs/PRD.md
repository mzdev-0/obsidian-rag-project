# Second Brain RAG System - Product Requirements Document

## Project Overview

### Vision
Build a "second-brain" application that actually delivers what users expect from personal knowledge management: intelligent note retrieval with proper context, metadata, and organizational structure. Unlike existing solutions that treat personal notes as semantic blobs, this system preserves the relationships, temporal context, and structural information that makes personal knowledge management effective.

### Problem Statement
Current "AI-powered" note apps fail at basic user expectations:
- **No contextual retrieval**: Users get content snippets without knowing where they came from
- **Poor temporal filtering**: Can't answer queries like "show me notes about X from last week"
- **Broken search results**: Semantic search returns irrelevant content that matches date criteria but not topic
- **Loss of structure**: Notes become disconnected chunks without relationship context
- **Contaminated embeddings**: Images, PDFs, and text get mixed together, degrading search quality

### Solution Approach
A hybrid retrieval system that combines:
1. **Structured metadata** for precise filtering (dates, tags, file paths, etc.)
2. **Semantic search** for content relevance
3. **Two-stage retrieval** that intersects both criteria to prevent false positives
4. **Clean embedding strategy** that preserves content type separation

## Core Features

### 1. Intelligent Note Parsing
- **Metadata extraction** from note templates and file system
- **Wikilink parsing** for relationship mapping (e.g., `[[Machine Learning]]`)
- **Heading-based chunking** for structured content retrieval
- **Image detection** with filtering of attachment links vs. concept links

### 2. Multi-Modal Embedding Strategy
- **Text sections**: One embedding per heading section with clean semantic content
- **Images**: Separate visual embeddings using lightweight vision models
- **No PDF embedding**: Avoid massive documents that contaminate search results
- **Metadata preservation**: Store file paths, dates, tags, and relationships alongside embeddings

### 3. Hybrid Search Architecture
```
Query: "Show me notes about transformers from last week"
├── Metadata Filter → Get note IDs matching date range
├── Semantic Search → Find content matching "transformers"
└── Intersection → Return only results that satisfy BOTH criteria
```

### 4. Structured Retrieval Results
Each search result includes:
- **Content snippet** with semantic relevance
- **Full metadata**: Title, date, file path, tags, section heading
- **Relationship context**: Wikilinks and note connections
- **Direct navigation**: Links to view/edit the source note

### 5. Advanced Query Capabilities
- **Temporal queries**: "Notes from last week", "Recent thoughts about X"
- **Relationship queries**: "Notes linking to [[RAG]]", "Everything connected to vector databases"
- **Multi-modal queries**: "Show me that note with the CICD pipeline diagram"
- **Compound queries**: "RAG notes from this month that mention vector databases but aren't tagged as draft"

## Technical Architecture

### Tech Stack
- **Language**: Python
- **Vector Database**: ChromaDB
- **LLM Framework**: LangChain
- **Embedding Model**: Qwen3-Embedding-0.6B (1024-dimensional vectors, multilingual capabilities)
- **Vision Model**: Lightweight classifier (TBD - CPU-optimized)

### Data Structure
```python
# Note Object
{
    "metadata": {
        "title": str,
        "created_date": datetime,
        "modified_date": datetime,
        "file_path": str,
        "tags": List[str],
        "wikilinks": List[str],
        "note_type": str
    },
    "content_sections": [
        {
            "id": str,
            "heading": str,
            "content": str,
            "embedding": vector,
            "level": int  # h1, h2, h3, etc.
        }
    ],
    "images": [
        {
            "path": str,
            "embedding": vector,
            "ocr_text": str,
            "context": str
        }
    ]
}
```

### Embedding Strategy
- **Clean content embedding**: `f"{note.title} | {section.heading}\n\n{section.content}"`
- **Metadata stored separately**: Associated with embeddings but not embedded
- **No ID contamination**: IDs used for linking, not embedded in content
- **Image separation**: Pure visual embeddings with contextual metadata

## User Experience

### Target User Queries
1. **Temporal**: "What did I write about machine learning last month?"
2. **Topical**: "Find my notes on attention mechanisms"
3. **Relational**: "Show me everything linked to [[Transformers]]"
4. **Visual**: "That note with the system architecture diagram"
5. **Compound**: "Recent RAG notes that mention ChromaDB"
6. **Specific References**: "Show me all notes that include references to CVE-2025-1235 I wrote this month"
7. **Multi-criteria**: "Give me a list of recon TTPs and the note they were found in that will be helpful in an engagement where the target is primarily windows and active-directory/azure"
8. **Visual Context**: "Show me that note with the diagram of red team TTPs"

### Expected Behavior
- **Precision over recall**: Return nothing rather than irrelevant matches
- **Full context**: Always provide source location and metadata
- **Structured responses**: Clear organization with proper citations
- **Fail gracefully**: Inform users when no matches exist rather than returning random results

## Success Metrics

### Functional Requirements
- [ ] Extract metadata from existing note collections
- [ ] Generate clean embeddings for text sections (including note titles)
- [ ] Implement two-stage retrieval (metadata + semantic)
- [ ] Process wikilinks and relationship mapping
- [ ] Handle image embeddings separately from text
- [ ] Support compound queries with multiple criteria

### Project Completion Tests
- [ ] "Show me all the notes that include references to CVE-2025-1235 I wrote this month" - Tests specific reference search with temporal filtering
- [ ] "Give me a list of recon TTPs and the note they were found in that will be helpful in an engagement where the target is primarily windows and active-directory/azure" - Tests domain-specific semantic search with source attribution
- [ ] "Show me that note with the diagram of red team TTPs" - Tests visual content retrieval with contextual matching

### User Experience Goals
- **Query success rate**: Users find what they're looking for >90% of the time
- **Context completeness**: Every result includes source location and metadata
- **Response relevance**: No irrelevant results due to date/metadata contamination
- **Navigation efficiency**: Users can quickly access and edit source notes

## Future Considerations

### Potential Product Extensions
- **AI tag generation**: Automatically suggest relevant wikilinks based on content
- **Relationship visualization**: Graph view of note connections
- **Multi-user support**: Team knowledge bases with proper permissions
- **Integration ecosystem**: API for connecting to other tools

### Technical Scalability
- **Performance optimization**: Efficient metadata indexing for large note collections
- **Incremental updates**: Handle note modifications without full re-indexing
- **Storage efficiency**: Optimize embedding storage and retrieval
- **Multi-format support**: Extend beyond Obsidian to other note formats

## Risk Assessment

### Technical Risks
- **Embedding quality**: Ensure vision models provide meaningful image search
- **Performance**: Metadata + semantic search intersection at scale
- **Data complexity**: Handling diverse note structures and formats

### Product Risks
- **User adoption**: Requires users to understand structured note-taking
- **Migration complexity**: Existing note collections may need cleanup
- **Feature scope**: Balancing power with simplicity

## Success Criteria

This project succeeds when users can:
1. Ask natural language questions about their notes and get precise, contextual results
2. Navigate from search results directly to source notes for editing
3. Discover connections between ideas through relationship mapping
4. Trust that "no results" means they genuinely haven't written about that topic
5. Maintain their existing note-taking workflows while gaining AI-powered search capabilities
