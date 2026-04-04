"""Generate eval sets from conversation context for skill evaluation."""
import json
from pathlib import Path


def generate_eval_set(
    skill_name: str,
    skill_description: str,
    conversation_topics: list[str],
) -> dict:
    """Generate an eval set structure for testing skill trigger accuracy.

    Returns a dict in skill-creator's eval set format. The actual trigger
    queries are populated by the conversation-analyzer agent which has
    full conversation context — this function provides the format scaffold.
    """
    return {
        "skill_name": skill_name,
        "queries": [],
    }


def write_eval_set(eval_set: dict, output_path: str) -> None:
    """Write eval set to JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(eval_set, indent=2) + "\n")


def read_eval_set(filepath: str) -> dict:
    """Read eval set from JSON file."""
    return json.loads(Path(filepath).read_text())
