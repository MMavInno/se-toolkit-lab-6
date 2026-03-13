# Task 2 Plan: The Documentation Agent

## Overview

Extend agent from Task 1 with tools (`read_file`, `list_files`) and agentic loop to answer questions by reading documentation.

## Implementation

### Tool Schemas
- `read_file(path)`: Read file contents with path security
- `list_files(path)`: List directory contents

### Agentic Loop
- Max 10 iterations
- Execute tool calls, feed results back to LLM
- Extract source reference from final answer

### Path Security
- Reject `../` (directory traversal)
- Reject absolute paths
- Verify resolved path within project root

## Testing

2 regression tests:
1. `test_agent_uses_list_files_tool` - Wiki listing question
2. `test_agent_uses_read_file_for_merge_conflict` - Merge conflict question

## Acceptance Criteria

- [x] `plans/task-2.md` exists
- [x] `read_file` and `list_files` tool schemas defined
- [x] Agentic loop executes tool calls
- [x] `tool_calls` populated in output
- [x] `source` field identifies wiki section
- [x] Path security prevents traversal
- [x] `AGENT.md` documents tools and loop
- [x] 2 regression tests pass
