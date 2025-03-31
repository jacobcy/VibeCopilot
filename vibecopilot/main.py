"""Main entry point for VibeCopilot."""
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from vibecopilot import __version__

app = typer.Typer(
    name="vibecopilot",
    help="AI-powered development workflow assistant",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print the version of the package."""
    if value:
        console.print(
            f"[bold]VibeCopilot[/bold] version: "
            f"[bold blue]{__version__}[/bold blue]"
        )
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application version and exit.",
        callback=version_callback,
        is_eager=True,
    )
) -> None:
    """Provide CLI for VibeCopilot application."""
    return


@app.command()
def init(
    project_name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Name of the project to initialize.",
    ),
    template: str = typer.Option(
        "standard",
        "--template",
        "-t",
        help="Template to use for initialization.",
    ),
    directory: str = typer.Option(
        ".",
        "--directory",
        "-d",
        help="Directory to initialize the project in.",
    ),
) -> None:
    """Initialize a new project with VibeCopilot."""
    console.print(
        Panel.fit(
            f"[bold green]Initializing project[/bold green]: "
            f"[bold]{project_name}[/bold]"
            f"\n[bold]Template[/bold]: {template}"
            f"\n[bold]Directory[/bold]: {directory}",
            title="VibeCopilot",
            border_style="blue",
        )
    )
    # TODO: Implement project initialization logic


@app.command()
def analyze(
    path: str = typer.Argument(".", help="Path to the project to analyze."),
    output: str = typer.Option(
        "terminal",
        "--output",
        "-o",
        help="Output format (terminal, json, markdown).",
    ),
) -> None:
    """Analyze an existing project."""
    console.print(
        Panel.fit(
            f"[bold green]Analyzing project[/bold green]: [bold]{path}[/bold]"
            f"\n[bold]Output format[/bold]: {output}",
            title="VibeCopilot",
            border_style="blue",
        )
    )
    # TODO: Implement project analysis logic


if __name__ == "__main__":
    app()
