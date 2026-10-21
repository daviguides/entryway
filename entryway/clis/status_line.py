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
import re
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.text import Text

# Display toggles
SHOW_COST = False
SHOW_VERSION = False
SHOW_MACHINE = True
SHOW_CONTEXT_WINDOW = True
SHOW_SESSION_ID = True

# Context window
PROGRESS_BAR_WIDTH = 8

# Separators
SEP = ""

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


def smart_path(cwd: str) -> str:
    """Context-aware path display, ported from _prompt_smart_path (davi-ups prompt-theme.zsh).

    Priority: worktree > projects > sources > home > full path.
    Reads SOURCES_PATH/PROJECTS_PATH env vars, defaulting to ~/work/sources and
    ~/work/projects.
    """
    sources = os.environ.get("SOURCES_PATH", str(Path.home() / "work" / "sources"))
    projects = os.environ.get("PROJECTS_PATH", str(Path.home() / "work" / "projects"))
    home = str(Path.home())

    worktree_marker = "/.worktrees/"
    if worktree_marker in cwd:
        before_wt, _, wt_remainder = cwd.partition(worktree_marker)

        if cwd.startswith(f"{projects}/"):
            # Externalized: <projects>/<owner>/<repo>/<name>/.worktrees/...
            project = before_wt.rsplit("/", 1)[-1]
        else:
            # Source-local: <sources>/<project>/.../.worktrees/...
            marker = f"{sources}/"
            project = before_wt.split(marker, 1)[-1] if marker in before_wt else before_wt

        subpath = wt_remainder.partition("/")[2]
        return f"⎇ {project}/{subpath}" if subpath else f"⎇ {project}"

    if cwd.startswith(projects):
        rel = cwd[len(projects):].lstrip("/")
        return f"⟢ {rel}" if rel else "⟢ "

    if cwd.startswith(sources):
        rel = cwd[len(sources):]
        return f"»{rel}" if rel else "» "

    if cwd.startswith(home):
        return f"~{cwd[len(home):]}"

    return cwd


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
    return f"\\[[{color}]{'#' * filled}[/][dim]{'•' * empty}[/]]"


def format_tokens(tokens: int) -> str:
    """Format token count (e.g., 150.2k, 1.50M)."""
    if tokens < 1000:
        return str(tokens)
    if tokens < 1_000_000:
        return f"{tokens / 1000:.1f}k"
    return f"{tokens / 1_000_000:.2f}M"


def generate_status_line(data: dict) -> tuple[str, str]:
    """Generate two-line status bar from session data.

    Line 1: session, dir, branch, context window.
    Line 2: session ID, machine/model.
    """
    model = data.get("model", {}).get("display_name", "Claude")
    workspace = data.get("workspace", {})
    dir_name = smart_path(workspace.get("current_dir", "~"))
    git_branch = extract_git_branch()
    machine = os.environ.get("MACHINE") if SHOW_MACHINE else None
    cost = round(data.get("cost", {}).get("total_cost_usd", 0), 2)
    version = data.get("version", "") if SHOW_VERSION else None
    ppid = os.getppid()
    session_meta = get_session_meta(ppid)
    session_name = session_meta.get("name")

    line1_parts = []
    line2_parts = []

    if session_name:
        line1_parts.append(f"[grey][[/][cyan]{session_name}[/][grey]][/]")

    line1_parts.append(f"{SEP}[blue]{dir_name}[/]")

    if git_branch:
        dirty = "[yellow]*[/]" if is_git_dirty() else ""
        line1_parts.append(f"{SEP}[grey]([/][red]{git_branch}[/]{dirty}[grey])[/]")

    if SHOW_COST and cost and cost > 0:
        line1_parts.append(f"{SEP}[yellow]${cost:.2f}[/]")

    if version:
        line1_parts.append(f"{SEP}[cyan]{version}[/]")

    if SHOW_CONTEXT_WINDOW:
        ctx = data.get("context_window", {})
        used_pct = ctx.get("used_percentage", 0) or 0
        ctx_size = ctx.get("context_window_size", 20000) or 20000
        remaining = int(ctx_size * ((100 - used_pct) / 100))
        color = get_usage_color(used_pct)
        bar = create_progress_bar(used_pct)
        line1_parts.append(f"{bar}")
        line1_parts.append(f"[{color}]{used_pct:.1f}%[/]")
        line1_parts.append(f"[blue]({format_tokens(remaining)}/{format_tokens(ctx_size)})[/]")

    if machine:
        line1_parts.append(f"{SEP}[grey][[/][cyan]{machine}[/][grey]][grey]([/][blue]{model}[/][grey])[/]")

    elapsed = get_session_elapsed()
    status = session_meta.get("status", "unknown")
    if status == "busy":
        state_label = "[green]active[/]"
    elif status == "idle":
        state_label = "[dim]idle[/]"
    else:
        state_label = f"[dim]{status}[/]"

    if elapsed:
        line2_parts.append(f"running: [green]{elapsed}[/] {state_label} [dim]pid:{ppid}[/]")

    if SHOW_SESSION_ID:
        session_id = data.get("session_id", "")
        if session_id:
            line2_parts.append(f"[dim]sid:{session_id}[/]")

    return " ".join(line1_parts), " ".join(line2_parts)


def get_session_elapsed() -> str | None:
    """Get elapsed time of parent Claude Code process via PPID."""
    try:
        ppid = os.getppid()
        result = subprocess.run(
            ["ps", "-p", str(ppid), "-o", "etime="],
            capture_output=True, text=True, timeout=2,
        )
        raw = result.stdout.strip()
        if not raw:
            return None
        # ps etime format: [[DD-]HH:]MM:SS → compact "2h25m" / "45m" / "3d2h"
        parts = re.split(r"[-:]", raw)
        parts = [int(p) for p in parts]
        if len(parts) == 2:
            minutes, _ = parts
            if minutes < 1:
                return "<1m"
            return f"{minutes}m"
        if len(parts) == 3:
            hours, minutes, _ = parts
            if hours == 0:
                return f"{minutes}m"
            return f"{hours}h{minutes}m"
        if len(parts) == 4:
            days, hours, minutes, _ = parts
            if days == 0:
                return f"{hours}h{minutes}m"
            return f"{days}d{hours}h"
        return raw
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
        return None


def get_session_meta(pid: int) -> dict:
    """Read session metadata from ~/.claude/sessions/{pid}.json."""
    try:
        session_file = Path.home() / ".claude" / "sessions" / f"{pid}.json"
        if session_file.exists():
            return json.loads(session_file.read_text())
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def is_git_dirty() -> bool:
    """Check if working tree has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            capture_output=True, text=True, timeout=2,
        )
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


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
        line1, line2 = generate_status_line(data)
        ansi1 = render_to_ansi(line1)
        sys.stdout.write(ansi1)
        if line2:
            sys.stdout.write("\n")
            ansi2 = render_to_ansi(line2)
            sys.stdout.write(ansi2)
        sys.stdout.flush()
        sys.exit(0)
    except Exception:
        print("Claude Code")
        sys.exit(0)


if __name__ == "__main__":
    app()
