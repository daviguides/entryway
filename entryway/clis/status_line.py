"""Status line for Claude Code.

Generates a custom status line showing model, machine, directory,
git branch, cost, context window usage, and session ID.

Configuration in ~/.claude/settings.json:
    {
      "statusLine": {
        "type": "command",
        "command": "status_line",
        "padding": 0
      }
    }
"""

import json
import os
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.text import Text

# Display toggles
SHOW_COST = True
SHOW_VERSION = False
SHOW_MACHINE = True
SHOW_CONTEXT_WINDOW = True
SHOW_SESSION_ID = True

# Context window
PROGRESS_BAR_WIDTH = 15

# Separators
SEP = "|"

# Git
GIT_DIR = ".git"
GIT_REF_PREFIX = "ref: refs/heads/"

app = typer.Typer(add_completion=False)
console = Console(highlight=False, force_terminal=True, record=True)


def get_sample_data() -> dict:
    """Generate sample data for echo/test mode."""
    return {
        "model": {"display_name": "Opus 4.5"},
        "workspace": {"current_dir": str(Path.cwd())},
        "cost": {"total_cost_usd": 0.1234},
        "version": "1.0.0",
        "context_window": {
            "used_percentage": 42.5,
            "context_window_size": 200000,
        },
        "session_id": "abc12345",
    }


def get_usage_color(percentage: float) -> str:
    """Get Rich color based on context window usage."""
    if percentage < 50:
        return "green"
    if percentage < 75:
        return "yellow"
    if percentage < 90:
        return "red"
    return "bold red"


def create_progress_bar(percentage: float) -> str:
    """Create visual progress bar with Rich markup."""
    filled = int((percentage / 100) * PROGRESS_BAR_WIDTH)
    empty = PROGRESS_BAR_WIDTH - filled
    color = get_usage_color(percentage)
    return f"\\[[{color}]{'#' * filled}[/][dim]{'-' * empty}[/]]"


def format_tokens(tokens: int) -> str:
    """Format token count (e.g., 150.2k, 1.50M)."""
    if tokens < 1000:
        return str(tokens)
    if tokens < 1_000_000:
        return f"{tokens / 1000:.1f}k"
    return f"{tokens / 1_000_000:.2f}M"


def generate_status_line(data: dict) -> str:
    """Generate status line from session data."""
    model = data.get("model", {}).get("display_name", "Claude")
    workspace = data.get("workspace", {})
    dir_name = Path(workspace.get("current_dir", "~")).name or "~"
    git_branch = extract_git_branch()
    machine = os.environ.get("MACHINE") if SHOW_MACHINE else None
    cost = round(data.get("cost", {}).get("total_cost_usd", 0), 2)
    version = data.get("version", "") if SHOW_VERSION else None

    parts = [f"[bold cyan]\\[{model}][/]"]

    if machine:
        parts.append(f"{SEP} [cyan]{machine}[/]")

    parts.append(f"{SEP} [blue]{dir_name}[/]")

    if git_branch:
        parts.append(f"{SEP} [green]{git_branch}[/]")

    if SHOW_COST and cost and cost > 0:
        parts.append(f"{SEP} [yellow]${cost:.2f}[/]")

    if version:
        parts.append(f"{SEP} [cyan]{version}[/]")

    if SHOW_CONTEXT_WINDOW:
        ctx = data.get("context_window", {})
        used_pct = ctx.get("used_percentage", 0) or 0
        ctx_size = ctx.get("context_window_size", 200000) or 200000
        remaining = int(ctx_size * ((100 - used_pct) / 100))
        color = get_usage_color(used_pct)
        bar = create_progress_bar(used_pct)
        parts.append(f"{bar} [{color}]{used_pct:.1f}%[/]")
        parts.append(f"[blue]~{format_tokens(remaining)} left[/]")

    if SHOW_SESSION_ID:
        session_id = data.get("session_id", "")
        if session_id:
            parts.append(f"[dim]{session_id}[/]")

    return " ".join(parts)


def find_git_dir() -> Path | None:
    """Find .git directory by walking up the tree."""
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        git_path = parent / GIT_DIR
        if git_path.exists():
            return git_path
    return None


def extract_git_branch() -> str | None:
    """Extract current git branch. Handles regular repos and worktrees."""
    git_path = find_git_dir()

    if not git_path:
        return None

    try:
        if git_path.is_file():
            content = git_path.read_text(encoding="utf-8").strip()
            if content.startswith("gitdir:"):
                gitdir = content.replace("gitdir:", "").strip()
                git_head = Path(gitdir) / "HEAD"
            else:
                return None
        else:
            git_head = git_path / "HEAD"

        if not git_head.exists():
            return None

        head = git_head.read_text(encoding="utf-8").strip()
        if not head.startswith(GIT_REF_PREFIX):
            return None

        return head.replace(GIT_REF_PREFIX, "")

    except (OSError, UnicodeDecodeError):
        return None


def render_to_ansi(markup: str) -> str:
    """Convert Rich markup to ANSI escape codes."""
    text = Text.from_markup(markup)
    with console.capture() as capture:
        console.print(
            text, end="", soft_wrap=True, overflow="ignore", no_wrap=True
        )
    return capture.get()


@app.command()
def main(
    echo: bool = typer.Option(
        False, "--echo", "-e", help="Test mode with sample data"
    ),
) -> None:
    """Generate status line for Claude Code."""
    try:
        data = get_sample_data() if echo else json.load(sys.stdin)
        status = generate_status_line(data)
        ansi_output = render_to_ansi(status)
        sys.stdout.write(ansi_output + "\n")
        sys.stdout.flush()
        sys.exit(0)
    except Exception:
        print("Claude Code")
        sys.exit(0)


if __name__ == "__main__":
    app()
