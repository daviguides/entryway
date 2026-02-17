#!/bin/bash
# Test script for status_line.py
# Tests various scenarios with mock data

echo "======================================================"
echo "Test 1: Basic status line (model + dir + git)"
echo "======================================================"
cat <<'EOF' | status_line
{
  "hook_event_name": "Status",
  "session_id": "test123",
  "transcript_path": "/tmp/test.json",
  "cwd": "/Users/daviguides/work/sources/my/genai/ymd-prompt",
  "model": {
    "id": "claude-sonnet-4",
    "display_name": "Sonnet 4"
  },
  "workspace": {
    "current_dir": "/Users/daviguides/work/sources/my/genai/ymd-prompt",
    "project_dir": "/Users/daviguides/work/sources/my/genai/ymd-prompt"
  },
  "version": "1.0.80",
  "output_style": { "name": "default" },
  "cost": {
    "total_cost_usd": 0.01234,
    "total_duration_ms": 45000,
    "total_api_duration_ms": 2300,
    "total_lines_added": 156,
    "total_lines_removed": 23
  }
}
EOF
echo ""
echo ""

echo "======================================================"
echo "Test 2: Without git repository"
echo "======================================================"
cd /tmp
cat <<'EOF' | status_line
{
  "hook_event_name": "Status",
  "model": {
    "display_name": "Opus"
  },
  "workspace": {
    "current_dir": "/tmp"
  }
}
EOF
cd - > /dev/null
echo ""
echo ""

echo "======================================================"
echo "Test 3: Minimal data (fallback handling)"
echo "======================================================"
echo '{}' | status_line
echo ""
echo ""

echo "======================================================"
echo "Test 4: Invalid JSON (error handling)"
echo "======================================================"
echo 'invalid json' | status_line
echo ""
echo ""

echo "======================================================"
echo "All tests completed!"
echo "======================================================"
