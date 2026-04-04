"""Parse and write YAML frontmatter from skill/command markdown files."""
import os
import re
from pathlib import Path

import yaml


def parse_frontmatter(filepath: str) -> dict:
    """Parse a markdown file with YAML frontmatter.

    Returns dict with 'metadata' (frontmatter fields) and 'body' (markdown content).
    """
    content = Path(filepath).read_text()
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", content, re.DOTALL)
    if not match:
        return {"metadata": {}, "body": content}
    frontmatter_str, body = match.groups()
    metadata = yaml.safe_load(frontmatter_str) or {}
    return {"metadata": metadata, "body": body}


def write_frontmatter(filepath: str, metadata: dict, body: str) -> None:
    """Write a markdown file with YAML frontmatter."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    frontmatter_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
    content = f"---\n{frontmatter_str}---\n{body}"
    Path(filepath).write_text(content)


def find_skillify_skills(directories: list[str]) -> list[dict]:
    """Find all skills/commands with generated_by: skillify in frontmatter.

    Scans directories for markdown files, filters by frontmatter field,
    returns sorted by modification time (most recent first).
    Ignores .backup.md files.
    """
    results = []
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            continue
        for md_file in dir_path.rglob("*.md"):
            if ".backup." in md_file.name:
                continue
            try:
                parsed = parse_frontmatter(str(md_file))
            except Exception:
                continue
            if parsed["metadata"].get("generated_by") == "skillify":
                skill_type = "skill" if "/skills/" in str(md_file) else "command"
                results.append({
                    "path": str(md_file),
                    "type": skill_type,
                    **parsed["metadata"],
                })
    results.sort(key=lambda x: os.path.getmtime(x["path"]), reverse=True)
    return results
