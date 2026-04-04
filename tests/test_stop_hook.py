import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "stop.py"
PLUGIN_ROOT = Path(__file__).parent.parent


class TestStopHook:
    def _run_hook(self, input_data: dict, env_override: dict = None) -> dict:
        """Run stop.py as a subprocess with JSON on stdin."""
        import os
        env = os.environ.copy()
        env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        env["PYTHONPATH"] = str(PLUGIN_ROOT)
        if env_override:
            env.update(env_override)
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, f"Hook must always exit 0, got {result.returncode}: {result.stderr}"
        if result.stdout.strip():
            return json.loads(result.stdout)
        return {}

    def test_exits_zero_on_empty_input(self):
        result = self._run_hook({})
        assert isinstance(result, dict)

    def test_returns_empty_when_below_threshold(self):
        data = {
            "messages": [
                {"role": "assistant", "content": [{"type": "text", "text": "Hi"}]},
                {"role": "user", "content": "Hello"},
            ]
        }
        result = self._run_hook(data)
        assert result == {} or "systemMessage" not in result

    def test_returns_system_message_when_thresholds_met(self, tmp_path):
        # Create a config with low thresholds for testing
        tool_blocks = [{"type": "tool_use", "name": f"tool_{i}"} for i in range(15)]
        data = {
            "messages": [
                {"role": "assistant", "content": tool_blocks},
                {"role": "user", "content": "perfect, that worked great"},
            ]
        }
        result = self._run_hook(data)
        assert "systemMessage" in result
        assert "skillify" in result["systemMessage"].lower()

    def test_exits_zero_on_invalid_json(self):
        """Hook must never crash — even on bad input."""
        import os
        env = os.environ.copy()
        env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        env["PYTHONPATH"] = str(PLUGIN_ROOT)
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="not json at all",
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0
