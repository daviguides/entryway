"""System notification sender for macOS, Linux, and SSH relay."""

import os
import shutil
import subprocess
import sys
from typing import Literal

from .models import NotificationConfig

ExitCode = Literal[0, 1]

NOTIFY_MAC_HOST = os.environ.get("NOTIFY_MAC_HOST")


def send_notification(
    config: NotificationConfig, *, debug: bool = False
) -> ExitCode:
    """Send system notification via platform-specific notifier.

    Priority: SSH to Mac > terminal-notifier > notify-send.
    Exits silently if no notifier is available.
    """
    if NOTIFY_MAC_HOST:
        return _send_ssh_mac(config, debug)

    cmd = _build_command(config)
    if cmd is None:
        return 0

    if debug:
        print(f"Debug: {' '.join(cmd)}", file=sys.stderr)
        return 0

    return _execute_command(cmd)


def _send_ssh_mac(
    config: NotificationConfig, debug: bool
) -> ExitCode:
    message = config.message or config.subtitle or ""
    notifier_cmd = (
        f"terminal-notifier"
        f" -title '{config.title}'"
        f" -message '{message}'"
        f" -sound '{config.sound}'"
    )

    if debug:
        print(
            f'Debug SSH: ssh {NOTIFY_MAC_HOST} "{notifier_cmd}"',
            file=sys.stderr,
        )
        return 0

    try:
        subprocess.run(
            [
                "ssh",
                "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=5",
                NOTIFY_MAC_HOST,
                notifier_cmd,
            ],
            capture_output=True,
            timeout=10,
            check=False,
        )
        return 0
    except Exception:
        return 0


def _build_command(config: NotificationConfig) -> list[str] | None:
    if shutil.which("terminal-notifier"):
        cmd = [
            "terminal-notifier",
            "-sound", config.sound,
            "-title", config.title,
            "-message", config.message or config.subtitle or "",
        ]
        if config.subtitle:
            cmd.extend(["-subtitle", config.subtitle])
        return cmd

    if shutil.which("notify-send"):
        body = config.message or config.subtitle or ""
        return ["notify-send", config.title, body]

    return None


def _execute_command(cmd: list[str]) -> ExitCode:
    try:
        subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, check=False
        )
        return 0
    except Exception:
        return 0
