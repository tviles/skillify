"""Manage skillify configuration."""
import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".claude" / "skillify.config.json"

DEFAULT_CONFIG = {
    "auto_mode": True,
    "tool_count_threshold": 10,
    "positive_signal_patterns": [
        "perfect",
        "that worked",
        "exactly what I wanted",
        "yes exactly",
        "great",
        "that's right",
    ],
    "default_save_location": "global",
    "max_skill_scan": 20,
    "description_optimization_iterations": 3,
}


def load_config() -> dict:
    """Load config from disk, falling back to defaults for missing keys."""
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()
    try:
        data = json.loads(CONFIG_PATH.read_text())
        merged = DEFAULT_CONFIG.copy()
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    """Save config to disk."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")


def get(key: str):
    """Get a single config value."""
    return load_config().get(key, DEFAULT_CONFIG.get(key))


def set_value(key: str, value) -> None:
    """Set a single config value and persist."""
    config = load_config()
    config[key] = value
    save_config(config)
