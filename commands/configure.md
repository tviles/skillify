---
name: configure
description: View and modify skillify settings through an interactive AskUserQuestion wizard. Covers auto-mode, thresholds, save location, trigger patterns, and scan limits. Auto-creates the config file on first save — no manual setup required.
---

# /skillify:configure

Interactive wizard for viewing and modifying skillify configuration. Uses AskUserQuestion throughout for type-safe, discoverable menu navigation. All changes are staged in a `pending` dict and only written to disk when the user confirms at the Done step.

## How to execute this command

You will act as an interactive configurator. Follow these instructions **carefully and literally** — most steps include explicit JSON parameter blocks to pass to the AskUserQuestion tool. Substitute `{{placeholder}}` tokens with real values before invoking.

**State you must track in context as you execute:**
- `current`: the config loaded at Step 1 (immutable reference point)
- `pending`: a dict of user-made changes (starts empty, grows as user makes changes)
- `effective(key)`: helper concept — returns `pending[key]` if set, else `current[key]`
- `config_file_exists`: boolean captured at Step 1

**Placeholder substitution rule**: Before every AskUserQuestion call, replace ALL `{{var}}` tokens in the JSON with their current effective values. If a value is missing or unresolvable, fall back to "unknown" rather than leaving a literal `{{...}}` in the rendered UI.

## Step 1 — Load config

Invoke this Python snippet via the Bash tool:

```bash
python3 <<'PY'
import sys, json
from pathlib import Path
sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}")
from core.config_manager import load_config, DEFAULT_CONFIG
config_path = Path.home() / ".claude" / "skillify.config.json"
print(json.dumps({
    "current": load_config(),
    "defaults": DEFAULT_CONFIG,
    "config_file_exists": config_path.exists(),
}))
PY
```

Parse the JSON output. Initialize state:
- `current` = parsed `current` object
- `pending` = `{}` (empty dict)
- `config_file_exists` = parsed boolean

Display the loaded config to the user as a formatted table. For each setting, show the value and mark it as `default` or `overridden` by comparing against `defaults`:

```
Skillify Configuration
[If !config_file_exists: "Note: no config file yet — changes will create ~/.claude/skillify.config.json on save"]

  auto_mode:                            <value>   (<default|overridden>)
  tool_count_threshold:                 <value>   (<default|overridden>)
  positive_signal_patterns:             <N> phrases   (<default|overridden>)
  default_save_location:                <value>   (<default|overridden>)
  max_skill_scan:                       <value>   (<default|overridden>)
  description_optimization_iterations:  <value>   (<default|overridden>)
```

Then proceed to Step 2 (top menu).

## Step 2 — Top-level menu

Call AskUserQuestion with these exact parameters (substitute `{{signal_pattern_count}}` with `len(effective("positive_signal_patterns"))`):

```json
{
  "questions": [{
    "header": "Configure",
    "question": "What would you like to do?",
    "multiSelect": false,
    "options": [
      {"label": "Settings", "description": "Configure scalar settings (auto_mode, thresholds, save location, limits)"},
      {"label": "Patterns", "description": "Add/remove trigger phrases ({{signal_pattern_count}} currently)"},
      {"label": "Reset all", "description": "Restore all settings to defaults (requires confirmation)"},
      {"label": "Done", "description": "Save pending changes and exit"}
    ]
  }]
}
```

**Route based on user answer:**
- `Settings` → Step 3a (scalar settings page 1)
- `Patterns` → Step 3b (patterns sub-menu)
- `Reset all` → Step 3c (reset confirmation)
- `Done` → Step 3d (save flow)
- `Other` (custom text): try to match to the closest option; if unclear, re-show this menu

## Step 3a — Scalar settings submenu, page 1

Substitute `{{auto_mode}}`, `{{tool_count_threshold}}`, `{{default_save_location}}` with effective values:

```json
{
  "questions": [{
    "header": "Settings",
    "question": "Which setting would you like to change?",
    "multiSelect": false,
    "options": [
      {"label": "auto_mode", "description": "Toggle on/off (currently: {{auto_mode}})"},
      {"label": "tool_count", "description": "Threshold before auto mode analyzes (currently: {{tool_count_threshold}})"},
      {"label": "save_loc", "description": "Default save location (currently: {{default_save_location}})"},
      {"label": "More...", "description": "Show advanced settings (max_scan, desc_iterations)"}
    ]
  }]
}
```

