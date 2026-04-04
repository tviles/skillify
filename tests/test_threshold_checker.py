from pathlib import Path
from unittest.mock import patch
from core.threshold_checker import (
    check_flag,
    clean_flag,
    count_tool_calls,
    check_positive_signals,
    should_analyze,
)


class TestCheckFlag:
    def test_returns_true_when_flag_exists(self, tmp_path):
        flag = tmp_path / ".skillify-active"
        flag.touch()
        with patch("core.threshold_checker.FLAG_PATH", flag):
            assert check_flag() is True

    def test_returns_false_when_no_flag(self, tmp_path):
        flag = tmp_path / ".skillify-active"
        with patch("core.threshold_checker.FLAG_PATH", flag):
            assert check_flag() is False


class TestCleanFlag:
    def test_removes_existing_flag(self, tmp_path):
        flag = tmp_path / ".skillify-active"
        flag.touch()
        with patch("core.threshold_checker.FLAG_PATH", flag):
            clean_flag()
        assert not flag.exists()

    def test_no_error_when_flag_missing(self, tmp_path):
        flag = tmp_path / ".skillify-active"
        with patch("core.threshold_checker.FLAG_PATH", flag):
            clean_flag()  # Should not raise


class TestCountToolCalls:
    def test_counts_tool_use_blocks(self):
        data = {
            "messages": [
                {
                    "role": "assistant",
                    "content": [
                        {"type": "tool_use", "name": "Read"},
                        {"type": "text", "text": "Hello"},
                        {"type": "tool_use", "name": "Edit"},
                    ],
                },
                {"role": "user", "content": "Thanks"},
                {
                    "role": "assistant",
                    "content": [{"type": "tool_use", "name": "Bash"}],
                },
            ]
        }
        assert count_tool_calls(data) == 3

    def test_returns_zero_for_no_tool_calls(self):
        data = {
            "messages": [
                {"role": "assistant", "content": [{"type": "text", "text": "Hi"}]},
                {"role": "user", "content": "Hello"},
            ]
        }
        assert count_tool_calls(data) == 0

    def test_handles_empty_messages(self):
        assert count_tool_calls({"messages": []}) == 0
        assert count_tool_calls({}) == 0


class TestCheckPositiveSignals:
    def test_detects_positive_phrases(self):
        data = {
            "messages": [
                {"role": "user", "content": "that worked perfectly"},
            ]
        }
        assert check_positive_signals(data, ["perfect"]) is True

    def test_case_insensitive(self):
        data = {
            "messages": [
                {"role": "user", "content": "THAT WORKED PERFECTLY"},
            ]
        }
        assert check_positive_signals(data, ["perfect"]) is True

    def test_returns_false_when_no_signals(self):
        data = {
            "messages": [
                {"role": "user", "content": "Fix this bug please"},
            ]
        }
        assert check_positive_signals(data, ["perfect", "great"]) is False

    def test_ignores_assistant_messages(self):
        data = {
            "messages": [
                {"role": "assistant", "content": [{"type": "text", "text": "perfect solution"}]},
            ]
        }
        assert check_positive_signals(data, ["perfect"]) is False

    def test_handles_structured_content(self):
        data = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "yes exactly what I wanted"}],
                },
            ]
        }
        assert check_positive_signals(data, ["exactly what I wanted"]) is True


class TestShouldAnalyze:
    def _make_conversation(self, tool_count, user_msg="great work"):
        tool_blocks = [{"type": "tool_use", "name": f"tool_{i}"} for i in range(tool_count)]
        return {
            "messages": [
                {"role": "assistant", "content": tool_blocks},
                {"role": "user", "content": user_msg},
            ]
        }

    def test_returns_true_when_flag_exists(self, tmp_path):
        flag = tmp_path / ".skillify-active"
        flag.touch()
        config = {"tool_count_threshold": 100, "positive_signal_patterns": []}
        with patch("core.threshold_checker.FLAG_PATH", flag):
            # Even with impossible thresholds, flag overrides
            assert should_analyze({"messages": []}, config) is True

    def test_returns_true_when_thresholds_met(self, tmp_path):
        flag = tmp_path / ".skillify-active"
        config = {"tool_count_threshold": 5, "positive_signal_patterns": ["great"]}
        with patch("core.threshold_checker.FLAG_PATH", flag):
            data = self._make_conversation(tool_count=10, user_msg="great work")
            assert should_analyze(data, config) is True

    def test_returns_false_when_tool_count_low(self, tmp_path):
        flag = tmp_path / ".skillify-active"
        config = {"tool_count_threshold": 10, "positive_signal_patterns": ["great"]}
        with patch("core.threshold_checker.FLAG_PATH", flag):
            data = self._make_conversation(tool_count=3, user_msg="great work")
            assert should_analyze(data, config) is False

    def test_returns_false_when_no_positive_signals(self, tmp_path):
        flag = tmp_path / ".skillify-active"
        config = {"tool_count_threshold": 5, "positive_signal_patterns": ["perfect"]}
        with patch("core.threshold_checker.FLAG_PATH", flag):
            data = self._make_conversation(tool_count=10, user_msg="fix this bug")
            assert should_analyze(data, config) is False
