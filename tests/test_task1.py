"""Regression tests for Task 1."""

import json
import subprocess
import sys


def test_agent_outputs_valid_json():
    """Test that agent.py outputs valid JSON with required fields."""
    result = subprocess.run(
        [sys.executable, "agent.py", "What is 2 plus 2?"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, f"Agent exited with code {result.returncode}"

    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Invalid JSON: {e}")

    assert "answer" in output, "Missing 'answer' field"
    assert isinstance(output["answer"], str) and len(output["answer"]) > 0
    assert "tool_calls" in output, "Missing 'tool_calls' field"
    assert isinstance(output["tool_calls"], list)


if __name__ == "__main__":
    test_agent_outputs_valid_json()
    print("Task 1 test passed!")
