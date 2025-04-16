# Refactoring Plan: Decoupling SyncService and Introducing Sync Orchestration

**Date:** 2025-04-16
**Author:** AI Assistant (System Architect Role)
**Status:** Proposed

## 1. Background & Problem Statement

Currently, the `src/memory/sync_service.py` module handles multiple responsibilities related to synchronizing local file content (rules, documents) with the vector store (Basic Memory). Its responsibilities include:

1. **Deciding What to Sync:** Based on input parameters (`changed_files`) or default settings, it determines whether to sync rules (`.mdc`), documents (`.md`), or all content.
2. **Orchestrating Processing:** It directly imports and calls specific content processors (`RuleProcessor`, `DocumentProcessor`) to parse the files.
3. **Executing Storage:** It calls the `VectorStoreAdapter` to store the processed data into the appropriate vector collection.

This design leads to several issues:

* **Violation of Single Responsibility Principle (SRP):** `SyncService` mixes high-level orchestration logic (deciding *what* to sync and *how* to process it) with lower-level execution logic (calling the storage adapter).
* **Tight Coupling:** The `memory` layer becomes coupled with higher-level concepts like "rules" and "documents" and specific file processing logic residing in `src/parsing`.
* **Reduced Extensibility:** Adding new syncable content types requires modifying `SyncService`.
* **Lower Testability:** Testing `SyncService` requires mocking processors and the vector store, making tests more complex.

## 2. Proposed Architecture

To address these issues, we propose restructuring the synchronization logic into distinct layers with clear responsibilities:

```mermaid
graph TD
    subgraph Sync Trigger (CLI, File Watcher, etc.)
        A[Trigger Event]
    end

    subgraph Orchestration Layer (e.g., src/sync)
        B(SyncOrchestrator)
    end

    subgraph Processing Layer (src/parsing)
        C{Content Processors}
        C1(RuleProcessor)
        C2(DocumentProcessor)
        C3(...)
    end

    subgraph Sync Execution Layer (src/memory)
        D(SyncExecutor)
    end

    subgraph Storage Adapter Layer (src/memory/vector)
        E(VectorStoreAdapter)
    end

    subgraph Vector Database
        F[(ChromaDB/Other)]
    end

    A --> B
    B -- Identifies Files & Type --> C
    C -- Processes Files --> B
    B -- Sends Processed Data & Target --> D
    D --> E
    E --> F

    %% Layer Responsibilities
    %% B: Decides WHAT to sync, calls Processors, calls Executor
    %% C: Knows HOW to parse specific file types
    %% D: Knows HOW to store data via the Adapter
    %% E: Interacts with the specific DB implementation
```

**Layer Responsibilities:**

1. **Sync Trigger:** Initiates the synchronization process (e.g., a CLI command, a file system watcher).
2. **Orchestration Layer (`SyncOrchestrator`):**
    * Receives the trigger and identifies which files need syncing.
    * Determines the type of each file (rule, document, etc.).
    * Instantiates and calls the appropriate `Processor` from the Processing Layer.
    * Collects the processed data (texts, metadata).
    * Calls the `SyncExecutor`'s new method (see step 4).
3. **Processing Layer (`src/parsing/...Processor`):**
    * Contains specialized processors for each content type.
    * Each processor knows how to parse its specific file type and extract relevant information (content, metadata).
    * Processors are unaware of the "sync" concept.
4. **Sync Execution Layer (`SyncExecutor` - potentially refactored `SyncService`):**
    * Receives processed data (texts, metadata) and a target collection name from the Orchestrator.
    * Its *sole responsibility* is to call the `VectorStoreAdapter` to store this data in the specified location.
    * It does not know or care about file types, file paths, or processors.
5. **Storage Adapter Layer (`VectorStoreAdapter`):**
    * Remains the abstraction layer for interacting with the specific vector database implementation.
6. **Vector Database:** The underlying storage.

## 3. Refactoring Steps (Detailed)

1. **Create `SyncOrchestrator`:**
    * Create a new file, e.g., `src/sync/sync_orchestrator.py`.
    * Define a class `SyncOrchestrator`.
    * Inject dependencies like `RuleProcessor`, `DocumentProcessor`, and the new `SyncExecutor`.
