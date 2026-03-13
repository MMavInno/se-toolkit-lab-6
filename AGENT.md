# Agent Architecture (Task 2 & 3)

## Overview

CLI agent that answers questions using an LLM with tools.

## Tools

### `read_file(path)`
Read file contents from project repository.

### `list_files(path)`
List files/directories at given path.

### `query_api(method, path, body)` (Task 3)
Call backend API with LMS_API_KEY authentication.

## Agentic Loop

1. Send question to LLM with tool schemas
2. If tool calls → execute, append results, repeat
3. If final answer → extract source, output JSON
4. Max 10 iterations

## Output Format

```json
{
  "answer": "...",
  "source": "wiki/git-workflow.md#section",
  "tool_calls": [...]
}
```

## Configuration

`.env.agent.secret`:
```
LLM_API_KEY=...
LLM_API_BASE=http://localhost:42005/v1
LLM_MODEL=qwen3-coder-plus
```

`.env.docker.secret`:
```
LMS_API_KEY=...  # For query_api authentication
```

## How to Run

```bash
uv run agent.py "Your question"
```

## Testing

```bash
uv run pytest tests/ -v
```
