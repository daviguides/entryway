#!/bin/bash
# Test script for status_line
# Tests various scenarios with mock data

echo "======================================================"
echo "Test 1: Full status line (all fields)"
echo "======================================================"
cat <<'EOF' | status_line
{
  "model": { "display_name": "Opus 4.6" },
  "workspace": { "current_dir": "/Users/dev/project" },
  "version": "1.0.80",
  "cost": { "total_cost_usd": 12.27 },
  "context_window": {
    "used_percentage": 78.0,
    "context_window_size": 200000
  },
  "session_id": "7940d8f1-b2e2-4e1c-8867-8fc60cde818d"
}
EOF
echo ""
echo ""

echo "======================================================"
echo "Test 2: Low context usage (green)"
echo "======================================================"
cat <<'EOF' | status_line
{
  "model": { "display_name": "Sonnet 4.5" },
  "workspace": { "current_dir": "/tmp/test" },
  "cost": { "total_cost_usd": 0.05 },
  "context_window": {
    "used_percentage": 15.3,
    "context_window_size": 200000
  },
  "session_id": "abc123"
}
EOF
echo ""
echo ""

echo "======================================================"
echo "Test 3: Critical context usage (>90%, bold red)"
echo "======================================================"
cat <<'EOF' | status_line
{
  "model": { "display_name": "Opus 4.6" },
  "workspace": { "current_dir": "/home/user/big-project" },
  "cost": { "total_cost_usd": 45.89 },
  "context_window": {
    "used_percentage": 94.7,
    "context_window_size": 200000
  },
  "session_id": "def456"
}
EOF
echo ""
echo ""

echo "======================================================"
echo "Test 4: Without git repository"
echo "======================================================"
cd /tmp
cat <<'EOF' | status_line
{
  "model": { "display_name": "Haiku 4.5" },
  "workspace": { "current_dir": "/tmp" },
  "context_window": {
    "used_percentage": 0,
    "context_window_size": 200000
  }
}
EOF
cd - > /dev/null
echo ""
echo ""

echo "======================================================"
echo "Test 5: Minimal data (fallback handling)"
echo "======================================================"
echo '{}' | status_line
echo ""
echo ""

echo "======================================================"
echo "Test 6: Invalid JSON (error handling)"
echo "======================================================"
echo 'invalid json' | status_line
echo ""
echo ""

echo "======================================================"
echo "Test 7: Echo mode (sample data)"
echo "======================================================"
status_line --echo
echo ""
echo ""

echo "======================================================"
echo "All tests completed!"
echo "======================================================"
