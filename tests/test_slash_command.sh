#!/usr/bin/env bash
set -e

TEST_SESSION="test-session-$$"
YAML_FILE="$HOME/.claude/data/loader_slash_commands.yaml"

echo "=== Slash Command Hook Tests ==="
echo ""

# Test 1: Normal prompt passes through
echo "Test 1: Normal prompt"
echo '{"session_id": "test", "transcript_path": "/tmp/test.jsonl", "cwd": "/tmp", "hook_event_name": "UserPromptSubmit", "prompt": "normal"}' | slash_command
echo "✓ Passed"

# Test 2: Non-load slash command passes through
echo "Test 2: Non-load slash command"
echo '{"session_id": "test", "transcript_path": "/tmp/test.jsonl", "cwd": "/tmp", "hook_event_name": "UserPromptSubmit", "prompt": "/help"}' | slash_command
echo "✓ Passed"

# Test 3: Load command first time passes and caches
echo "Test 3: Load command first time"
echo '{"session_id": "'"$TEST_SESSION"'", "transcript_path": "/tmp/test.jsonl", "cwd": "/tmp", "hook_event_name": "UserPromptSubmit", "prompt": "/code-zen:load-python-context"}' | slash_command
echo "✓ Passed"

# Test 4: Load command duplicate should block
echo "Test 4: Load command duplicate (should block)"
OUTPUT=$(echo '{"session_id": "'"$TEST_SESSION"'", "transcript_path": "/tmp/test.jsonl", "cwd": "/tmp", "hook_event_name": "UserPromptSubmit", "prompt": "/code-zen:load-python-context"}' | slash_command)
if echo "$OUTPUT" | grep -q "decision.*block"; then
    echo "✓ Passed - Blocked as expected"
else
    echo "✗ Failed - Should have blocked"
    exit 1
fi

# Test 5: Different load command should pass
echo "Test 5: Different load command"
echo '{"session_id": "'"$TEST_SESSION"'", "transcript_path": "/tmp/test.jsonl", "cwd": "/tmp", "hook_event_name": "UserPromptSubmit", "prompt": "/ymd-spec:load-ymd-context"}' | slash_command
echo "✓ Passed"

# Test 6: Purge with /clear should clear session cache
echo "Test 6: Purge with /clear"
echo '{"session_id": "'"$TEST_SESSION"'", "transcript_path": "/tmp/test.jsonl", "cwd": "/tmp", "hook_event_name": "UserPromptSubmit", "prompt": "/clear"}' | slash_command
echo "✓ Passed - Purge command executed"

# Test 7: After purge, load command should work again
echo "Test 7: Load command after /clear (should pass)"
OUTPUT=$(echo '{"session_id": "'"$TEST_SESSION"'", "transcript_path": "/tmp/test.jsonl", "cwd": "/tmp", "hook_event_name": "UserPromptSubmit", "prompt": "/code-zen:load-python-context"}' | slash_command)
if [ -z "$OUTPUT" ]; then
    echo "✓ Passed - Command allowed after purge"
else
    echo "✗ Failed - Should allow after purge"
    echo "Output: $OUTPUT"
    exit 1
fi

# Test 8: Duplicate again after reload
echo "Test 8: Duplicate after reload (should block again)"
OUTPUT=$(echo '{"session_id": "'"$TEST_SESSION"'", "transcript_path": "/tmp/test.jsonl", "cwd": "/tmp", "hook_event_name": "UserPromptSubmit", "prompt": "/code-zen:load-python-context"}' | slash_command)
if echo "$OUTPUT" | grep -q "decision.*block"; then
    echo "✓ Passed - Blocked again as expected"
else
    echo "✗ Failed - Should block duplicate"
    exit 1
fi

# Test 9: Purge with /compact should also clear cache
echo "Test 9: Purge with /compact"
echo '{"session_id": "'"$TEST_SESSION"'", "transcript_path": "/tmp/test.jsonl", "cwd": "/tmp", "hook_event_name": "UserPromptSubmit", "prompt": "/compact"}' | slash_command
echo "✓ Passed - Purge with /compact executed"

# Test 10: After /compact, load should work again
echo "Test 10: Load command after /compact (should pass)"
OUTPUT=$(echo '{"session_id": "'"$TEST_SESSION"'", "transcript_path": "/tmp/test.jsonl", "cwd": "/tmp", "hook_event_name": "UserPromptSubmit", "prompt": "/code-zen:load-python-context"}' | slash_command)
if [ -z "$OUTPUT" ]; then
    echo "✓ Passed - Command allowed after /compact"
else
    echo "✗ Failed - Should allow after /compact"
    echo "Output: $OUTPUT"
    exit 1
fi

# Cleanup: Remove test session from YAML
if [ -f "$YAML_FILE" ]; then
    uv run python3 <<EOF
import yaml
from pathlib import Path

yaml_file = Path("$YAML_FILE")
if yaml_file.exists():
    data = yaml.safe_load(yaml_file.read_text()) or {}
    sessions = data.get("sessions", {})

    if "$TEST_SESSION" in sessions:
        del sessions["$TEST_SESSION"]
        data["sessions"] = sessions
        yaml_file.write_text(yaml.safe_dump(data))
EOF
fi

echo ""
echo "=== All tests passed! ✓ ==="
