from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()


def print_info(message: str, title: str = "INFO"):
    """Prints an informational message with a title."""
    console.print(Panel(message, title=title, border_style="blue"))


def print_success(message: str, title: str = "SUCCESS"):
    """Prints a success message."""
    console.print(Panel(message, title=title, border_style="green"))


def print_warning(message: str, title: str = "WARNING"):
    """Prints a warning message."""
    console.print(Panel(message, title=title, border_style="yellow"))


def print_error(message: str, title: str = "ERROR"):
    """Prints an error message."""
    console.print(Panel(message, title=title, border_style="red"))


def print_code(code: str, language: str, title: str = "Code Snippet"):
    """Prints a code snippet with syntax highlighting."""
    syntax = Syntax(code, language, theme="default", line_numbers=True)
    console.print(Panel(syntax, title=title, border_style="cyan"))


def print_table(data: list[dict], title: str = "Table"):
    """Prints data in a table format."""
    if not data:
        print_info("No data to display.", title=title)
        return

    table = Table(title=title, show_header=True, header_style="bold magenta")
    headers = data[0].keys()
    for header in headers:
        table.add_column(header)

    for row in data:
        table.add_row(*[str(row.get(header, "")) for header in headers])

    console.print(table)


# Example usage (can be removed later)
if __name__ == "__main__":
    print_info("This is an informational message.")
    print_success("Operation completed successfully.")
    print_warning("This is a warning.")
    print_error("An error occurred.")
    print_code("def hello():\n    print('Hello, world!')", language="python")
    sample_data = [
        {"ID": 1, "Name": "Alice", "Role": "Admin"},
        {"ID": 2, "Name": "Bob", "Role": "User"},
    ]
    print_table(sample_data, title="User List")
