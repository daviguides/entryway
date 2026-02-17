"""Slash command parser for Claude Code hooks."""

import re

SLASH_COMMAND_PATTERN = r"^\/(\S+)"
PURGE_COMMANDS = {"/compact", "/clear"}


class SlashCommandParser:
    """Parser for slash commands in user prompts."""

    @staticmethod
    def is_slash_command(prompt: str) -> bool:
        if not prompt:
            return False
        return prompt.strip().startswith("/")

    @staticmethod
    def extract_command(prompt: str) -> str | None:
        if not prompt:
            return None
        match = re.match(SLASH_COMMAND_PATTERN, prompt.strip())
        if match:
            return match.group(1)
        return None

    @staticmethod
    def is_load_context_command(command: str) -> bool:
        if not command:
            return False
        command_lower = command.lower()
        return "load" in command_lower and "context" in command_lower

    @staticmethod
    def is_purge_command(command: str) -> bool:
        if not command:
            return False
        return f"/{command}" in PURGE_COMMANDS
