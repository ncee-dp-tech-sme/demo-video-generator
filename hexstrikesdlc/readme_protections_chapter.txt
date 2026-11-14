Can you add a chapter to the README explaining these protections?
Mon Nov  9 00:48:30 CET 2026

Added dedicated documentation section in README.md:
"## 🛡️ LLM Payload & Character Limit Protections (100k Chars & 128 Tools Guard)"

Documentation Structure Added:
1. Architectural Flow Diagram:
   - Visualizing query intake, schema minification, tool budgeting, output truncation, message compaction, and automatic error recovery retry.

2. Detailed Explanation of the 5 Protection Layers:
   - Tool Schema Minification (`core/hexstrike_tools.py`)
   - Query-Aware Dynamic Tool Selection (`select_tools_for_query`)
   - Scan Output Truncation (`_truncate_tool_result` in `core/agent.py`)
   - Pre-Flight Message History Compaction (`_compact_messages_if_needed` in `core/agent.py`)
   - Automatic Fallback Recovery Retry on provider character limit error (HTTP 400).