**Route:**
- `auto_mode` → Step 3a-1
- `tool_count` → Step 3a-2
- `save_loc` → Step 3a-3
- `More...` → Step 3a-page2
- `Other`: re-show this menu

## Step 3a-page2 — Scalar settings submenu, page 2

Substitute `{{max_skill_scan}}`, `{{description_optimization_iterations}}` with effective values:

```json
{
  "questions": [{
    "header": "Advanced",
    "question": "Which advanced setting would you like to change?",
    "multiSelect": false,
    "options": [
      {"label": "max_scan", "description": "Max existing skills to scan for overlap (currently: {{max_skill_scan}})"},
      {"label": "desc_iters", "description": "Refinement iterations for descriptions (currently: {{description_optimization_iterations}})"},
      {"label": "Back", "description": "Return to settings page 1"}
    ]
  }]
}
```

**Route:**
- `max_scan` → Step 3a-4
- `desc_iters` → Step 3a-5
- `Back` → Step 3a (page 1)

## Step 3a-1 — auto_mode handler

```json
{
  "questions": [{
    "header": "Auto mode",
    "question": "Should skillify auto-analyze conversations at the end via the Stop hook?",
    "multiSelect": false,
    "options": [
      {"label": "Enable", "description": "Analyzer fires at conversation end when thresholds are met"},
      {"label": "Disable", "description": "Turn off auto mode; use /skillify manually only"}
    ]
  }]
}
```

On answer: `pending["auto_mode"] = (answer == "Enable")`. Return to Step 2.

## Step 3a-2 — tool_count_threshold handler

```json
{
  "questions": [{
    "header": "Threshold",
    "question": "Minimum tool calls before auto mode considers a conversation for analysis?",
    "multiSelect": false,
    "options": [
      {"label": "5", "description": "More sensitive — fires on quick sessions"},
      {"label": "10", "description": "Default — balanced"},
      {"label": "15", "description": "Less sensitive — only moderate+ sessions"},
      {"label": "25", "description": "Only deep sessions with lots of tool usage"}
    ]
  }]
}
```

On answer:
- If answer is a numeric label (`5`/`10`/`15`/`25`): `pending["tool_count_threshold"] = int(answer)`
- If `Other`: parse the custom input as an integer. Validate: integer > 0. On invalid input, tell the user the constraint and re-ask this question. On valid: store.

Return to Step 2.

## Step 3a-3 — default_save_location handler

```json
{
  "questions": [{
    "header": "Save loc",
    "question": "Where should auto-mode save generated skills by default?",
    "multiSelect": false,
    "options": [
      {"label": "global", "description": "~/.claude/skills/ and ~/.claude/commands/ (available everywhere)"},
      {"label": "project", "description": ".claude/skills/ and .claude/commands/ in current project directory"}
    ]
  }]
}
```

On answer: `pending["default_save_location"] = answer`. Return to Step 2.

## Step 3a-4 — max_skill_scan handler

```json
{
  "questions": [{
    "header": "Scan cap",
    "question": "Max existing skills to scan when checking for overlap with a new skill?",
    "multiSelect": false,
    "options": [
      {"label": "10", "description": "Fast but may miss overlaps in larger libraries"},
      {"label": "20", "description": "Default — balanced"},
      {"label": "50", "description": "Thorough — slower, best for users with many skillify skills"},
      {"label": "100", "description": "Exhaustive — noticeable delay during analysis"}
    ]
  }]
}
```

On answer:
- Numeric label: `pending["max_skill_scan"] = int(answer)`
- `Other`: parse integer, validate > 0, re-ask on invalid

Return to Step 2.

## Step 3a-5 — description_optimization_iterations handler

```json
{
  "questions": [{
    "header": "Iter count",
    "question": "How many optimization iterations should skill-creator run when refining descriptions?",
    "multiSelect": false,
    "options": [
      {"label": "1", "description": "Fastest — single pass, minimal tuning"},
      {"label": "3", "description": "Default — balanced quality vs speed"},
      {"label": "5", "description": "Thorough — better trigger precision, noticeably slower"},
      {"label": "10", "description": "Maximum — best quality, slowest"}
    ]
  }]
}
```

