# entryway

Claude Code starter kit — settings, hooks, status line, and notifications.

## Install

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/daviguides/entryway/main/install.sh)"
```

## What it installs

| Component | Description |
|-----------|-------------|
| `settings.json` | Curated Claude Code settings with permissions, hooks, and plugins |
| `status_line` | Custom status bar: model, machine, directory, git branch, cost, context window |
| `slash_command` | Hook that prevents duplicate load-context commands per session |
| `claude_notifier` | Desktop notifications on Stop/Notification events (macOS, Linux, SSH relay) |
| `session-start-loader` | Session start hook that triggers Arche principles loading |
| Plugins | [arche](https://github.com/daviguides/arche), [zazen](https://github.com/daviguides/zazen), [shodo](https://github.com/daviguides/shodo) |

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- git

## Test

```bash
status_line --echo          # Test status line
claude_notifier -e Stop -d  # Test notifier (debug)
slash_command -p "/test" -d  # Test slash command hook
```

## Update

Re-run the installer or:

```bash
cd ~/.local/share/entryway && git pull
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MACHINE` | Machine name shown in status line |
| `NOTIFY_MAC_HOST` | Mac hostname for SSH notification relay (headless Linux) |

## License

MIT
