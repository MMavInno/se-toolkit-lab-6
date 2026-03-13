# Agent Architecture

## Overview

This project implements a CLI agent (`agent.py`) that answers questions about a software project using an LLM (Large Language Model) with tools. The agent connects to a Qwen Code API endpoint and returns structured JSON responses with source references.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  User (CLI)     │────▶│   agent.py       │────▶│  Qwen Code API      │
│  (question)     │     │  (agentic loop)  │     │  (LLM inference)    │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
                               │
                               │ tool calls
                               ▼
        ┌──────────────────────────────────────────┐
        │  Tools:                                   │
        │  - list_files(path)                       │
        │  - read_file(path)                        │
        │  - query_api(method, path, body)          │
        └──────────────────────────────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  JSON Response   │
                        │  (stdout)        │
                        └──────────────────┘
```

## Components

### 1. `agent.py`

The main CLI program that implements an **agentic loop**:

1. Parse command-line arguments (the user's question)
2. Load configuration from `.env.agent.secret` and `.env.docker.secret`
3. Send question to LLM with tool schemas
4. If LLM returns tool calls:
   - Execute each tool
   - Append results to conversation
   - Repeat from step 3
5. If LLM returns final answer:
   - Extract source reference
   - Output JSON to stdout

**Input:**
```bash
uv run agent.py "Your question here"
```

**Output:**
```json
{
  "answer": "The answer from the LLM",
  "source": "wiki/git-workflow.md#section",
  "tool_calls": [
    {"tool": "list_files", "args": {"path": "wiki/"}, "result": "..."},
    {"tool": "read_file", "args": {"path": "wiki/git.md"}, "result": "..."}
  ]
}
```

### 2. Configuration Files

**`.env.agent.secret`** - LLM configuration:
```bash
LLM_API_KEY=my-secret-qwen-key
LLM_API_BASE=http://localhost:42005/v1
LLM_MODEL=qwen3-coder-plus
```

**`.env.docker.secret`** - Backend API configuration:
```bash
LMS_API_KEY=my-lab-6-secret-key
AUTOCHECKER_API_URL=https://auche.namaz.live
...
```

### 3. LLM Provider

**Provider:** Qwen Code API (self-hosted via `qwen-code-oai-proxy`)

- **Model:** `qwen3-coder-plus`
- **API Format:** OpenAI-compatible chat completions
- **Endpoint:** `POST /v1/chat/completions`

## Tools

### `read_file(path)`

Read the contents of a file from the project repository.

- **Parameters:** `path` (string) - Relative path from project root
- **Returns:** File contents as string, or error message
- **Security:** Rejects paths with `../` to prevent directory traversal

### `list_files(path)`

List files and directories at a given path.

- **Parameters:** `path` (string) - Relative directory path
- **Returns:** Newline-separated list of entries
- **Security:** Rejects paths with `../` to prevent directory traversal

### `query_api(method, path, body)`

Call the backend API to query data or check system status.

- **Parameters:** 
  - `method` (string) - HTTP method (GET, POST, etc.)
  - `path` (string) - API endpoint (e.g., `/items/`)
  - `body` (string, optional) - JSON request body
- **Returns:** JSON string with `status_code` and `body`
- **Authentication:** Uses `LMS_API_KEY` from `.env.docker.secret`

## Agentic Loop

The agent implements the following loop:

```python
messages = [system_prompt, {"role": "user", "content": question}]
tool_calls_log = []

for iteration in range(max_iterations=10):
    # Call LLM with tool schemas
    response = call_llm(messages, tools=TOOLS)
    
    # Check if LLM wants to call tools
    if response has tool_calls:
        # Add assistant message with tool calls
        messages.append(response_message)
        
        # Execute each tool and append results
        for tool_call in tool_calls:
            result = execute_tool(tool_call)
            messages.append({"role": "tool", "content": result})
            tool_calls_log.append({tool, args, result})
    else:
        # LLM provided final answer
        answer = response.content
        source = extract_source(answer)
        return answer, source, tool_calls_log
```

## System Prompt Strategy

The system prompt guides the LLM to select appropriate tools:

```
You are a helpful assistant that answers questions about a software project.

You have access to these tools:
1. list_files(path) - List files in a directory
2. read_file(path) - Read contents of a file  
3. query_api(method, path, body) - Call the backend API

To answer questions:
- For documentation questions: Use list_files("wiki/") to find relevant files, then read_file() to read them
- For system questions (framework, ports, etc.): 
  - First use list_files() to explore the directory structure (e.g., backend/, backend/app/)
  - Then use read_file() to read the actual source files (e.g., backend/app/main.py)
  - Look for framework imports like "fastapi", "flask", "django" in the code
