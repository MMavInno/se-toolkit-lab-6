#!/usr/bin/env python3
"""
Agent CLI - Calls an LLM with tools to answer questions.

Usage:
    uv run agent.py "Your question here"

Output:
    JSON to stdout: {"answer": "...", "source": "...", "tool_calls": [...]}
    Debug output to stderr.
"""

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv


# Project root directory (where agent.py is located)
PROJECT_ROOT = Path(__file__).parent.resolve()


def load_config() -> dict:
    """Load configuration from environment files."""
    # Load LLM config
    env_file = PROJECT_ROOT / ".env.agent.secret"
    if not env_file.exists():
        print(f"Error: {env_file} not found", file=sys.stderr)
        sys.exit(1)
    load_dotenv(env_file)

    # Load LMS API key for query_api
    lms_env_file = PROJECT_ROOT / ".env.docker.secret"
    if lms_env_file.exists():
        load_dotenv(lms_env_file, override=False)

    config = {
        "api_key": os.getenv("LLM_API_KEY"),
        "api_base": os.getenv("LLM_API_BASE"),
        "model": os.getenv("LLM_MODEL"),
        "lms_api_key": os.getenv("LMS_API_KEY", ""),
        "agent_api_base_url": os.getenv("AGENT_API_BASE_URL", "http://localhost:42002"),
    }

    missing = [k for k, v in config.items() if not v and k in ["api_key", "api_base", "model"]]
    if missing:
        print(f"Error: Missing config: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    return config


def validate_path(path: str) -> tuple[bool, str]:
    """
    Validate that a path is safe to access (no directory traversal).
    Returns (is_valid, error_message).
    """
    if not path:
        return False, "Empty path"
    
    # Check for directory traversal
    if ".." in path:
        return False, "Directory traversal not allowed"
    
    # Check for absolute paths
    if path.startswith("/"):
        return False, "Absolute paths not allowed"
    
    # Resolve the full path and ensure it's within project root
    try:
        full_path = (PROJECT_ROOT / path).resolve()
        if not str(full_path).startswith(str(PROJECT_ROOT)):
            return False, "Path outside project root"
    except Exception as e:
        return False, f"Invalid path: {e}"
    
    return True, ""


def read_file_tool(path: str) -> str:
    """
    Read the contents of a file from the project repository.
    
    Args:
        path: Relative path from project root (e.g., wiki/git-workflow.md)
    
    Returns:
        File contents as string, or error message.
    """
    is_valid, error = validate_path(path)
    if not is_valid:
        return f"Error: {error}"
    
    file_path = PROJECT_ROOT / path
    
    if not file_path.exists():
        return f"Error: File not found: {path}"
    
    if not file_path.is_file():
        return f"Error: Not a file: {path}"
    
    try:
        content = file_path.read_text(encoding="utf-8")
        # Limit content size to avoid token limits
        max_chars = 10000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n... [content truncated]"
        return content
    except Exception as e:
        return f"Error reading file: {e}"


def list_files_tool(path: str) -> str:
    """
    List files and directories at a given path.
    
    Args:
        path: Relative directory path from project root (e.g., wiki/)
    
    Returns:
        Newline-separated list of entries, or error message.
    """
    is_valid, error = validate_path(path)
    if not is_valid:
        return f"Error: {error}"
    
    dir_path = PROJECT_ROOT / path
    
    if not dir_path.exists():
        return f"Error: Directory not found: {path}"
    
    if not dir_path.is_dir():
        return f"Error: Not a directory: {path}"
    
    try:
        entries = []
        for entry in sorted(dir_path.iterdir()):
            # Skip hidden files and common ignored directories
            if entry.name.startswith(".") and entry.name not in [".qwen"]:
                continue
            if entry.name in ["__pycache__", ".venv", ".git", "node_modules"]:
                continue
            
            suffix = "/" if entry.is_dir() else ""
            entries.append(f"{entry.name}{suffix}")
        
        return "\n".join(entries)
    except Exception as e:
        return f"Error listing directory: {e}"


def query_api_tool(method: str, path: str, body: str = None) -> str:
    """
    Call the backend API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: API path (e.g., /items/)
        body: Optional JSON request body
    
    Returns:
        JSON string with status_code and body.
    """
    base_url = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002")
    lms_api_key = os.getenv("LMS_API_KEY", "")
    
    url = f"{base_url}{path}"
    headers = {
        "Content-Type": "application/json",
    }
    
    if lms_api_key:
        headers["Authorization"] = f"Bearer {lms_api_key}"
    
    try:
        if method.upper() == "GET":
            response = httpx.get(url, headers=headers, timeout=30.0)
        elif method.upper() == "POST":
            response = httpx.post(url, headers=headers, json=json.loads(body) if body else {}, timeout=30.0)
        else:
            return f"Error: Unsupported method: {method}"
        
        result = {
            "status_code": response.status_code,
            "body": response.text,
        }
        return json.dumps(result)
    except httpx.TimeoutException:
        return json.dumps({"status_code": 0, "body": "Error: Request timed out"})
    except httpx.RequestError as e:
        return json.dumps({"status_code": 0, "body": f"Error: {str(e)}"})
    except json.JSONDecodeError as e:
        return json.dumps({"status_code": 0, "body": f"Error: Invalid JSON body: {e}"})


# Tool definitions for LLM function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the project repository. Use this to read documentation files in wiki/ or source code files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root (e.g., 'wiki/git-workflow.md' or 'backend/main.py')",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path. Use this to discover what files exist in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root (e.g., 'wiki/' or 'backend/')",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Call the backend API to query data or check system status. Use this for questions about database content, analytics, or system state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, etc.)",
                    },
                    "path": {
                        "type": "string",
                        "description": "API endpoint path (e.g., '/items/', '/analytics/completion-rate')",
                    },
                    "body": {
                        "type": "string",
                        "description": "Optional JSON request body for POST requests",
                    },
                },
                "required": ["method", "path"],
            },
        },
    },
]

