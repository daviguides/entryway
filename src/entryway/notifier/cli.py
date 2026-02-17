"""CLI for Claude Code hook notifications."""

import json
import sys

import typer
from rich.console import Console

from .hooks import get_notification_config
from .models import HookEvent
from .notifier import send_notification

app = typer.Typer(help="Claude Code Hook Notifier")
console = Console()


@app.command()
def main(
    event: str | None = typer.Option(
        None, "--event", "-e", help="Event type (for testing)"
    ),
    project: str | None = typer.Option(
        None, "--project", "-p", help="Project name (for testing)"
    ),
    debug: bool = typer.Option(
        False, "--debug", "-d", help="Debug mode"
    ),
) -> None:
    """Process Claude Code hook events and send notifications."""
    if event:
        _handle_test_mode(event, project, debug)
    else:
        _handle_hook_mode(debug)


def _handle_test_mode(
    event: str, project: str | None, debug: bool
) -> None:
    hook_event = HookEvent(hook_event_name=event, cwd=project)
    if debug:
        console.print("[bold]Test Mode[/bold]")
        console.print(f"Event: {hook_event.model_dump_json(indent=2)}")
    config = get_notification_config(hook_event)
    exit_code = send_notification(config, debug=debug)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


def _handle_hook_mode(debug: bool) -> None:
    if sys.stdin.isatty():
        console.print(
            "[bold red]Error:[/bold red] Expected JSON on stdin"
        )
        raise typer.Exit(code=1)
    try:
        stdin_data = sys.stdin.read()
        data = json.loads(stdin_data)
        hook_event = HookEvent(**data)
        config = get_notification_config(hook_event)
        exit_code = send_notification(config, debug=debug)
        if exit_code != 0:
            raise typer.Exit(code=exit_code)
    except json.JSONDecodeError as e:
        console.print(f"[bold red]JSON Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
