"""Lightweight threshold checking for the Stop hook."""
import re
from pathlib import Path

FLAG_PATH = Path("/tmp/.skillify-active")


def check_flag() -> bool:
    """Check if the skillify flag file exists."""
    return FLAG_PATH.exists()


def clean_flag() -> None:
    """Remove the flag file if it exists."""
    try:
        FLAG_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def count_tool_calls(conversation_data: dict) -> int:
    """Count tool_use blocks in assistant messages."""
    count = 0
    for msg in conversation_data.get("messages", []):
        if msg.get("role") == "assistant":
            content = msg.get("content", [])
            if isinstance(content, list):
                count += sum(
                    1
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "tool_use"
                )
    return count


def check_positive_signals(conversation_data: dict, patterns: list[str]) -> bool:
    """Check if user messages contain positive validation signals."""
    for msg in conversation_data.get("messages", []):
        if msg.get("role") != "user":
            continue
        content = msg.get("content", "")
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            text = " ".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
        else:
            continue
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
    return False


def should_analyze(conversation_data: dict, config: dict) -> bool:
    """Determine if conversation is worth analyzing.

    Returns True if:
    - Flag file exists (skip threshold checks), OR
    - Tool count >= threshold AND positive signals found
    """
    if check_flag():
        return True
    tool_count = count_tool_calls(conversation_data)
    if tool_count < config.get("tool_count_threshold", 10):
        return False
    patterns = config.get("positive_signal_patterns", [])
    return check_positive_signals(conversation_data, patterns)
