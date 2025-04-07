# Vector Storage

This module provides vector storage capabilities for VibeCopilot, enabling semantic search and retrieval of content.

## Overview

The vector storage system consists of:

1. **Vector Store Interface**: A common interface for all vector storage implementations
2. **Basic Memory Adapter**: Implementation using Basic Memory as the backend

## Structure

- `vector_store.py`: Abstract interface for vector storage implementations
- `memory_adapter.py`: Basic Memory adapter implementation
- `__init__.py`: Package exports

## Usage

### Basic Usage

```python
from src.db.vector.memory_adapter import BasicMemoryAdapter

# Create a Basic Memory adapter
vector_store = BasicMemoryAdapter()

# Store text with metadata
permalinks = await vector_store.store(
    texts=["This is some text to store", "This is another text to store"],
    metadata=[
        {
            "title": "First Text",
            "tags": "example,text",
            "custom_field": "value1"
        },
        {
            "title": "Second Text",
            "tags": "example,text",
            "custom_field": "value2"
        }
    ],
    folder="examples"
)

# Search for text
results = await vector_store.search("example text", limit=5)

# Get text by permalink
content = await vector_store.get(results[0]["permalink"])

# Update text
success = await vector_store.update(
    results[0]["permalink"],
    "This is updated text",
    {"title": "Updated Text", "tags": "example,updated"}
)

# Delete text
success = await vector_store.delete([results[0]["permalink"]])
```

### Custom Configuration

```python
config = {
    "default_folder": "custom_folder",
    "default_tags": "custom_tag"
}

vector_store = BasicMemoryAdapter(config)
```

## Extending

### Implementing a New Vector Store

To implement a new vector store, create a new class that inherits from `VectorStore` and implements all required methods:

```python
from src.db.vector.vector_store import VectorStore

class MyVectorStore(VectorStore):
    def __init__(self, config=None):
        # Initialize your vector store
        pass

    async def store(self, texts, metadata, folder=None):
        # Store texts with metadata
        pass

    async def search(self, query, limit=5):
        # Search for similar texts
        pass

    async def delete(self, ids):
        # Delete texts by ID
        pass

    async def update(self, id, text, metadata):
        # Update text and metadata
        pass

    async def get(self, id):
        # Get text by ID
        pass
```

## Future Extensions

Future versions may add support for additional vector storage backends:

- Chroma
- Milvus
- Qdrant
- Pinecone
