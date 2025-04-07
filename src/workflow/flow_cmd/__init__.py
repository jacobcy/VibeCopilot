"""
Workflow Command Module Utilities

Contains helper functions and logic related to workflow CLI command processing.
(Note: Handlers have been moved to src/cli/commands/flow/handlers)
"""

# Remove the import of the deleted cmd_handlers
# from src.workflow.flow_cmd.cmd_handlers import (
#     handle_create_command,
#     handle_export_command,
#     handle_list_command,
#     handle_run_command,
#     handle_show_command,
#     handle_start_command,
# )

# Keep other potentially useful exports from this package if any
from .helpers import format_checklist, format_deliverables, format_workflow_stages  # Example
from .workflow_creator import create_workflow_from_rule, create_workflow_from_template_with_vars  # Example
from .workflow_runner import run_workflow_stage  # Example

# Update __all__ if necessary, removing handler names
__all__ = [
    # Keep existing exports if still valid
    "format_checklist",
    "format_deliverables",
    "format_workflow_stages",
    "create_workflow_from_rule",
    "create_workflow_from_template_with_vars",
    "run_workflow_stage",
    # Remove old handler names if they were listed
]
