"""Regression tests for Task 3: The System Agent."""

import json
import subprocess
import sys


def test_agent_uses_read_file_for_framework_question():
    """Test that agent uses read_file for system framework question."""
    result = subprocess.run(
        [sys.executable, "agent.py", "What Python web framework does the backend use?"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, f"Agent exited with code {result.returncode}"
    output = json.loads(result.stdout)
    
    assert "answer" in output and "tool_calls" in output
    assert len(output["tool_calls"]) > 0, "Expected at least one tool call"
    tool_names = [tc["tool"] for tc in output["tool_calls"]]
    assert "read_file" in tool_names, f"Expected read_file in tool_calls, got: {tool_names}"
    
    answer_lower = output["answer"].lower()
    assert any(fw in answer_lower for fw in ["fastapi", "flask", "django"]), \
        f"Answer should mention a framework: {output['answer'][:100]}"


def test_agent_uses_query_api_for_data_question():
    """Test that agent uses query_api for database item count question."""
    result = subprocess.run(
        [sys.executable, "agent.py", "How many items are in the database?"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, f"Agent exited with code {result.returncode}"
    output = json.loads(result.stdout)
    
    assert "answer" in output and "tool_calls" in output
    tool_names = [tc["tool"] for tc in output["tool_calls"]]
    assert "query_api" in tool_names, f"Expected query_api in tool_calls, got: {tool_names}"


if __name__ == "__main__":
    test_agent_uses_read_file_for_framework_question()
    test_agent_uses_query_api_for_data_question()
    print("Task 3 tests passed!")