On answer:
- Numeric label: `pending["description_optimization_iterations"] = int(answer)`
- `Other`: parse integer, validate 1 ≤ N ≤ 10, re-ask on invalid

Return to Step 2.

## Step 3b — Patterns sub-menu

Compute `effective_patterns = effective("positive_signal_patterns")` and `pattern_count = len(effective_patterns)`. Substitute `{{pattern_count}}`:

```json
{
  "questions": [{
    "header": "Patterns",
    "question": "What would you like to do with the trigger phrase list? ({{pattern_count}} phrases currently)",
    "multiSelect": false,
    "options": [
      {"label": "Add", "description": "Add a new trigger phrase"},
      {"label": "Remove", "description": "Remove an existing phrase"},
      {"label": "Reset", "description": "Restore the default 6 phrases"},
      {"label": "Back", "description": "Return to main menu"}
    ]
  }]
}
```

**Route:**
- `Add` → Step 3b-add
- `Remove` → Step 3b-remove
- `Reset` → Set `pending["positive_signal_patterns"] = list(defaults["positive_signal_patterns"])`. Return to Step 3b (loop back to this menu).
- `Back` → Return to Step 2

## Step 3b-add — Add phrase handler

```json
{
  "questions": [{
    "header": "Add phrase",
    "question": "Which phrase should trigger skillify to flag the conversation?",
    "multiSelect": false,
    "options": [
      {"label": "ship it", "description": "Phrase: \"ship it\""},
      {"label": "nice", "description": "Phrase: \"nice\""},
      {"label": "looks good", "description": "Phrase: \"looks good\""},
      {"label": "lgtm", "description": "Phrase: \"lgtm\""}
    ]
  }]
}
```

On answer:
- If answer is a label (`ship it`/`nice`/`looks good`/`lgtm`): the new phrase is the label text
- If `Other`: the new phrase is the custom string the user typed

**Validation:**
- Reject empty strings (tell user, return to Step 3b)
- Reject duplicates of any phrase already in `effective_patterns` (case-insensitive match). Tell user "\"<phrase>\" is already in the list" and return to Step 3b.
- On valid: `pending["positive_signal_patterns"] = effective_patterns + [new_phrase]`, tell user "Added \"<phrase>\"", return to Step 3b.

## Step 3b-remove — Remove phrase handler

Get `effective_patterns`. If empty, tell user "No patterns to remove — the list is already empty." and return to Step 3b.

**Present the patterns as removable options. AskUserQuestion allows max 4 options, and we need a Back/More option, so:**

- If `len(effective_patterns) ≤ 3`: show all patterns + `Back` (total 2-4 options)
- If `len(effective_patterns) ≥ 4`: show first 3 patterns + `More...` (total 4 options). `More...` pages through the next 3 + `More...`/`Back`.

For the first page (≤3 patterns case), substitute `{{pattern_i}}` with `effective_patterns[i]`:

```json
{
  "questions": [{
    "header": "Remove",
    "question": "Which phrase should be removed?",
    "multiSelect": false,
    "options": [
      {"label": "{{pattern_0}}", "description": "Remove phrase: \"{{pattern_0}}\""},
      {"label": "{{pattern_1}}", "description": "Remove phrase: \"{{pattern_1}}\""},
      {"label": "Back", "description": "Return to patterns menu"}
    ]
  }]
}
```

(Adapt the number of pattern options based on how many exist. Minimum is 2 options total per AskUserQuestion schema, so if only 1 pattern exists, show it plus Back for a 2-option menu.)

For the paginated case (≥4 patterns), first page:

```json
{
  "questions": [{
    "header": "Remove",
    "question": "Which phrase should be removed?",
    "multiSelect": false,
    "options": [
      {"label": "{{pattern_0}}", "description": "Remove phrase: \"{{pattern_0}}\""},
      {"label": "{{pattern_1}}", "description": "Remove phrase: \"{{pattern_1}}\""},
      {"label": "{{pattern_2}}", "description": "Remove phrase: \"{{pattern_2}}\""},
      {"label": "More...", "description": "Show more phrases or go back"}
    ]
  }]
}
```

Subsequent pages follow the same shape (3 patterns + `More...` if more remain, or 3 patterns + `Back` on the last page).

**Label truncation**: if any pattern string is longer than 5 words, truncate the label to first 5 words with `...` suffix. The description still shows the full phrase.

