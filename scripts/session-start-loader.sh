#!/bin/bash
# Outputs instruction for Claude to load Arché Universal Principles

cat << 'EOF'
---
description: Load Arché Universal Principles
---

# ⚠️ MANDATORY ACTION
## BEFORE DO ANYTHING LOAD ARCHÉ!!!

You can use simple: /arche:load

Or use the Read tool on the file below. DO NOT summarize or acknowledge - READ IT:

```
Read: ~/.claude/arche/prompts/load.md
```

Then follow the instructions inside that file.
EOF
