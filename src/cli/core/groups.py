import click


class FormattedHelpGroup(click.Group):
    """
    A Click Group subclass that formats the commands list with headers
    based on predefined groups.
    """

    # Define the desired groups and the commands within them
    # The order in this list determines the order in the help output
    COMMAND_GROUPS = [
        ("工作流定义命令", ["create", "update", "delete", "export", "list", "validate"]),
        ("工作流会话命令", ["session", "run", "context", "next", "show"]),
    ]

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Formats the commands section of the help page with group headers."""
        commands_handled = set()

        # Format commands based on predefined groups
        for group_name, command_names in self.COMMAND_GROUPS:
            cmds_in_group = []
            for cmd_name in command_names:
                cmd = self.get_command(ctx, cmd_name)
                if cmd and not cmd.hidden:
                    cmds_in_group.append((cmd_name, cmd))
                    commands_handled.add(cmd_name)

            if cmds_in_group:
                with formatter.section(f"  {group_name}"):  # Indent group headers slightly
                    formatter.write_dl([(cmd_name, cmd.get_short_help_str(limit=formatter.width)) for cmd_name, cmd in cmds_in_group])

        # List any remaining commands that weren't in the predefined groups
        remaining_commands = []
        for cmd_name in self.list_commands(ctx):
            if cmd_name not in commands_handled:
                cmd = self.get_command(ctx, cmd_name)
                if cmd and not cmd.hidden:
                    remaining_commands.append((cmd_name, cmd))

        if remaining_commands:
            with formatter.section("  未分组命令"):  # Header for ungrouped commands
                formatter.write_dl([(cmd_name, cmd.get_short_help_str(limit=formatter.width)) for cmd_name, cmd in remaining_commands])
