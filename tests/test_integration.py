"""Integration smoke tests for the skillify plugin."""
import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent


class TestPluginStructure:
    """Verify the plugin has all required files."""

    def test_plugin_json_exists(self):
        assert (PLUGIN_ROOT / ".claude-plugin" / "plugin.json").exists()

    def test_plugin_json_valid(self):
        data = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text())
        assert data["name"] == "skillify"
        assert "description" in data

    def test_hooks_json_exists(self):
        assert (PLUGIN_ROOT / "hooks" / "hooks.json").exists()

    def test_hooks_json_registers_stop(self):
        data = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text())
        assert "Stop" in data["hooks"]

    def test_agent_definition_exists(self):
        assert (PLUGIN_ROOT / "agents" / "conversation-analyzer.md").exists()

    def test_skill_definition_exists(self):
        assert (PLUGIN_ROOT / "skills" / "skillify" / "SKILL.md").exists()

    def test_all_commands_exist(self):
        for cmd in ["skillify.md", "list.md", "configure.md", "help.md"]:
            assert (PLUGIN_ROOT / "commands" / cmd).exists(), f"Missing command: {cmd}"

    def test_all_core_modules_importable(self):
        sys.path.insert(0, str(PLUGIN_ROOT))
        from core.frontmatter_parser import parse_frontmatter, write_frontmatter, find_skillify_skills
        from core.config_manager import load_config, save_config, DEFAULT_CONFIG
        from core.threshold_checker import should_analyze, check_flag, clean_flag
        from core.eval_generator import generate_eval_set, write_eval_set, read_eval_set

    def test_templates_exist(self):
        assert (PLUGIN_ROOT / "templates" / "skill_template.md").exists()
        assert (PLUGIN_ROOT / "templates" / "command_template.md").exists()

    def test_eval_scripts_exist(self):
        for script in ["run_eval.py", "run_loop.py", "aggregate_benchmark.py", "utils.py"]:
            assert (PLUGIN_ROOT / "core" / "eval" / script).exists(), f"Missing eval script: {script}"

    def test_all_generated_files_have_valid_frontmatter(self):
        """Agent, skill, and commands must all parse with valid YAML frontmatter."""
        sys.path.insert(0, str(PLUGIN_ROOT))
        from core.frontmatter_parser import parse_frontmatter

        files = [
            PLUGIN_ROOT / "agents" / "conversation-analyzer.md",
            PLUGIN_ROOT / "skills" / "skillify" / "SKILL.md",
            PLUGIN_ROOT / "commands" / "skillify.md",
            PLUGIN_ROOT / "commands" / "list.md",
            PLUGIN_ROOT / "commands" / "configure.md",
            PLUGIN_ROOT / "commands" / "help.md",
        ]
        for f in files:
            result = parse_frontmatter(str(f))
            assert "name" in result["metadata"], f"{f.name} missing name in frontmatter"
            assert "description" in result["metadata"], f"{f.name} missing description in frontmatter"


class TestEndToEndStopHook:
    """Simulate the Stop hook flow end-to-end."""

    def _run_hook(self, input_payload):
        env = os.environ.copy()
        env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        env["PYTHONPATH"] = str(PLUGIN_ROOT)
        result = subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / "hooks" / "stop.py")],
            input=input_payload,
            capture_output=True,
            text=True,
            env=env,
        )
        return result

    def test_qualifying_conversation_triggers_analysis(self):
        """A conversation with 15 tool calls and positive signals should trigger."""
        tool_blocks = [{"type": "tool_use", "name": f"t{i}"} for i in range(15)]
        data = {
            "messages": [
                {"role": "assistant", "content": tool_blocks},
                {"role": "user", "content": "perfect, exactly what I needed"},
                {"role": "assistant", "content": [{"type": "text", "text": "Glad it worked!"}]},
            ]
        }
        result = self._run_hook(json.dumps(data))
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "systemMessage" in output
        assert "skillify" in output["systemMessage"].lower()

    def test_trivial_conversation_does_not_trigger(self):
        """A short conversation should not trigger analysis."""
        data = {
            "messages": [
                {"role": "user", "content": "What's 2+2?"},
                {"role": "assistant", "content": [{"type": "text", "text": "4"}]},
            ]
        }
        result = self._run_hook(json.dumps(data))
        assert result.returncode == 0
        output = json.loads(result.stdout) if result.stdout.strip() else {}
        assert "systemMessage" not in output

    def test_hook_never_crashes(self):
        """Hook must always exit 0 regardless of input."""
        result = self._run_hook("total garbage input {{{")
        assert result.returncode == 0
