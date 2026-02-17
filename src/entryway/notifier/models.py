"""Data models for Claude Code hook events and notifications."""

from pydantic import BaseModel, Field


class HookEvent(BaseModel):
    """Event received from Claude Code hooks."""

    hook_event_name: str = Field(
        ..., description="Event name (Stop, Notification, etc)"
    )
    session_id: str | None = Field(None, description="Current session ID")
    cwd: str | None = Field(None, description="Current working directory")
    transcript_path: str | None = Field(
        None, description="Path to session transcript"
    )


class NotificationConfig(BaseModel):
    """Configuration for a system notification."""

    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message body")
    subtitle: str | None = Field(None, description="Optional subtitle")
    sound: str = Field("Funk", description="System sound name")
