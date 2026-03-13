# Agent Architecture (Tasks 2 & 3)

## Overview

This CLI agent answers questions about a software project using an LLM with tools. It implements an agentic loop that iteratively calls tools until it finds an answer.

## Tools

### `read_file(path)`
Reads file contents from the project repository. Validates paths to prevent directory traversal attacks (rejects `../` and absolute paths). Returns file content up to 10,000 characters.

### `list_files(path)`
Lists files and directories at a given path. Skips hidden files and common ignored directories (`.git`, `node_modules`, `.venv`). Returns newline-separated entries.

### `query_api(method, path, body)` (Task 3)
Calls the backend API with HTTP methods (GET, POST). Authenticates using `LMS_API_KEY` from `.env.docker.secret` via `Authorization: Bearer` header. Returns JSON with `status_code` and `body`.

## Agentic Loop

The agent follows this loop (max 10 iterations):

1. Send user question + system prompt to LLM with tool schemas
2. LLM returns either:
   - **Tool calls**: Execute each tool, append results as `tool` messages, repeat
   - **Final answer**: Extract source reference, output JSON
3. If max iterations reached, return partial answer

## System Prompt Strategy

The system prompt guides tool selection:
- **Documentation questions** → `list_files("wiki/")` then `read_file()`
- **System questions** → `list_files()` to explore, then `read_file()` source code
- **Data questions** → `query_api()` for database/analytics

## Output Format

```json
{
  "answer": "The answer text",
  "source": "wiki/git-workflow.md#section",
  "tool_calls": [
    {"tool": "list_files", "args": {"path": "wiki/"}, "result": "..."}
  ]
}
```

## Configuration

**`.env.agent.secret`** (LLM config):
```
LLM_API_KEY=...
LLM_API_BASE=http://localhost:42005/v1
LLM_MODEL=qwen3-coder-plus
```

**`.env.docker.secret`** (Backend config):
```
LMS_API_KEY=...  # For query_api authentication
AGENT_API_BASE_URL=http://localhost:42002  # Optional
```

## Security

- Path validation prevents directory traversal
- API authentication uses Bearer token
- Content size limits prevent token exhaustion

## Lessons Learned

1. **Tool call format**: Assistant message must come before tool responses
2. **Prompt clarity**: Explicit instructions improve tool selection
3. **Iteration limits**: Max 10 calls prevents infinite loops
4. **Windows CLI**: Quoted arguments need careful handling

## Testing

Run: `uv run pytest tests/ -v`

Tests verify:
- Valid JSON output with required fields
- Correct tool usage for different question types
- Path security and authentication
