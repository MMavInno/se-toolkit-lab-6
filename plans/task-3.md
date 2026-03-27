# Task 3 Plan: The System Agent

## Overview

Extend agent from Task 2 with `query_api` tool for backend API access.

## Implementation

### Tool Schema Definition

The `query_api` tool is defined as a function-calling schema with:

- `method` (required): HTTP method (GET, POST, etc.)
- `path` (required): API endpoint path (e.g., `/items/`, `/analytics/completion-rate`)
- `body` (optional): JSON request body for POST requests

### Authentication

The tool reads `LMS_API_KEY` from `.env.docker.secret` and sends it via `Authorization: Bearer` header.

### Environment Variables

All configuration is read from environment variables:

- `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL` from `.env.agent.secret`
- `LMS_API_KEY` from `.env.docker.secret`
- `AGENT_API_BASE_URL` from `.env.docker.secret` (defaults to `http://localhost:42002`)

### System Prompt Update

The system prompt guides the LLM to choose the right tool:

- Documentation questions → `list_files("wiki/")` then `read_file()`
- System questions → `list_files()` to explore, then `read_file()` source code
- Data questions → `query_api()` for database/analytics

## Benchmark Results

Initial score: Run `uv run run_eval.py` after implementation.

Iteration strategy:

1. Run the benchmark
2. Check which questions fail
3. Read the feedback hint
4. Fix tool descriptions or system prompt
5. Re-run until all 10 questions pass

## Acceptance Criteria

- [x] Plan document exists
- [x] `query_api` tool implemented with authentication
- [x] Agent reads config from environment variables
- [x] Agent answers system and data questions
- [x] 2 regression tests pass
