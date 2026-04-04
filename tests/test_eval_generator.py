import json
from pathlib import Path
from core.eval_generator import generate_eval_set, write_eval_set, read_eval_set


class TestGenerateEvalSet:
    def test_returns_valid_structure(self):
        result = generate_eval_set(
            skill_name="react-perf",
            skill_description="Debug React performance with profiler",
            conversation_topics=["debug react", "check profiler"],
        )
        assert result["skill_name"] == "react-perf"
        assert "queries" in result
        assert isinstance(result["queries"], list)

    def test_includes_skill_name(self):
        result = generate_eval_set(
            skill_name="my-skill",
            skill_description="Does things",
            conversation_topics=[],
        )
        assert result["skill_name"] == "my-skill"


class TestWriteAndReadEvalSet:
    def test_roundtrip(self, tmp_path):
        eval_set = {
            "skill_name": "test-skill",
            "queries": [
                {"query": "debug react app", "should_trigger": True},
                {"query": "write a poem", "should_trigger": False},
            ],
        }
        filepath = str(tmp_path / "eval_set.json")
        write_eval_set(eval_set, filepath)
        loaded = read_eval_set(filepath)
        assert loaded == eval_set

    def test_creates_parent_dirs(self, tmp_path):
        filepath = str(tmp_path / "nested" / "dir" / "eval.json")
        write_eval_set({"skill_name": "test", "queries": []}, filepath)
        assert Path(filepath).exists()
