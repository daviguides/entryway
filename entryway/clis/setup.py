"""Merge entryway settings into user's Claude Code settings.json.

Performs intelligent merge:
- hooks, statusLine: REPLACE (entryway core)
- permissions (allow/deny/ask): MERGE (keep user's, add new)
- enabledPlugins: MERGE from plugins.yaml + entryway.yaml extras
- alwaysThinkingEnabled: SET IF ABSENT
- unknown fields: PRESERVE
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import typer
import yaml
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()

CLAUDE_DIR = Path.home() / ".claude"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"

# Resolve paths relative to this package
PACKAGE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_FILE = PACKAGE_DIR.parent / "settings.json"
PLUGINS_FILE = PACKAGE_DIR / "data" / "plugins.yaml"
EXTRA_PLUGINS_FILE = (
    Path.home()
    / "work"
    / "sources"
    / "remote-dev-node"
    / "data"
    / "entryway.yaml"
)

# Fields that replace entirely (entryway core)
REPLACE_FIELDS = {"hooks", "statusLine"}

# Fields that merge lists (union, deduplicated)
MERGE_LIST_FIELDS = {
    ("permissions", "allow"),
    ("permissions", "deny"),
    ("permissions", "ask"),
}

# Fields set only if absent
SET_IF_ABSENT_FIELDS = {"alwaysThinkingEnabled"}


# ============================================================
# Plugin loading
# ============================================================


def load_plugin_list(path: Path) -> list[dict]:
    """Load plugins from YAML (list of {name, install?})."""
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [p for p in raw if isinstance(p, dict) and "name" in p]
    return []


def load_extra_plugins() -> tuple[Path | None, list[dict]]:
    """Load extra plugins from fixed path if it exists."""
    if not EXTRA_PLUGINS_FILE.exists():
        return None, []
    try:
        raw = yaml.safe_load(
            EXTRA_PLUGINS_FILE.read_text(encoding="utf-8")
        )
        if isinstance(raw, dict) and "plugins-extra" in raw:
            extras = raw["plugins-extra"]
            if isinstance(extras, list):
                plugins = [
                    p for p in extras if isinstance(p, dict) and "name" in p
                ]
                return EXTRA_PLUGINS_FILE, plugins
    except (yaml.YAMLError, OSError):
        pass
    return None, []


def get_all_plugins() -> tuple[list[dict], Path | None]:
    """Get combined plugin list (base + extras).

    Returns (plugins, extra_path or None).
    """
    plugins = load_plugin_list(PLUGINS_FILE)
    extra_path, extras = load_extra_plugins()
    if extras:
        # Deduplicate by name, extras win
        existing = {p["name"] for p in plugins}
        for p in extras:
            if p["name"] not in existing:
                plugins.append(p)
    return plugins, extra_path


def plugins_to_enabled_dict(plugins: list[dict]) -> dict[str, bool]:
    """Convert plugin list to enabledPlugins dict."""
    return {p["name"]: True for p in plugins}


# ============================================================
# JSON helpers
# ============================================================


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ============================================================
# Merge logic
# ============================================================


def merge_settings(
    user: dict, template: dict, plugins: dict[str, bool]
) -> dict:
    """Merge template and plugins into user settings."""
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

    # 3. Merge enabledPlugins
    if plugins:
        user_plugins = result.get("enabledPlugins", {})
        merged = dict(user_plugins)
        for k, v in plugins.items():
            if k not in merged:
                merged[k] = v
        result["enabledPlugins"] = merged

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


# ============================================================
# CLI
# ============================================================


@app.command()
def main(
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would change"
    ),
    template: Path = typer.Option(
        TEMPLATE_FILE, "--template", "-t", help="Template settings.json"
    ),
    list_installers: bool = typer.Option(
        False,
        "--list-installers",
        help="Output plugin installers as name|url lines",
    ),
) -> None:
    """Merge entryway settings into ~/.claude/settings.json."""
    all_plugins, extra_path = get_all_plugins()

    # --list-installers: output for bash consumption
    if list_installers:
        if extra_path:
            print(f"#extra:{extra_path}", file=sys.stderr)
        for p in all_plugins:
            url = p.get("install", "")
            if url:
                # short name: "arche@daviguides" -> "arche"
                short = p["name"].split("@")[0]
                print(f"{short}|{url}")
        return

    if not template.exists():
        console.print(f"[red]Template not found:[/red] {template}")
        sys.exit(1)

    template_data = load_json(template)
    plugins_dict = plugins_to_enabled_dict(all_plugins)

    if extra_path:
        console.print(
            f"[dim]Extra plugins from:[/dim] {extra_path}"
        )

    if SETTINGS_FILE.exists():
        user_data = load_json(SETTINGS_FILE)
        merged = merge_settings(user_data, template_data, plugins_dict)
    else:
        user_data = {}
        merged = merge_settings({}, template_data, plugins_dict)

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
    added_allow = set(
        merged.get("permissions", {}).get("allow", [])
    ) - set(user_data.get("permissions", {}).get("allow", []))

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
