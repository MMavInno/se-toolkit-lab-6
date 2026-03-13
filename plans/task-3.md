# Task 3 Plan: The System Agent

## Overview

Extend the agent from Task 2 with `query_api` tool to query the backend API.

## Implementation

- `query_api` tool with LMS_API_KEY authentication
- Updated system prompt for tool selection
- Environment variables for configuration

## Benchmark

Note: run_eval.py requires API access that may not be available locally.
Testing done via direct question testing.

## Acceptance Criteria

- [x] Plan document exists
- [x] `query_api` tool implemented with authentication
- [x] Agent reads config from environment variables
- [x] Agent answers system and data questions
- [x] 2 regression tests pass
