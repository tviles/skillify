---
name: help
description: Explain how skillify works, its modes, and configuration options.
---

# /skillify:help

Explain how Skillify works to the user. Output this help text verbatim:

---

## Skillify

Skillify captures successful conversation patterns as reusable skills and commands. It's the generative counterpart to hookify — where hookify prevents mistakes, skillify preserves what works.

### Two Modes

**Manual mode** (`/skillify`):
- Analyzes the current conversation for reusable patterns
- Presents a ranked menu of suggestions
- You choose which to create, where to save, and whether to refine with skill-creator

**Auto mode** (runs at conversation end via Stop hook):
- Checks if the conversation qualifies (enough tool calls + positive signals)
- If it qualifies, suggests the highest-confidence pattern for capture
- You confirm before anything is saved

### What It Looks For

1. **Repeated instructions** — things you told Claude to do multiple times
2. **Successful workflows** — complex sequences that worked without backtracking
3. **Validated approaches** — creative solutions you explicitly approved

### Commands

- `/skillify` — manually analyze this conversation
- `/skillify:list` — see all skillify-generated skills and commands
- `/skillify:configure` — adjust thresholds, toggle auto-mode, set defaults
- `/skillify:help` — this help text

### Configuration

Settings are stored in `~/.claude/skillify.config.json`. Key options:

- `auto_mode` (default: true) — enable/disable auto-mode
- `tool_count_threshold` (default: 10) — minimum tool calls to trigger analysis
- `positive_signal_patterns` — regex patterns for validation phrases
- `default_save_location` (default: global) — where auto-mode saves skills
- `max_skill_scan` (default: 20) — max existing skills to check for overlap when refining
- `description_optimization_iterations` (default: 3) — iterations for description tuning

### Provenance

All skillify-generated files include `generated_by: skillify` in their YAML frontmatter, along with `generated_date`, `source_session`, and `confidence`. Use `/skillify:list` to see them.
