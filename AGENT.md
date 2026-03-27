# Agent Architecture (Tasks 2 & 3)

## Overview

This CLI agent answers questions about a software project using an LLM with tools. It implements an agentic loop that iteratively calls tools until it finds an answer. The agent supports three tools: `read_file`, `list_files`, and `query_api`.

## Tools

### `read_file(path)`

Reads file contents from the project repository. Validates paths to prevent directory traversal attacks (rejects `../` and absolute paths). Returns file content up to 10,000 characters.

### `list_files(path)`

Lists files and directories at a given path. Skips hidden files and common ignored directories (`.git`, `node_modules`, `.venv`). Returns newline-separated entries.

### `query_api(method, path, body)` (Task 3)

Calls the backend API with HTTP methods (GET, POST). Authenticates using `LMS_API_KEY` from `.env.docker.secret` via `Authorization: Bearer` header. Returns JSON with `status_code` and `body`.

**Authentication Details:**

- The `LMS_API_KEY` is loaded from `.env.docker.secret` during agent initialization
- The key is sent in the `Authorization: Bearer <key>` header with every API request
- This ensures only authorized clients can query the backend

**Request Handling:**

- GET requests fetch data without a body
- POST requests can include a JSON body for mutations or complex queries
- Timeout is set to 30 seconds to prevent hanging
- Errors (timeout, connection failures, JSON parse errors) are returned as structured JSON

## Agentic Loop

The agent follows this loop (max 10 iterations):

1. Send user question + system prompt to LLM with tool schemas
2. LLM returns either:
   - **Tool calls**: Execute each tool, append results as `tool` messages, repeat
3. If max iterations reached, return partial answer

**Message Flow:**

```
System Prompt → User Question → LLM → Tool Calls → Execute Tools → Tool Results → LLM → Final Answer
```

## System Prompt Strategy

The system prompt guides tool selection based on question type:

| Question Type | Tool Strategy |
|--------------|---------------|
| Documentation (wiki) | `list_files("wiki/")` → `read_file()` |
| System facts (framework, ports) | `list_files()` → `read_file()` source code |
| Data queries (database, analytics) | `query_api()` |
| Bug diagnosis | `query_api()` for error → `read_file()` for source |

**Key Instructions:**

- Always include source references in answers
- Use the right tool for the question type
- Maximum 10 tool calls to prevent infinite loops

## Output Format

```json
{
  "answer": "The answer text with source reference",
  "source": "wiki/git-workflow.md#section",
  "tool_calls": [
    {"tool": "list_files", "args": {"path": "wiki/"}, "result": "..."}
  ]
}
```

## Configuration

All configuration is read from environment variables at runtime:

**`.env.agent.secret`** (LLM config):

```
LLM_API_KEY=...           # LLM provider API key
LLM_API_BASE=...          # LLM API endpoint URL
LLM_MODEL=...             # Model name (e.g., qwen3-coder-plus)
```

**`.env.docker.secret`** (Backend config):

```
LMS_API_KEY=...                        # For query_api authentication
AGENT_API_BASE_URL=http://localhost:42002  # Backend URL (optional, defaults to localhost:42002)
```

**Important:** The autochecker injects its own values for these variables during evaluation. Hardcoding values will cause the agent to fail.

## Security

- **Path validation**: Rejects `../` and absolute paths to prevent directory traversal
- **API authentication**: Uses Bearer token for all backend requests
- **Content limits**: File content capped at 10,000 characters to prevent token exhaustion
- **Timeout handling**: API requests timeout after 30 seconds

## Lessons Learned

1. **Tool call format**: The assistant message must come before tool responses in the message history. Initially I appended tool results directly, but the LLM expects the pattern: assistant (with tool_calls) → tool (with results).

2. **Prompt clarity**: Explicit instructions in the system prompt dramatically improve tool selection. Adding specific guidance like "For data questions, use query_api()" reduced incorrect tool usage.

3. **Iteration limits**: Setting max 10 iterations prevents infinite loops when the LLM gets stuck. This is especially important for complex questions that might require multiple tool calls.

4. **Windows CLI handling**: Quoted arguments need careful handling on Windows. Using `sys.argv[1]` directly works, but users must wrap questions in quotes.

5. **Environment variable loading**: Loading both `.env.agent.secret` and `.env.docker.secret` ensures all credentials are available. The `LMS_API_KEY` must come from the docker env file, not the agent env file.

6. **Error handling in tools**: Returning structured error messages (e.g., `{"status_code": 0, "body": "Error: timeout"}`) allows the LLM to understand what went wrong and potentially retry.

## Testing

Run: `uv run pytest tests/ -v`

Tests verify:

- Valid JSON output with required fields (`answer`, `source`, `tool_calls`)
- Correct tool usage for different question types
- Path security and authentication

**Test Cases:**

1. Framework question → expects `read_file` in tool_calls
2. Database count question → expects `query_api` in tool_calls

## Final Evaluation Score

Run `uv run run_eval.py` to check the local benchmark score. The autochecker tests additional hidden questions not present in the local eval script.