2. **Migrate Logic to `SyncOrchestrator`:**
    * Create a primary method in `SyncOrchestrator`, e.g., `orchestrate_sync(changed_files: Optional[List[str]] = None)`.
    * Move the logic from the current `SyncService.sync_all` method (identifying files, determining types based on extensions like `.mdc` or `.md`) into this new method.
    * Implement the flow:
        * Identify files to sync (based on `changed_files` or scanning default directories like `.cursor/rules`, `docs`).
        * For each file:
            * Determine its type.
            * Instantiate/call the corresponding `Processor` (e.g., `await self.rule_processor.process_rule_file(file_path)`).
            * Collect the processed `result` (text, metadata).
        * Group results by target collection (e.g., all rule texts/metadata for the "rules" collection, all document texts/metadata for the "documents" collection).
        * For each group, call the `SyncExecutor`'s new method (see step 4).
3. **Refactor `SyncService` into `SyncExecutor`:**
    * Rename `src/memory/sync_service.py` to `src/memory/sync_executor.py` (and update class name).
    * **Remove Dependencies:** Delete imports for `RuleProcessor` and `DocumentProcessor`.
    * **Remove Methods:** Delete `sync_rules`, `sync_documents`, and `sync_all`.
    * **Create `execute_storage` Method:** Add a new, generic async method:
        ```python
        async def execute_storage(self, texts: List[str], metadata_list: List[Dict[str, Any]], collection_name: str) -> List[str]:
            """
            Stores processed texts and metadata into the specified vector store collection.

            Args:
                texts: List of text content to store.
                metadata_list: List of corresponding metadata dictionaries.
                collection_name: The target collection/folder name in the vector store.

            Returns:
                List of permalinks or IDs of the stored items.
            """
            if not texts:
                return []
            # Directly call the vector store adapter's store method
            permalinks = await self.vector_store.store(texts, metadata_list, collection_name)
            # Optionally return success/failure status or counts based on permalinks
            return permalinks
        ```
    * Ensure the `__init__` method only initializes necessary components like `VectorStoreAdapter` and `config`.
4. **Update Callers:**
    * Modify any code that previously called `SyncService.sync_all` (e.g., CLI commands, tests, etc.) to now instantiate and call `SyncOrchestrator.orchestrate_sync`.
5. **Update Tests:**
    * Refactor tests for `SyncService` (now `SyncExecutor`) to focus *only* on testing the `execute_storage` method's interaction with a mocked `VectorStoreAdapter`.
    * Create new tests for `SyncOrchestrator`, mocking the processors and the `SyncExecutor` to verify the orchestration logic.

## 4. Key Changes Summary

* **New File:** `src/sync/sync_orchestrator.py` (contains `SyncOrchestrator` class)
* **Renamed/Refactored:** `src/memory/sync_service.py` -> `src/memory/sync_executor.py` (class `SyncService` -> `SyncExecutor`, methods removed/added)
* **Modified:** Callers of the old `SyncService` (CLI, tests, etc.) need to be updated to use `SyncOrchestrator`.
* **Unchanged:** `src/parsing/...Processor` classes, `src/memory/vector/memory_adapter.py`.

## 5. Expected Benefits

* **Improved Separation of Concerns:** Clear distinction between orchestration, processing, and execution.
* **Increased Cohesion:** Each module focuses on a single, well-defined task.
* **Reduced Coupling:** `memory` layer is decoupled from specific file types and parsing logic.
* **Enhanced Extensibility:** Adding new syncable types only requires a new `Processor` and updating the `SyncOrchestrator`.
* **Improved Testability:** Each layer can be tested more easily in isolation.

## 6. Potential Risks/Considerations

* **Async Handling:** Ensure `await` is used correctly when calling async methods (`process_rule_file`, `execute_storage`, etc.) within the `SyncOrchestrator`.
* **Error Handling:** Implement robust error handling in the `SyncOrchestrator` for processor failures or storage failures.
* **Configuration:** Ensure necessary configurations (default directories, etc.) are passed correctly to the `SyncOrchestrator`.
* **Test Coverage:** Ensure adequate test coverage for the new `SyncOrchestrator` and the refactored `SyncExecutor`.

## 7. Next Steps

1. Review and approve this refactoring plan.
2. Implement the changes outlined in the steps above.
3. Write/update unit and integration tests.
4. Perform thorough testing.
5. Code review.
6. Merge changes.
