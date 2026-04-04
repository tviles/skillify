import os
import tempfile
from pathlib import Path
from core.frontmatter_parser import parse_frontmatter, write_frontmatter, find_skillify_skills


class TestParseFrontmatter:
    def test_parses_valid_frontmatter(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("---\nname: my-skill\ndescription: A test skill\n---\n# Body\nContent here\n")
        result = parse_frontmatter(str(md))
        assert result["metadata"]["name"] == "my-skill"
        assert result["metadata"]["description"] == "A test skill"
        assert "# Body" in result["body"]

    def test_returns_empty_metadata_when_no_frontmatter(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("# Just a markdown file\nNo frontmatter here.\n")
        result = parse_frontmatter(str(md))
        assert result["metadata"] == {}
        assert "# Just a markdown file" in result["body"]

    def test_handles_multiline_description(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("---\nname: my-skill\ndescription: >\n  A long\n  description\n---\nBody\n")
        result = parse_frontmatter(str(md))
        assert result["metadata"]["name"] == "my-skill"
        assert "long" in result["metadata"]["description"]

    def test_preserves_custom_frontmatter_fields(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("---\nname: test\ngenerated_by: skillify\nconfidence: high\n---\nBody\n")
        result = parse_frontmatter(str(md))
        assert result["metadata"]["generated_by"] == "skillify"
        assert result["metadata"]["confidence"] == "high"


class TestWriteFrontmatter:
    def test_writes_valid_frontmatter(self, tmp_path):
        md = tmp_path / "test.md"
        metadata = {"name": "my-skill", "description": "Test"}
        write_frontmatter(str(md), metadata, "# Body\nContent\n")
        result = parse_frontmatter(str(md))
        assert result["metadata"]["name"] == "my-skill"
        assert "# Body" in result["body"]

    def test_roundtrip_preserves_data(self, tmp_path):
        md = tmp_path / "test.md"
        metadata = {
            "name": "react-perf",
            "generated_by": "skillify",
            "generated_date": "2026-04-03",
            "confidence": "high",
        }
        body = "# React Performance\n\nDebug with profiler first.\n"
        write_frontmatter(str(md), metadata, body)
        result = parse_frontmatter(str(md))
        assert result["metadata"]["name"] == "react-perf"
        assert result["metadata"]["generated_by"] == "skillify"
        assert "Debug with profiler first" in result["body"]

    def test_creates_parent_directories(self, tmp_path):
        md = tmp_path / "nested" / "dir" / "test.md"
        write_frontmatter(str(md), {"name": "test"}, "Body\n")
        assert md.exists()


class TestFindSkillifySkills:
    def _make_skill(self, base_dir, rel_path, metadata_str, body="Content\n"):
        filepath = base_dir / rel_path
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(f"---\n{metadata_str}---\n{body}")
        return filepath

    def test_finds_skillify_generated_skills(self, tmp_path):
        self._make_skill(
            tmp_path, "skills/my-skill/SKILL.md",
            "name: my-skill\ngenerated_by: skillify\nconfidence: high\n",
        )
        results = find_skillify_skills([str(tmp_path)])
        assert len(results) == 1
        assert results[0]["name"] == "my-skill"
        assert results[0]["type"] == "skill"

    def test_finds_skillify_generated_commands(self, tmp_path):
        self._make_skill(
            tmp_path, "commands/my-cmd.md",
            "name: my-cmd\ngenerated_by: skillify\nconfidence: medium\n",
        )
        results = find_skillify_skills([str(tmp_path)])
        assert len(results) == 1
        assert results[0]["name"] == "my-cmd"
        assert results[0]["type"] == "command"

    def test_ignores_non_skillify_skills(self, tmp_path):
        self._make_skill(
            tmp_path, "skills/manual/SKILL.md",
            "name: manual-skill\ndescription: Hand-written\n",
        )
        results = find_skillify_skills([str(tmp_path)])
        assert len(results) == 0

    def test_ignores_backup_files(self, tmp_path):
        self._make_skill(
            tmp_path, "skills/my-skill/SKILL.backup.md",
            "name: my-skill\ngenerated_by: skillify\n",
        )
        results = find_skillify_skills([str(tmp_path)])
        assert len(results) == 0

    def test_handles_nonexistent_directories(self):
        results = find_skillify_skills(["/nonexistent/path"])
        assert results == []

    def test_sorted_by_modification_time(self, tmp_path):
        p1 = self._make_skill(
            tmp_path, "skills/old/SKILL.md",
            "name: old-skill\ngenerated_by: skillify\n",
        )
        import time
        time.sleep(0.05)
        p2 = self._make_skill(
            tmp_path, "skills/new/SKILL.md",
            "name: new-skill\ngenerated_by: skillify\n",
        )
        results = find_skillify_skills([str(tmp_path)])
        assert results[0]["name"] == "new-skill"
        assert results[1]["name"] == "old-skill"