- For data questions (database content, analytics): Use query_api() to query the backend
- IMPORTANT: After using list_files() to find files, ALWAYS use read_file() to read the relevant files
- Always include source references in your answer (e.g., wiki/git-workflow.md#section or backend/app/main.py)
- Be concise and accurate
- Maximum 10 tool calls per question
```

## Tool Selection Logic

The LLM decides which tool to use based on the question type:

| Question Type | Example | Expected Tools |
|--------------|---------|----------------|
| Documentation | "How do you resolve a merge conflict?" | `list_files` → `read_file` on wiki/ |
| Wiki listing | "What files are in the wiki?" | `list_files` |
| System facts | "What framework does the backend use?" | `list_files` → `read_file` on backend/ |
| Data queries | "How many items are in the database?" | `query_api` GET /items/ |
| Analytics | "What is the completion rate?" | `query_api` GET /analytics/... |

## Data Flow

1. User runs `uv run agent.py "What is REST?"`
2. Agent loads `.env.agent.secret` and `.env.docker.secret`
3. Agent constructs initial messages with system prompt
4. Agent calls LLM with tool schemas
5. LLM returns tool calls (if any)
6. Agent executes tools, appends results
7. Agent calls LLM again with tool results
8. LLM returns final answer
9. Agent extracts source reference
10. Agent outputs JSON to stdout

## Error Handling

- **Missing config:** Exit code 1 with error message to stderr
- **Network errors:** Exit code 1 with error message to stderr
- **Invalid LLM response:** Exit code 1 with error message to stderr
- **Timeout (>60s per call):** Exit code 1 with timeout message to stderr
- **Max iterations (10):** Return partial answer with tool_calls log
- **Path traversal attempt:** Return error message from tool

## Output Format

All output goes to **stdout** as a single JSON line:
```json
{
  "answer": "...",
  "source": "wiki/file.md#section",
  "tool_calls": [...]
}
```

All debug/logging output goes to **stderr**.

## Security

### Path Validation

Both `read_file` and `list_files` validate paths:
- Reject paths containing `../` (directory traversal)
- Reject absolute paths starting with `/`
- Verify resolved path is within project root using `Path.resolve()`

### API Authentication

`query_api` uses `LMS_API_KEY` from `.env.docker.secret`:
- Added as `Authorization: Bearer <key>` header
- Required for accessing protected backend endpoints

## How to Run

1. Ensure `.env.agent.secret` exists with valid LLM credentials
2. Ensure `.env.docker.secret` exists with `LMS_API_KEY`
3. Run: `uv run agent.py "Your question"`

Example:
```bash
uv run agent.py "How do you resolve a merge conflict?"
```

## Testing

Run all regression tests:
```bash
uv run pytest tests/ -v
```

Tests include:
- `test_task1.py` - Basic LLM integration
- `test_task2.py` - Documentation agent (read_file, list_files)
- `test_task3.py` - System agent (query_api)

## Lessons Learned

### Challenge 1: Tool Call Format

Initially, the agent failed to make multiple tool calls because the message format was incorrect. The fix was to add the assistant message with tool_calls **before** the tool response messages, following the OpenAI function-calling format.

### Challenge 2: Windows Command-Line Arguments

Windows command-line handling of quoted arguments differs from Unix. Long questions with spaces were being truncated. Solution: Use a test script (`test_agent.py`) for reliable testing.

### Challenge 3: LLM Token Refresh

The Qwen proxy occasionally returns 401 errors when tokens expire. The proxy handles this automatically, but we need to ensure proper authentication flow.

### Challenge 4: Tool Selection

The LLM sometimes calls unnecessary tools or gets stuck in loops. The system prompt was refined to explicitly guide tool selection based on question type and to emphasize reading files after listing directories.

### Challenge 5: Iterative Debugging

The agent required multiple iterations to handle different question types correctly. Key improvements:
- Added explicit guidance for system questions to explore directories first, then read files
- Improved tool descriptions with examples
- Limited content size to avoid token limits

## Final Architecture Summary

The agent successfully implements:
- ✅ Agentic loop with iterative tool calls
- ✅ Three tools: `read_file`, `list_files`, `query_api`
- ✅ Path security to prevent directory traversal
- ✅ API authentication for backend queries
- ✅ Source reference extraction
- ✅ Structured JSON output
- ✅ Error handling and timeouts

The agent can answer:
- Documentation questions by reading wiki files
- System questions by reading source code
- Data questions by querying the backend API

## Dependencies

- `httpx` - HTTP client for API calls
- `python-dotenv` - Environment variable loading
- `uv` - Python package manager and runner