# Tool name to function mapping
TOOL_FUNCTIONS = {
    "read_file": read_file_tool,
    "list_files": list_files_tool,
    "query_api": query_api_tool,
}


SYSTEM_PROMPT = """You are a helpful assistant that answers questions about a software project.

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

When you find the answer, provide it with the source reference.
"""


def call_llm(messages: list, config: dict, tools: list = None) -> dict:
    """Call the LLM API and return the response."""
    url = f"{config['api_base']}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config["model"],
        "messages": messages,
    }
    
    if tools:
        payload["tools"] = tools

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
    except httpx.TimeoutException:
        print("Error: LLM request timed out", file=sys.stderr)
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"Error: Failed to connect to LLM: {e}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def execute_tool_call(tool_call: dict) -> str:
    """Execute a single tool call and return the result."""
    function = tool_call.get("function", {})
    name = function.get("name")
    args_str = function.get("arguments", "{}")
    
    try:
        args = json.loads(args_str)
    except json.JSONDecodeError:
        return f"Error: Invalid arguments JSON: {args_str}"
    
    if name not in TOOL_FUNCTIONS:
        return f"Error: Unknown tool: {name}"
    
    func = TOOL_FUNCTIONS[name]
    print(f"  Calling {name}({args})...", file=sys.stderr)
    
    try:
        result = func(**args)
        return result
    except Exception as e:
        return f"Error executing {name}: {e}"


def run_agentic_loop(question: str, config: dict) -> tuple[str, str, list]:
    """
    Run the agentic loop to answer a question.
    
    Returns:
        (answer, source, tool_calls_log)
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    
    tool_calls_log = []
    max_iterations = 10
    
    for iteration in range(max_iterations):
        print(f"\n[Iteration {iteration + 1}/{max_iterations}]", file=sys.stderr)
        
        # Call LLM
        response_data = call_llm(messages, config, tools=TOOLS)
        
        # Get the assistant message
        choice = response_data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        # Check for tool calls
        tool_calls = message.get("tool_calls")
        
        if tool_calls:
            # Add assistant message with tool calls first
            messages.append(message)
            
            # Execute each tool call
            for tool_call in tool_calls:
                result = execute_tool_call(tool_call)
                
                # Log the tool call
                function = tool_call.get("function", {})
                tool_calls_log.append({
                    "tool": function.get("name"),
                    "args": json.loads(function.get("arguments", "{}")),
                    "result": result,
                })
                
                # Add tool response to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id"),
                    "content": result,
                })
            
        else:
            # No tool calls - LLM provided final answer
            answer = message.get("content") or ""
            
            # Try to extract source from answer
            source = extract_source(answer)
            
            return answer, source, tool_calls_log
    
    # Max iterations reached
    print("Warning: Max iterations reached", file=sys.stderr)
    answer = "I was unable to find a complete answer within the tool call limit."
    return answer, "", tool_calls_log


def extract_source(answer: str) -> str:
    """
    Try to extract a source reference from the answer.
    Looks for patterns like wiki/file.md, backend/file.py, etc.
    """
    import re
    
    # Look for markdown file references
    patterns = [
        r'(wiki/[\w-]+\.md(?:#[\w-]+)?)',
        r'(backend/[\w/]+\.py)',
        r'(frontend/[\w/]+\.(?:ts|tsx|js|jsx))',
        r'(/[\w/-]+)',  # API endpoints
    ]
    
    for pattern in patterns:
        match = re.search(pattern, answer)
        if match:
            return match.group(1)
    
    return ""


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run agent.py \"<question>\"", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]
    config = load_config()

    print(f"Question: {question}", file=sys.stderr)

    answer, source, tool_calls = run_agentic_loop(question, config)

    result = {
        "answer": answer,
        "source": source,
        "tool_calls": tool_calls,
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