**On answer:**
- If answer is a pattern label: `pending["positive_signal_patterns"] = [p for p in effective_patterns if p != selected]`. Tell user "Removed \"<phrase>\"". Return to Step 3b.
- If `More...`: show next page.
- If `Back`: return to Step 3b.

## Step 3c — Reset all confirmation

Build a summary of current non-default settings by comparing `effective(key)` against `defaults[key]` for each key. Display the summary to the user before the question.

Example summary format:
```
This will reset the following overridden settings:
  tool_count_threshold: 15 → 10 (default)
  positive_signal_patterns: 7 phrases → 6 (default)

And discard any pending changes not yet saved.
```

Then call AskUserQuestion:

```json
{
  "questions": [{
    "header": "Reset all",
    "question": "Restore ALL settings to defaults and discard pending changes?",
    "multiSelect": false,
    "options": [
      {"label": "Yes, reset", "description": "Replace all pending changes with DEFAULT_CONFIG values"},
      {"label": "No, back", "description": "Return to main menu without resetting"}
    ]
  }]
}
```

**On answer:**
- `Yes, reset`: `pending = dict(defaults)`. Tell user "Reset all pending changes to defaults." Return to Step 2.
- `No, back`: Return to Step 2 without changes.

## Step 3d — Done / save flow

Compute `final = {**current, **pending}` and `diff = {k: (current[k], final[k]) for k in final if current.get(k) != final.get(k)}`.

**If `diff` is empty** (no pending changes): print `No changes to save.` and exit the command entirely. Do not call AskUserQuestion.

**Otherwise**, build a human-readable diff string for the preview field. For each changed key:

- Scalar change: `<key>: <old> → <new>`
- List change (positive_signal_patterns): show additions as `+"<phrase>"` and removals as `-"<phrase>"`

Example preview content:
```
Pending changes:

  tool_count_threshold:
    10 → 15

  positive_signal_patterns:
    +"ship it"
    -"great"
```

Call AskUserQuestion with the diff in the `preview` field of the Save option (substitute `{{diff_content}}`):

```json
{
  "questions": [{
    "header": "Confirm",
    "question": "Save these changes to ~/.claude/skillify.config.json?",
    "multiSelect": false,
    "options": [
      {"label": "Save", "description": "Write merged config and exit", "preview": "{{diff_content}}"},
      {"label": "Discard", "description": "Exit without writing any changes"},
      {"label": "Back", "description": "Return to main menu to make more changes"}
    ]
  }]
}
```

**On answer:**
- `Save` → proceed to Step 4 (save execution)
- `Discard` → print `Discarded pending changes.` and exit command
- `Back` → return to Step 2

## Step 4 — Save execution

Invoke Python via the Bash tool, passing the final config as JSON via stdin:

```bash
python3 <<'PY'
import sys, json
sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}")
from core.config_manager import save_config
final = json.loads(sys.stdin.read())
save_config(final)
print(json.dumps({"saved": True}))
PY
```

(Use the Bash tool's ability to pipe input, or write the JSON to a temporary file and read it inside the Python snippet. Either approach works — use the one that's most reliable in your current context.)

On success, print to the user:

```
✓ Saved to ~/.claude/skillify.config.json

Applied changes:
  [formatted diff summary]
```

Then exit the command.

On failure (subprocess error, file write error), print the error message, tell the user their pending changes were NOT saved, and exit gracefully. Do not retry automatically — let the user re-run the command.

## Navigation invariants

- After every leaf operation (setting handler, pattern add/remove, reset), return to the menu specified in that step's "Return to" instruction
- Never skip the Step 3d confirmation — `save_config()` is only called via the Save option in that menu
- `current` is captured once at Step 1 and never reloaded during the session
- `pending` accumulates across all handlers until Step 3d writes or discards
- If the user picks `Other` on any menu and their custom text doesn't map cleanly to an expected option, re-show the menu with a brief clarification rather than guessing

## Error handling

- If Python subprocess at Step 1 fails: print the error, tell the user the config couldn't be loaded, and exit
- If any AskUserQuestion call fails: print the error and exit (don't try to resume mid-flow)
- If validation fails on a user-provided value: stay on the current question, explain the constraint, and let them try again
- If the Step 4 save fails: print the error, clarify pending changes were NOT written, exit without retry
