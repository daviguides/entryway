"""Hook event parsing and notification configuration."""

from pathlib import Path

from .models import HookEvent, NotificationConfig


def get_project_name(cwd: str | None) -> str:
    if not cwd:
        return "Claude Code"
    try:
        return Path(cwd).name
    except Exception:
        return "Claude Code"


def get_notification_config(event: HookEvent) -> NotificationConfig:
    """Map hook event to notification configuration."""
    project = get_project_name(event.cwd).title()

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
