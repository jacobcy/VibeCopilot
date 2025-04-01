"""Command line interface for VibeCopilot."""

from .commands import process_command
from .cursor_commands import handle_cursor_command

__all__ = ["handle_cursor_command", "process_command"]
