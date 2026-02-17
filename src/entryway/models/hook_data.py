"""Data models for Claude Code hooks."""

from pydantic import BaseModel, Field


class HookInput(BaseModel):
    """Input data received by UserPromptSubmit hook."""

    session_id: str = Field(description="Unique session identifier")
    transcript_path: str = Field(description="Path to conversation transcript")
    cwd: str = Field(description="Current working directory")
    hook_event_name: str = Field(description="Name of hook event")
    prompt: str = Field(description="User prompt text")


class HookSpecificOutput(BaseModel):
    """Hook-specific output structure."""

    hookEventName: str = Field(
        default="UserPromptSubmit",
        description="Name of hook event",
    )
    additionalContext: str = Field(
        default="",
        description="Context string injected for Claude",
    )


class HookOutput(BaseModel):
    """Output data returned by UserPromptSubmit hook."""

    decision: str | None = Field(
        default=None,
        description='Decision: "block" or None (allow)',
    )
    reason: str | None = Field(
        default=None,
        description="Reason for blocking",
    )
    systemMessage: str | None = Field(
        default=None,
        description="Message visible to user",
    )
    hookSpecificOutput: HookSpecificOutput | None = Field(
        default=None,
        description="Hook-specific output with additional context",
    )


class LoaderCommandsData(BaseModel):
    """Structure of loader_slash_commands.yaml file."""

    sessions: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Session ID mapped to list of loader commands",
    )
