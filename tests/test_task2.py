"""Regression tests for Task 2: The Documentation Agent."""

import json
import subprocess
import sys


def test_agent_uses_list_files_tool():
    """Test that agent uses list_files tool for wiki listing question."""
    result = subprocess.run(
        [sys.executable, "agent.py", "What files are in wiki?"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, f"Agent exited with code {result.returncode}"
    output = json.loads(result.stdout)
    
    assert "answer" in output and "tool_calls" in output
    tool_names = [tc["tool"] for tc in output["tool_calls"]]
    assert "list_files" in tool_names, f"Expected list_files in tool_calls, got: {tool_names}"


def test_agent_uses_read_file_for_merge_conflict():
    """Test that agent uses read_file tool for merge conflict question."""
    result = subprocess.run(
        [sys.executable, "agent.py", "How do you resolve a merge conflict?"],
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


if __name__ == "__main__":
    test_agent_uses_list_files_tool()
    test_agent_uses_read_file_for_merge_conflict()
    print("Task 2 tests passed!")
