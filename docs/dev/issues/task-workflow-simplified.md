# Refactoring Plan: Task-Centric Workflow with Status Providers

**Goal:** Transition VibeCopilot's core workflow management to a task-centric model where the application state (current task, current session) is managed by dedicated Status Providers instead of boolean flags (`is_current`) in the database models.

**Core Philosophy:**

* **Task:** Represents the central goal or unit of work. It's the *why*.
* **Flow Session:** Represents a specific action or process undertaken to achieve a Task's goal. It's the *how* (following a defined Workflow pattern). Multiple sessions can be linked to a single task over its lifecycle.
* **Workflow:** Defines reusable patterns or sequences of actions (Flow Sessions) applicable to Tasks.
* **Memory:** Provides contextual information, history, and knowledge relevant to Tasks and Sessions.
* **Rules:** Define constraints, standards, and best practices governing actions within Sessions and Tasks.

**Problem:** The current implementation uses `is_current` boolean flags in `Task` and `FlowSession` models, managed directly by repository methods. This leads to:
    *Scattered state logic.
    *   Potential race conditions or inconsistencies if not managed carefully.
    *Difficulty in observing state changes centrally.
    *   Tight coupling between state management and database persistence.

**Proposed Solution:**

1. **Centralize State Management:** Introduce/Modify Status Providers for Task and Flow Session.
    * `src/status/providers/task_provider.py`: `TaskStatusProvider` will be responsible for holding and publishing the `current_task_id`.
    * `src/status/providers/flow_session_provider.py` (Create if needed): `FlowSessionProvider` will be responsible for holding and publishing the `current_session_id`.
2. **Remove Database Flags:** Eliminate the `is_current` column from both `Task` and `FlowSession` database models.
3. **Update Core Logic:** Modify task creation and session switching logic to interact with the Status Providers.
4. **Refactor Repositories:** Remove methods directly manipulating the `is_current` state from `TaskRepository` and `FlowSessionRepository`.

## Implementation Details

### 1. Data Model Changes

* **`src/models/db/task.py`:**
  * Remove `is_current = Column(Boolean, default=False)`.
  * Remove `is_current` from `to_dict()`.
* **`src/models/db/flow_session.py`:**
  * Remove `is_current = Column(Boolean, default=False)`.
  * Remove `is_current` from `to_dict()` and `from_dict()`.

```python
# Example src/models/db/task.py (After Change)
class Task(Base):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True)
    # ... other columns ...
    current_session_id = Column(String, nullable=True) # Keep this to link task to its active session
    # is_current column removed

    def to_dict(self):
        return {
            # ... other fields ...
            "current_session_id": self.current_session_id,
            # is_current field removed
        }

# Example src/models/db/flow_session.py (After Change)
class FlowSession(Base):
    __tablename__ = 'flow_sessions'
    id = Column(String, primary_key=True)
    # ... other columns ...
    task_id = Column(String, ForeignKey('tasks.id'))
    # is_current column removed

    def to_dict(self) -> Dict[str, Any]:
         return {
            # ... other fields ...
            "task_id": self.task_id,
            # is_current field removed
         }
```

### 2. Status Provider Implementation

* **`src/status/providers/task_provider.py` (`TaskStatusProvider`):**
  * Add state variable: `_current_task_id: Optional[str] = None`.
  * Add persistence logic (e.g., using a state file like `~/.vibecopilot/status/current_task.json` or similar, loaded on init).
  * Implement `set_current_task(self, task_id: Optional[str])`: Updates `_current_task_id` and persists the change. Should potentially notify subscribers.
  * Implement `get_current_task_id(self) -> Optional[str]`: Returns `_current_task_id`.
  * Update `get_status()`: Use `get_current_task_id()` to fetch details for the `current_task` part of the status summary. Remove calls to `task_repo.get_current_task()`.
* **`src/status/providers/flow_session_provider.py` (`FlowSessionProvider`):**
  * Create this provider if it doesn't exist.
  * Similar implementation to `TaskStatusProvider` for `_current_session_id`.
  * Implement `set_current_session(self, session_id: Optional[str])` and `get_current_session_id(self) -> Optional[str]`.
  * Implement persistence logic (e.g., `~/.vibecopilot/status/current_session.json`).

### 3. Repository Changes

* **`src/db/repositories/task_repository.py`:**
  * Remove methods: `get_current_task()`, `set_current_task()`.
  * Remove any logic updating the (now removed) `is_current` column.
* **`src/db/repositories/flow_session_repository.py`:**
  * Remove methods directly setting/unsetting `is_current` (like a dedicated `set_current_session` that modified the DB flag).
  * Remove any logic updating the (now removed) `is_current` column.

### 4. Core Logic Updates

* **Task Creation (`src/services/task/core.py` - `create_task`):**
  * After successfully creating `task_orm`:
    * Get the `TaskStatusProvider` instance.
    * Call `task_provider.set_current_task(task_orm.id)`.

* **Session Switching (`src/flow_session/manager/current_session.py` - `switch_session` or similar):**
  * Get the target `session` object.
  * Remove logic directly setting `session.is_current` or updating the DB flag via the repository.
  * Get the `FlowSessionProvider` instance.
  * Call `flow_session_provider.set_current_session(session.id)`.
  * **Task Linkage:**
    * If `session.task_id` exists:
      * Get the `TaskStatusProvider` instance.
      * Call `task_provider.set_current_task(session.task_id)`.

* **Task Service (`src/services/task/core.py`):**
  * Remove or refactor the existing `get_current_task` and `set_current_task` methods to use the `TaskStatusProvider`. Be mindful of the dependency chain (e.g., `TaskSessionService` might need updates too if it was involved).

### 5. Persistence Considerations

* Decide on a consistent strategy for persisting `current_task_id` and `current_session_id` (e.g., JSON files in a dedicated status directory, central config file). This ensures state is maintained across application restarts. The providers should handle loading this state during initialization.

## Action Plan (Sequence)

1. **Modify Models:** Remove `is_current` from `Task` and `FlowSession`.
2. **Modify Repositories:** Remove methods and logic related to `is_current`.
3. **Implement/Update Status Providers:** Add state variables, persistence, `set_current_*` and `get_current_*` methods to `TaskStatusProvider` and `FlowSessionProvider`.
4. **Update Session Switching Logic:** Modify `current_session.py` (or equivalent) to use `FlowSessionProvider` and trigger `TaskProvider` updates.
5. **Update Task Creation Logic:** Modify `task/core.py` to call `TaskProvider.set_current_task`.
6. **Refactor Services:** Update `TaskService` and potentially related services (`TaskSessionService`) to use providers instead of repository methods for current state.
7. **Testing:** Thoroughly test task creation, session switching, and status reporting commands.

This plan establishes a cleaner, task-centric architecture with centralized state management via the provider pattern.
