# entryway

Claude Code starter kit — settings, hooks, status line, and notifications.

## Install

```bash
bash -c "$(gh api repos/daviguides/entryway/contents/install.sh --jq '.content' | base64 -d)"
```

Requires: `gh` (authenticated), `uv`, `git`.

## Architecture

```
entryway/
├── install.sh                 # One-line installer (reaper-style UX)
├── settings.json              # Template (permissions, hooks, statusLine)
├── scripts/
│   └── session-start-loader.sh  # SessionStart hook → loads Arché
├── entryway/
│   ├── clis/
│   │   ├── status_line.py     # Status bar (model, branch, cost, context)
│   │   ├── slash_command.py   # Load-context dedup hook
│   │   └── setup.py           # Settings merge CLI
│   ├── notifier/
│   │   ├── cli.py             # Notification CLI entry point
│   │   ├── hooks.py           # Event → notification config mapping
│   │   ├── models.py          # HookEvent, NotificationConfig
│   │   └── notifier.py        # macOS/Linux/SSH notification sender
│   ├── hook_utils/
│   │   └── slash_command_parser.py
│   ├── models/
│   │   └── hook_data.py       # HookInput, HookOutput, LoaderCommandsData
│   ├── persistence/
│   │   └── yaml_store.py      # YAML-based session command cache
│   └── data/
│       └── plugins.yaml       # Base plugin list (name + repo)
└── tests/
    ├── test_status_line.sh    # Status line functional tests
    └── test_slash_command.sh  # Slash command dedup tests
```

## CLIs

| Command | Hook | Description |
|---------|------|-------------|
| `status_line` | `statusLine` | Status bar: model, machine, dir, branch, cost, context window, session ID |
| `slash_command` | `UserPromptSubmit` | Blocks duplicate load-context commands per session |
| `claude_notifier` | `Stop`, `Notification` | Desktop notifications (macOS terminal-notifier, Linux notify-send, SSH relay) |
| `entryway-setup` | — | Merges template into user's `settings.json` |

## Settings Merge Strategy (`entryway-setup`)

| Field | Strategy |
|-------|----------|
| `hooks`, `statusLine` | **replace** (entryway core) |
| `permissions.allow/deny/ask` | **merge** (keep user's, add new) |
| `enabledPlugins` | **merge** from `plugins.yaml` + extras |
| `alwaysThinkingEnabled` | **set if absent** |
| Unknown fields | **preserve** |

## Plugin Configuration

**Base plugins** — `entryway/data/plugins.yaml`:
```yaml
- name: arche@daviguides
  repo: daviguides/arche
```

**Extra plugins** (optional) — `~/.claude/entryway-extras.yaml`:
```yaml
plugins-extra:
  - name: my-plugin@user
    repo: user/my-plugin
```

All plugins install via `gh api` (works for public and private repos).

## Development

```bash
uv sync                        # Install dependencies
uv run status_line --echo      # Test status line
uv run slash_command -p "/test" -d  # Test slash command
uv run claude_notifier -e Stop -d   # Test notifier
uv run entryway-setup --dry-run     # Preview settings merge
./tests/test_status_line.sh    # Run status line tests
./tests/test_slash_command.sh  # Run slash command tests
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MACHINE` | Machine name shown in status line |
| `NOTIFY_MAC_HOST` | Mac hostname for SSH notification relay |
