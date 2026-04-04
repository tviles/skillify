import json
from pathlib import Path
from unittest.mock import patch
from core.config_manager import (
    load_config,
    save_config,
    get,
    set_value,
    DEFAULT_CONFIG,
    CONFIG_PATH,
)


class TestLoadConfig:
    def test_returns_defaults_when_no_file(self, tmp_path):
        fake_path = tmp_path / "nonexistent.json"
        with patch("core.config_manager.CONFIG_PATH", fake_path):
            config = load_config()
        assert config == DEFAULT_CONFIG

    def test_loads_from_file(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"auto_mode": False, "tool_count_threshold": 20}))
        with patch("core.config_manager.CONFIG_PATH", config_file):
            config = load_config()
        assert config["auto_mode"] is False
        assert config["tool_count_threshold"] == 20

    def test_merges_with_defaults_for_missing_keys(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"auto_mode": False}))
        with patch("core.config_manager.CONFIG_PATH", config_file):
            config = load_config()
        assert config["auto_mode"] is False
        assert config["tool_count_threshold"] == DEFAULT_CONFIG["tool_count_threshold"]
        assert config["max_skill_scan"] == DEFAULT_CONFIG["max_skill_scan"]

    def test_returns_defaults_on_corrupt_json(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text("not valid json{{{")
        with patch("core.config_manager.CONFIG_PATH", config_file):
            config = load_config()
        assert config == DEFAULT_CONFIG


class TestSaveConfig:
    def test_saves_to_file(self, tmp_path):
        config_file = tmp_path / "config.json"
        with patch("core.config_manager.CONFIG_PATH", config_file):
            save_config({"auto_mode": False, "tool_count_threshold": 5})
        data = json.loads(config_file.read_text())
        assert data["auto_mode"] is False
        assert data["tool_count_threshold"] == 5

    def test_creates_parent_directories(self, tmp_path):
        config_file = tmp_path / "nested" / "dir" / "config.json"
        with patch("core.config_manager.CONFIG_PATH", config_file):
            save_config(DEFAULT_CONFIG)
        assert config_file.exists()


class TestGetAndSet:
    def test_get_returns_value(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"auto_mode": False}))
        with patch("core.config_manager.CONFIG_PATH", config_file):
            assert get("auto_mode") is False

    def test_get_returns_default_for_missing_key(self, tmp_path):
        config_file = tmp_path / "nonexistent.json"
        with patch("core.config_manager.CONFIG_PATH", config_file):
            assert get("tool_count_threshold") == 10

    def test_set_value_persists(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(DEFAULT_CONFIG))
        with patch("core.config_manager.CONFIG_PATH", config_file):
            set_value("auto_mode", False)
            assert get("auto_mode") is False
