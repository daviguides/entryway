"""Merge entryway settings into user's Claude Code settings.json.

Performs intelligent merge:
- hooks, statusLine: REPLACE (entryway core)
- permissions (allow/deny/ask): MERGE (keep user's, add new)
- enabledPlugins: MERGE (keep user's, add new)
- alwaysThinkingEnabled: SET IF ABSENT
- unknown fields: PRESERVE
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()

CLAUDE_DIR = Path.home() / ".claude"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"

# Resolve template relative to this package
TEMPLATE_FILE = Path(__file__).resolve().parent.parent.parent / "settings.json"

# Fields that replace entirely (entryway core)
REPLACE_FIELDS = {"hooks", "statusLine"}

# Fields that merge lists (union, deduplicated)
MERGE_LIST_FIELDS = {
    ("permissions", "allow"),
    ("permissions", "deny"),
    ("permissions", "ask"),
}

# Fields that merge dicts (keep existing, add new keys)
MERGE_DICT_FIELDS = {"enabledPlugins"}

# Fields set only if absent
SET_IF_ABSENT_FIELDS = {"alwaysThinkingEnabled"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def merge_settings(user: dict, template: dict) -> dict:
    """Merge template into user settings."""
    result = dict(user)

    # 1. Replace fields
    for key in REPLACE_FIELDS:
        if key in template:
            result[key] = template[key]

    # 2. Merge permission lists
    for parent_key, child_key in MERGE_LIST_FIELDS:
        if parent_key not in template:
            continue
        if parent_key not in result:
            result[parent_key] = {}
        template_list = template.get(parent_key, {}).get(child_key, [])
        user_list = result.get(parent_key, {}).get(child_key, [])
        merged = list(dict.fromkeys(user_list + template_list))
        result[parent_key][child_key] = merged

    # Preserve permissions.defaultMode from template if not set
    if "permissions" in template:
        perms = result.setdefault("permissions", {})
        if "defaultMode" not in perms:
            perms["defaultMode"] = template["permissions"].get(
                "defaultMode", "default"
            )

    # 3. Merge dict fields (enabledPlugins)
    for key in MERGE_DICT_FIELDS:
        if key not in template:
            continue
        user_dict = result.get(key, {})
        template_dict = template[key]
        merged = dict(user_dict)
        for k, v in template_dict.items():
            if k not in merged:
                merged[k] = v
        result[key] = merged

    # 4. Set if absent
    for key in SET_IF_ABSENT_FIELDS:
        if key not in result and key in template:
            result[key] = template[key]

    return result


def backup_settings() -> Path | None:
    if not SETTINGS_FILE.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup = SETTINGS_FILE.with_suffix(f".backup.{timestamp}")
    backup.write_text(
        SETTINGS_FILE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return backup


@app.command()
def main(
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would change"
    ),
    template: Path = typer.Option(
        TEMPLATE_FILE, "--template", "-t", help="Template settings.json"
    ),
) -> None:
    """Merge entryway settings into ~/.claude/settings.json."""
    if not template.exists():
        console.print(f"[red]Template not found:[/red] {template}")
        sys.exit(1)

    template_data = load_json(template)

    if SETTINGS_FILE.exists():
        user_data = load_json(SETTINGS_FILE)
        merged = merge_settings(user_data, template_data)
    else:
        user_data = {}
        merged = template_data

    if dry_run:
        console.print("[bold]Would write:[/bold]")
        console.print(json.dumps(merged, indent=2))
        return

    backup = backup_settings()
    if backup:
        console.print(f"[dim]Backup:[/dim] {backup.name}")

    save_json(SETTINGS_FILE, merged)

    # Report what was added
    added_plugins = set(merged.get("enabledPlugins", {})) - set(
        user_data.get("enabledPlugins", {})
    )
    added_allow = set(merged.get("permissions", {}).get("allow", [])) - set(
        user_data.get("permissions", {}).get("allow", [])
    )

    if added_plugins:
        for p in sorted(added_plugins):
            console.print(f"[green]+[/green] plugin: {p}")
    if added_allow:
        console.print(
            f"[green]+[/green] {len(added_allow)} new permission rules"
        )

    console.print("[green]Settings merged.[/green]")


if __name__ == "__main__":
    app()
