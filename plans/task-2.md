# Task 2 Plan: The Documentation Agent

## Overview

Extend the agent from Task 1 with tools (`read_file`, `list_files`) and an agentic loop. The agent will answer questions by reading documentation from the `wiki/` directory.

## Implementation

- Tool schemas registered with LLM
- Agentic loop with max 10 iterations
- Path security to prevent directory traversal
- Source extraction from answers

## Acceptance Criteria

- [x] Plan document exists
- [x] `read_file` and `list_files` tools implemented
- [x] Agentic loop executes tool calls
- [x] `tool_calls` field populated in output
- [x] `source` field identifies wiki section
- [x] Path security prevents traversal
- [x] 2 regression tests pass
