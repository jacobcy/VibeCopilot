# Memory Management System

This module provides memory management capabilities for VibeCopilot, enabling content synchronization, entity management, knowledge storage and retrieval with integrated SQLite and vector database support.

## Overview

The memory system consists of:

1. **Memory Manager**: Core component managing SQLite and vector database integration
2. **Sync Service**: Synchronizes local content with Basic Memory
3. **Entity Manager**: Manages knowledge entities and their properties
4. **Observation Manager**: Records and retrieves observations (facts, events, states)
5. **Relation Manager**: Handles relationships between entities

## Structure

- `memory_manager.py`: Core memory management with SQLite and vector database integration
- `sync_service.py`: Synchronization service for local content and Basic Memory
- `entity_manager.py`: Entity management for knowledge entities
- `observation_manager.py`: Observation management for recording facts and events
- `relation_manager.py`: Relation management for entity relationships

## Database Integration

The system integrates both SQLite and vector database (ChromaDB) to provide:

- Fast SQL queries for structured data and metadata
- Semantic vector search for natural language queries
- Automatic synchronization between SQL and vector storage
- Data migration capabilities for smooth upgrades

## Usage

### Memory Manager

The Memory Manager is the primary interface for memory storage and retrieval with database integration.

```python
from src.memory.memory_manager import MemoryManager

# Create memory manager
memory_manager = MemoryManager()

# Store new memory
result = await memory_manager.store_memory(
    content="Vector databases are specialized database systems designed for storing and retrieving vector embeddings efficiently.",
    title="Introduction to Vector Databases",
    tags="vector,database,embeddings",
    folder="knowledge"
)

# Retrieve memory by permalink
memory = await memory_manager.get_memory_by_id(result["permalink"])

# Search memories
results = await memory_manager.retrieve_memory("What are vector databases?")

# List memories in a folder
memories = await memory_manager.list_memories(folder="knowledge")

# Delete memory
result = await memory_manager.delete_memory(permalink)
```

### Sync Service

The Sync Service is used to synchronize local content (rules, documents) with Basic Memory.

```python
from src.memory.sync_service import SyncService

# Create sync service
sync_service = SyncService()

# Sync all rules
result = await sync_service.sync_rules()

# Sync specific document files
files = ["docs/user/guide.md", "docs/dev/architecture.md"]
result = await sync_service.sync_documents(files)

# Sync all content
result = await sync_service.sync_all()
```

### Entity Manager

The Entity Manager is used to create, update, and manage knowledge entities.

```python
from src.memory.entity_manager import EntityManager

# Create entity manager
entity_manager = EntityManager()

# Create a new entity
entity = await entity_manager.create_entity(
    entity_type="technology",
    properties={
        "name": "Python",
        "version": "3.9",
        "category": "programming_language"
    }
)

# Get an entity by ID
python_entity = await entity_manager.get_entity(entity["id"])

# Update an entity
updated_entity = await entity_manager.update_entity(
    entity["id"],
    properties={"version": "3.10"}
)

# Search for entities
results = await entity_manager.search_entities("Python programming")
```

### Observation Manager

The Observation Manager is used to record and retrieve observations.

```python
from src.memory.observation_manager import ObservationManager

# Create observation manager
observation_manager = ObservationManager()

# Record an observation
observation = await observation_manager.record_observation(
    content="VibeCopilot repository was updated with new features.",
    metadata={
        "type": "development",
        "title": "Repository Update",
        "tags": ["github", "development"]
    },
    related_entities=["entity_vibecopilot", "entity_github"]
)

# Get an observation
result = await observation_manager.get_observation(observation["id"])

# Search for observations
results = await observation_manager.search_observations(
    query="repository update",
    observation_type="development"
)

# Get recent observations
recent = await observation_manager.get_recent_observations(limit=5)
```

### Relation Manager

The Relation Manager is used to create and query relationships between entities.

```python
from src.memory.relation_manager import RelationManager

# Create relation manager
relation_manager = RelationManager()

# Create a relationship
relation = await relation_manager.create_relation(
    source_id="entity_vibecopilot",
    target_id="entity_python",
    relation_type="uses",
    properties={"since": "2023-01-01"}
)

# Get relationships for an entity
relations = await relation_manager.get_relations(
    entity_id="entity_vibecopilot",
    relation_type="uses"
)

# Find a path between entities
path = await relation_manager.find_path(
    source_id="entity_vibecopilot",
    target_id="entity_claude",
    max_depth=3
)

# Find common connections
common = await relation_manager.find_common_connections(
    entity_id1="entity_vibecopilot",
    entity_id2="entity_cursor"
)
```

## Database Migration

To update the database schema for vector database integration:

```bash
python scripts/update_memory_schema.py
```

This script adds vector database related fields to the MemoryItem model:

- `permalink`: Link to vector database entry
- `folder`: Vector database storage directory
- `entity_count`: Number of parsed entities
- `relation_count`: Number of parsed relationships
- `observation_count`: Number of parsed observations
- `vector_updated_at`: Vector database update timestamp

## Example

A complete integration example is available at:

```bash
python examples/memory_integration_example.py
```

## Configuration

All components accept optional configuration parameters that can be used to customize behavior.

```python
config = {
    "default_folder": "custom_folder",
    "default_tags": "custom_tag",
    "vector_store_config": {
        "instance_id": "memory_manager"
    }
}

memory_manager = MemoryManager(config)
```

Default configurations are loaded from the application config.
