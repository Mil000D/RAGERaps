# Tool-Based RAG Integration for Parallel Agent Workflow

This document describes the enhanced parallel agent workflow system with tool-based RAG (Retrieval-Augmented Generation) capabilities for querying the artists_lyrics vector store in Qdrant database.

## Overview

The tool-based RAG integration enables each agent in the parallel workflow to dynamically retrieve artist-specific lyrical content and style information during execution, generating more contextually relevant and style-specific content while preserving the performance benefits of parallel execution.

## Architecture

### Components

1. **Artist Retrieval Tool** (`app/tools/artist_retrieval_tool.py`)
   - LangChain tool for dynamic artist data retrieval during agent execution
   - Provides async methods for artist-specific lyrical content and style information
   - Returns complete lyrics content and metadata from vector store
   - Includes error handling and fallback mechanisms

2. **Enhanced Parallel Workflow** (`app/agents/parallel_workflow.py`)
   - Maintains original parallel execution architecture using LangGraph's async methods
   - Agents can dynamically call retrieval tools during their execution
   - Preserves existing business logic while enabling contextual enhancement

3. **Updated Agents**
   - **Rapper Agent**: Enhanced with artist retrieval tool for authentic style generation
   - **Judge Agent**: Enhanced with artist retrieval tool for informed style evaluation

### Execution Flow

```
1. Parallel Verse Generation
   ├── Rapper 1 Verse Node (can call artist retrieval tool)
   └── Rapper 2 Verse Node (can call artist retrieval tool)

2. Judge Round Node (can call artist retrieval tool for both rappers)
```

### Tool-Based Approach Benefits

- **Dynamic Retrieval**: Agents decide when and what to retrieve based on their needs
- **Reduced Latency**: No pre-fetching of potentially unused data
- **Flexible Context**: Agents can retrieve different types of information as needed
- **Better Error Handling**: Individual tool calls can fail without affecting the entire workflow

## Features

### RAG Service Features

- **Artist-Specific Context Retrieval**: Queries vector store for specific artist's lyrical content and style information
- **Similar Artists Context**: Retrieves style examples from similar artists when specific artist data is limited
- **Concurrent Retrieval**: Fetches context for both rappers simultaneously for optimal performance
- **Error Handling**: Graceful fallback when vector store queries fail
- **Configurable Parameters**: Adjustable number of documents to retrieve per artist

### Enhanced Agent Features

- **Style-Aware Generation**: Rapper agents use retrieved lyrical samples and style characteristics
- **Contextual Judging**: Judge agent considers authentic style elements from vector store
- **Backward Compatibility**: All existing functionality preserved when RAG is disabled
- **Async Integration**: Maintains LangGraph's asynchronous execution patterns

## Configuration

### RAG Parameters

```python
# In execute_battle_round_parallel()
rag_enabled: bool = True          # Enable/disable RAG retrieval
rag_k_per_artist: int = 3         # Documents to retrieve per artist
```

### Vector Store Configuration

The system uses the existing `artists_lyrics` collection in Qdrant with the following schema:

```python
# Document metadata structure
{
    "artist": str,              # Artist name
    "genres": List[str],        # List of genres
    "songs_count": int,         # Number of songs
    "lyric": str,              # Full lyric content
    "source": str              # Data source identifier
}
```

## Usage

### Basic Usage with RAG

```python
from app.agents.parallel_workflow import execute_battle_round_parallel

# Execute battle with RAG enabled (default)
result = await execute_battle_round_parallel(
    round_id="round_1",
    rapper1_name="Eminem",
    rapper2_name="Jay-Z",
    style1="hardcore rap",
    style2="east coast rap",
    round_number=1,
    rag_enabled=True,
    rag_k_per_artist=3
)

# Access RAG context in results
rag_context = result.get("rag_context")
if rag_context:
    rapper1_context = rag_context["rapper1_context"]
    rapper2_context = rag_context["rapper2_context"]
```

### Direct RAG Service Usage

```python
from app.services.rag_service import rag_service

# Retrieve context for a single artist
context = await rag_service.retrieve_artist_style_context(
    artist_name="Eminem",
    style="hardcore rap",
    k=5,
    include_similar_artists=True
)

# Retrieve battle context for both rappers
battle_context = await rag_service.retrieve_battle_context(
    rapper1_name="Eminem",
    rapper2_name="Jay-Z",
    style1="hardcore rap",
    style2="east coast rap",
    k_per_artist=3
)
```

## Error Handling

The RAG integration includes comprehensive error handling:

1. **Vector Store Failures**: Graceful fallback to continue battle without RAG context
2. **Missing Data**: Default context generation when specific artist data is unavailable
3. **Concurrent Execution Errors**: Individual rapper context failures don't affect the other
4. **Logging**: Detailed logging for debugging and monitoring

## Performance Considerations

- **Parallel Retrieval**: RAG context for both rappers is retrieved concurrently
- **Caching**: Vector store service includes connection pooling and caching
- **Async Operations**: All RAG operations are fully asynchronous
- **Configurable Limits**: Adjustable document retrieval limits to balance context quality and performance

## Testing

Run the integration test to verify RAG functionality:

```bash
cd backend
python test_rag_integration.py
```

The test script verifies:
- Vector store connectivity and collection existence
- RAG service functionality
- Parallel workflow integration
- Error handling and fallback mechanisms

## Dependencies

The RAG integration requires the following existing dependencies:
- `langchain-qdrant>=0.2.0`
- `qdrant-client[fastembed]>=1.8.0`
- `langchain-openai>=0.3.0`
- `langgraph>=0.1.0`

## Future Enhancements

Potential improvements for the RAG integration:

1. **Semantic Caching**: Cache frequently retrieved contexts
2. **Dynamic K Selection**: Automatically adjust retrieval count based on available data
3. **Multi-Modal Context**: Include audio features and rhythm patterns
4. **Real-Time Updates**: Sync with live artist data feeds
5. **Advanced Filtering**: More sophisticated metadata filtering options
