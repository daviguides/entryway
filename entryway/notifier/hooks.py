"""Hook event parsing and notification configuration."""

import json
from pathlib import Path

from .models import HookEvent, NotificationConfig

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


def _encode_project_dir(cwd: str) -> str:
    return cwd.replace("/", "-").replace(".", "-")


def _get_session_title(cwd: str | None, session_id: str | None) -> str | None:
    if not cwd or not session_id:
        return None
    try:
        sidecar = (
            CLAUDE_PROJECTS_DIR
            / _encode_project_dir(cwd)
            / session_id
            / "custom-title.json"
        )
        if sidecar.is_file():
            data = json.loads(sidecar.read_text(encoding="utf-8"))
            title = data.get("customTitle", "").strip()
            if title:
                return title
    except Exception:
        pass
    return None


def get_project_name(cwd: str | None) -> str:
    if not cwd:
        return "Claude Code"
    try:
        return Path(cwd).name
    except Exception:
        return "Claude Code"


def get_notification_config(event: HookEvent) -> NotificationConfig:
    """Map hook event to notification configuration."""
    session_title = _get_session_title(event.cwd, event.session_id)
    project = session_title or get_project_name(event.cwd).title()

    configs = {
        "Stop": NotificationConfig(
            title=f"✅ {project}",
            message="",
            subtitle="Processing completed",
            sound="Blow",
        ),
        "Notification": NotificationConfig(
            title=f"🔔 {project}",
            subtitle="Claude needs your input",
            message="",
            sound="Funk",
        ),
        "SubagentStop": NotificationConfig(
            title=f"✅ {project}",
            subtitle="Subagent completed",
            message="",
            sound="Blow",
        ),
    }

    return configs.get(
        event.hook_event_name,
        NotificationConfig(
            title=f"🔔 {project}",
            subtitle=f"Event: {event.hook_event_name}",
            message="",
            sound="Funk",
        ),
    )
