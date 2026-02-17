"""UserPromptSubmit hook to prevent duplicate load context commands.

Intercepts slash commands and prevents duplicate load-context
executions in the same session, saving tokens.
"""

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from entryway.hook_utils.slash_command_parser import SlashCommandParser
from entryway.models.hook_data import HookInput, HookOutput
from entryway.persistence.yaml_store import LoaderCommandStore

DATA_FILE_PATH = (
    Path.home() / ".claude" / "data" / "loader_slash_commands.yaml"
)

app = typer.Typer(
    help="Slash Command Deduplication Hook",
)
console = Console()


@app.command()
def main(
    prompt: str | None = typer.Option(
        None, "--prompt", "-p", help="Prompt text (for testing)"
    ),
    session_id: str | None = typer.Option(
        None, "--session-id", "-s", help="Session ID (for testing)"
    ),
    debug: bool = typer.Option(
        False, "--debug", "-d", help="Debug mode"
    ),
) -> None:
    """Process slash commands and prevent duplicate load context commands."""
    if prompt:
        _handle_test_mode(
            prompt=prompt,
            session_id=session_id or "test-session",
            debug=debug,
        )
    else:
        _handle_hook_mode(debug=debug)


def _handle_test_mode(
    prompt: str, session_id: str, debug: bool
) -> None:
    hook_input = HookInput(
        session_id=session_id,
        transcript_path="/tmp/test_transcript.jsonl",
        cwd="/tmp",
        hook_event_name="UserPromptSubmit",
        prompt=prompt,
    )
    if debug:
        console.print(Panel("[bold]Test Mode[/bold]", style="cyan"))
        console.print("[bold]Input:[/bold]")
        console.print(
            Syntax(
                hook_input.model_dump_json(indent=2), "json", theme="monokai"
            )
        )
    _process_command(hook_input=hook_input, debug=debug)


def _handle_hook_mode(debug: bool) -> None:
    try:
        if sys.stdin.isatty():
            console.print(
                "[bold red]Error:[/bold red] Expected JSON on stdin"
            )
            sys.exit(1)
        stdin_data = sys.stdin.read()
        if debug:
            console.print("[bold]Stdin received:[/bold]")
            console.print(Syntax(stdin_data, "json", theme="monokai"))
        data = json.loads(stdin_data)
        hook_input = HookInput(**data)
        _process_command(hook_input=hook_input, debug=debug)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)


def _process_command(hook_input: HookInput, debug: bool) -> None:
    parser = SlashCommandParser()
    store = LoaderCommandStore(file_path=DATA_FILE_PATH)
    store.load()

    if not parser.is_slash_command(prompt=hook_input.prompt):
        sys.exit(0)

    command = parser.extract_command(prompt=hook_input.prompt)
    if not command:
        sys.exit(0)

    if parser.is_purge_command(command=command):
        store.purge_session(session_id=hook_input.session_id)
        try:
            store.save()
        except OSError:
            pass
        sys.exit(0)

    if not parser.is_load_context_command(command=command):
        sys.exit(0)

    full_command = f"/{command}"

    if store.has_command(
        session_id=hook_input.session_id, command=full_command
    ):
        response = HookOutput(
            decision="block",
            reason=(
                f"Context already loaded: {full_command}\n\n"
                f"Already executed in this session.\n"
                f"To reload, use /compact or /clear first."
            ),
            systemMessage=(
                f"Context already loaded: {full_command}\n\n"
                f"Already executed in this session.\n"
                f"To reload, use /compact or /clear first."
            ),
        )
        print(
            json.dumps(response.model_dump(exclude_none=True), indent=2)
        )
        return

    store.add_command(session_id=hook_input.session_id, command=full_command)
    try:
        store.save()
    except OSError:
        pass


if __name__ == "__main__":
    app()
