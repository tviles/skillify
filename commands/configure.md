---
name: configure
description: View and modify skillify settings through a tabbed multi-question form. Covers auto-mode, thresholds, save location, trigger patterns, and scan limits. Batches related questions into single AskUserQuestion calls so the user fills out the whole config in 2-3 round trips instead of navigating a step-by-step menu.
---

# /skillify:configure

Interactive tabbed wizard for viewing and modifying skillify configuration.

Uses AskUserQuestion's multi-question pattern: each call presents multiple related questions as **tabs at the top of the UI**. The user navigates between tabs freely, fills in whatever they want to change, and submits once per call. Most configs need only 2 calls total (core form + save confirmation).

## Execution model

You will:
1. Load config once (Step 1)
2. Present the **core settings form** as 4 tabs in a single AskUserQuestion call (Step 2)
3. Conditionally present the **advanced settings form** as 4 tabs in a second call (Step 3)
4. Handle any pattern add/remove sub-flows that were triggered (Steps 3a/3b)
5. Present the **save confirmation** with a diff preview (Step 4)
6. Execute the save if confirmed (Step 5)

**State you track in your context as you execute:**
- `current`: the config loaded at Step 1 (never mutated — reference point for diffs)
- `pending`: dict of user-made changes (starts empty, accumulates after each form submission; keys only set when user picks something OTHER than "Keep")
- `effective(key)`: helper concept — returns `pending[key]` if set, else `current[key]`

**Placeholder substitution rule**: Before every AskUserQuestion call, replace ALL `{{variable}}` tokens in the JSON with their effective values (pending if modified, else current). Never leave literal `{{...}}` tokens in the rendered UI — that's a bug.

**Answer parsing convention**: AskUserQuestion returns an `answers` dict keyed by question index as strings: `answers["0"]`, `answers["1"]`, etc. This is documented in plugin-dev's plugin-settings examples.

## Step 1 — Load config

Invoke via Bash:

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

Parse the JSON output. Initialize:
- `current` = parsed `current` object
- `defaults` = parsed `defaults` object
- `pending` = `{}` (empty dict)
- `config_file_exists` = parsed boolean

Display a brief status line to the user:
```
Skillify config — auto_mode={{auto_mode}}, threshold={{tool_count_threshold}}, save_loc={{default_save_location}}, patterns={{signal_pattern_count}} phrases[, file does not exist yet]
```
(Append `, file does not exist yet` only if `!config_file_exists`.)

Then proceed immediately to Step 2 — do NOT ask any intermediate questions before the form.

## Step 2 — Core settings form (4 tabs, 1 submit)

This is the main interaction — most users will complete their entire config session here.

Call AskUserQuestion with these exact parameters. Substitute `{{auto_mode}}`, `{{tool_count_threshold}}`, `{{default_save_location}}` with current effective values before invoking:

```json
{
  "questions": [
    {
      "header": "Auto mode",
      "question": "Should skillify auto-analyze conversations at the end via the Stop hook?",
      "multiSelect": false,
      "options": [
        {"label": "Keep ({{auto_mode}}) (Recommended)", "description": "Leave auto_mode unchanged"},
        {"label": "Enable", "description": "Analyzer fires at conversation end when thresholds are met"},
        {"label": "Disable", "description": "Turn off auto mode; use /skillify manually only"}
      ]
    },
    {
      "header": "Threshold",
      "question": "Minimum tool calls before auto mode considers a conversation for analysis?",
      "multiSelect": false,
      "options": [
        {"label": "Keep ({{tool_count_threshold}}) (Recommended)", "description": "Leave threshold unchanged"},
        {"label": "5", "description": "More sensitive — fires on quick sessions"},
        {"label": "15", "description": "Less sensitive — moderate+ sessions only"},
        {"label": "25", "description": "Only deep sessions with lots of tool usage"}
      ]
    },
    {
      "header": "Save loc",
      "question": "Default save location for skillify-generated skills and commands?",
      "multiSelect": false,
      "options": [
        {"label": "Keep ({{default_save_location}}) (Recommended)", "description": "Leave save location unchanged"},
        {"label": "global", "description": "~/.claude/skills/ and ~/.claude/commands/ — available everywhere"},
        {"label": "project", "description": ".claude/skills/ and .claude/commands/ — current project only"}
      ]
    },
    {
      "header": "More?",
      "question": "Edit advanced settings (scan cap, iteration count, patterns, reset all)?",
      "multiSelect": false,
      "options": [
        {"label": "No, go to save (Recommended)", "description": "Skip advanced settings and proceed to save confirmation"},
        {"label": "Yes, show advanced", "description": "Open the advanced settings form"}
      ]
    }
  ]
}
```

**Parse `answers` by index:**

| Index | Setting | Processing rule |
|---|---|---|
| `answers["0"]` | auto_mode | Starts with `"Keep"` → no change. `"Enable"` → `pending["auto_mode"] = True`. `"Disable"` → `pending["auto_mode"] = False`. |
| `answers["1"]` | tool_count_threshold | Starts with `"Keep"` → no change. Numeric label (`"5"`/`"15"`/`"25"`) → `pending["tool_count_threshold"] = int(label)`. If user typed a custom value via "Other" → parse as int, validate `> 0`, store in pending. |
| `answers["2"]` | default_save_location | Starts with `"Keep"` → no change. `"global"` or `"project"` → store in pending. |
| `answers["3"]` | routing | `"No, go to save"` → jump to Step 4. `"Yes, show advanced"` → proceed to Step 3. |

**Validation failures** (e.g., Other value is not a positive integer): tell the user the constraint, leave pending unchanged for that key, and still proceed based on `answers["3"]` — don't re-prompt Step 2, that would defeat the "one submit" UX.

## Step 3 — Advanced settings form (4 tabs, 1 submit) — conditional

Only execute this step if `answers["3"]` from Step 2 was `"Yes, show advanced"`.

Substitute `{{max_skill_scan}}`, `{{description_optimization_iterations}}`, `{{signal_pattern_count}}` with current effective values (pending if set, else current):

```json
{
  "questions": [
    {
      "header": "Scan cap",
      "question": "Max existing skills to scan when checking for overlap with a new skill?",
      "multiSelect": false,
      "options": [
        {"label": "Keep ({{max_skill_scan}}) (Recommended)", "description": "Leave scan cap unchanged"},
        {"label": "10", "description": "Fast — may miss overlaps in larger libraries"},
        {"label": "50", "description": "Thorough — slower, best for users with many skillify skills"},
        {"label": "100", "description": "Exhaustive — noticeable delay during analysis"}
      ]
    },
    {
      "header": "Iter count",
      "question": "Optimization iterations for description refinement during skill-creator runs?",
      "multiSelect": false,
      "options": [
        {"label": "Keep ({{description_optimization_iterations}}) (Recommended)", "description": "Leave iteration count unchanged"},
        {"label": "1", "description": "Fastest — single pass, minimal tuning"},
        {"label": "5", "description": "Thorough — better trigger precision, noticeably slower"},
        {"label": "10", "description": "Maximum — best quality, slowest"}
      ]
    },
    {
      "header": "Patterns",
      "question": "What should happen with the trigger phrase list? (currently {{signal_pattern_count}} phrases)",
      "multiSelect": false,
      "options": [
        {"label": "Keep as-is (Recommended)", "description": "No change to the phrase list"},
        {"label": "Add a phrase", "description": "Open the add-phrase dialog after submission"},
        {"label": "Remove a phrase", "description": "Open the remove-phrase dialog after submission"},
        {"label": "Reset to defaults", "description": "Restore the default 6 phrases from DEFAULT_CONFIG"}
      ]
    },
    {
      "header": "Reset all",
      "question": "Reset ALL settings to defaults? (If Yes, this overrides every other change you made in both forms)",
      "multiSelect": false,
      "options": [
        {"label": "No, keep my changes (Recommended)", "description": "Apply the changes I made in both forms"},
        {"label": "Yes, reset everything", "description": "Wipe pending and replace with DEFAULT_CONFIG"}
      ]
    }
  ]
}
```

**Parse `answers` by index:**

| Index | Setting | Processing rule |
|---|---|---|
| `answers["0"]` | max_skill_scan | `"Keep"` → no change. Numeric label or Other → `pending["max_skill_scan"] = int(value)`, validate `> 0`. |
| `answers["1"]` | description_optimization_iterations | `"Keep"` → no change. Numeric label or Other → `pending["description_optimization_iterations"] = int(value)`, validate `1 ≤ N ≤ 10`. |
| `answers["2"]` | patterns_action | `"Keep as-is"` → no action. `"Add a phrase"` → run Step 3a after this. `"Remove a phrase"` → run Step 3b after this. `"Reset to defaults"` → `pending["positive_signal_patterns"] = list(defaults["positive_signal_patterns"])`. |
| `answers["3"]` | reset_all | `"No, keep my changes"` → no action. `"Yes, reset everything"` → **replace** `pending` with `dict(defaults)`, discarding all prior changes. The reset takes precedence over everything else in the form. |

**Order of operations (important)**:
1. Process answers 0-2 first to build up pending
2. Then process answer 3 — if it's "Yes, reset", REPLACE pending with defaults (wiping the changes from 0-2 in this form AND the core form from Step 2)
3. Finally, if `answers["2"]` was Add or Remove AND reset was NOT triggered, run Step 3a or 3b
4. If reset WAS triggered, skip Step 3a/3b (no patterns editing needed — pending is already defaults)
5. Proceed to Step 4

## Step 3a — Add phrase sub-flow

Only run if `answers["2"]` in Step 3 was `"Add a phrase"` AND reset was NOT triggered.

Single focused AskUserQuestion:

```json
{
  "questions": [
    {
      "header": "Add phrase",
      "question": "Which phrase should trigger skillify to flag the conversation? (Pick a suggestion or use Other for a custom phrase.)",
      "multiSelect": false,
      "options": [
        {"label": "ship it", "description": "Phrase: \"ship it\""},
        {"label": "nice", "description": "Phrase: \"nice\""},
        {"label": "looks good", "description": "Phrase: \"looks good\""},
        {"label": "lgtm", "description": "Phrase: \"lgtm\""}
      ]
    }
  ]
}
```

Parse `answers["0"]`. The new phrase is either the label text (if user picked a suggestion) or the custom string (if user picked Other).

**Validation:**
- Empty string → reject, tell user, skip the addition, proceed to Step 4
- Duplicate (case-insensitive match against `effective("positive_signal_patterns")`) → reject with message "Phrase already in list", proceed to Step 4
- Valid → compute `effective_patterns = effective("positive_signal_patterns")`, then `pending["positive_signal_patterns"] = effective_patterns + [new_phrase]`, tell user "Added: \"<phrase>\""

Proceed to Step 4.

## Step 3b — Remove phrase sub-flow

Only run if `answers["2"]` in Step 3 was `"Remove a phrase"` AND reset was NOT triggered.

Compute `effective_patterns = effective("positive_signal_patterns")`.

**If `len(effective_patterns) == 0`**: tell user "No patterns to remove — the list is already empty." Proceed to Step 4.

**If `len(effective_patterns) <= 4`**: show all patterns as options in a single call. Must have at least 2 options per schema — if only 1 pattern, include a second "Cancel" option:

```json
{
  "questions": [
    {
      "header": "Remove",
      "question": "Which phrase should be removed from the trigger list?",
      "multiSelect": false,
      "options": [
        {"label": "{{pattern_0}}", "description": "Remove: \"{{pattern_0}}\""},
        {"label": "{{pattern_1}}", "description": "Remove: \"{{pattern_1}}\""}
      ]
    }
  ]
}
```

Include as many pattern options as there are patterns (2-4 options).

**If `len(effective_patterns) > 4`**: show first 3 patterns + `"More..."` as 4th option:

```json
{
  "questions": [
    {
      "header": "Remove",
      "question": "Which phrase should be removed? (Showing 1-3 of {{signal_pattern_count}})",
      "multiSelect": false,
      "options": [
        {"label": "{{pattern_0}}", "description": "Remove: \"{{pattern_0}}\""},
        {"label": "{{pattern_1}}", "description": "Remove: \"{{pattern_1}}\""},
        {"label": "{{pattern_2}}", "description": "Remove: \"{{pattern_2}}\""},
        {"label": "More...", "description": "Show next batch of patterns"}
      ]
    }
  ]
}
```

If user picks `"More..."`, recursively show the next batch of up to 3 patterns + More...-or-Back. Track the current offset in your context.

**Label handling**: if a phrase is longer than 5 words or 40 characters, truncate the label (use first few words + `...`) but keep the full phrase in the description. When matching the user's answer back to a pattern, match against the full description text or maintain an index → pattern map.

**On answer** (a pattern was selected):
`pending["positive_signal_patterns"] = [p for p in effective_patterns if p != selected_phrase]`

Tell user "Removed: \"<phrase>\"". Proceed to Step 4.

## Step 4 — Save confirmation (1 question with diff preview)

Compute:
- `final_config = {**current, **pending}`
- `diff` = dict of `{key: (current[key], final_config[key])}` for keys where values differ

**If `diff` is empty** (no pending changes): print `No changes to save.` and exit the command entirely. Do NOT call AskUserQuestion.

**Otherwise**, build a human-readable diff string for the preview field. Format:
```
Pending changes:

  <key1>:
    <old> → <new>

  positive_signal_patterns:
    +"<added phrase>"
    -"<removed phrase>"
```

For scalar changes, show `<key>: <old> → <new>`. For `positive_signal_patterns`, compute set diff and show additions with `+` and removals with `-`.

Call AskUserQuestion with the diff in the `preview` field:

```json
{
  "questions": [
    {
      "header": "Confirm",
      "question": "Save these changes to ~/.claude/skillify.config.json?",
      "multiSelect": false,
      "options": [
        {"label": "Save (Recommended)", "description": "Write merged config to disk and exit", "preview": "{{diff_content}}"},
        {"label": "Discard", "description": "Exit without writing any changes"}
      ]
    }
  ]
}
```

Substitute `{{diff_content}}` with the actual generated diff string before invoking.

Parse `answers["0"]`:
- `"Save"` → proceed to Step 5
- `"Discard"` → print `Discarded pending changes.` and exit the command

## Step 5 — Save execution

Pass the final config as JSON to a Python subprocess that calls `save_config`. Write to a temp file and read it from Python to avoid shell quoting issues with large JSON:

```bash
TMP=$(mktemp)
cat > "$TMP" <<'JSON'
{{final_config_json}}
JSON
python3 <<PY
import sys, json
sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}")
from core.config_manager import save_config
with open("$TMP") as f:
    final = json.load(f)
save_config(final)
print(json.dumps({"saved": True}))
PY
rm -f "$TMP"
```

Substitute `{{final_config_json}}` with the actual final_config as pretty JSON before running.

**On success**, print to the user:
```
✓ Saved to ~/.claude/skillify.config.json

Applied changes:
  [formatted diff summary — same content as the preview field]
```

**On failure** (subprocess error, file write error, JSON parse error): print the error, clarify that pending changes were NOT written to disk, exit without retry. Do not attempt to recover automatically — let the user re-run the command.

## Navigation flow summary

| Scenario | Path | AskUserQuestion calls |
|---|---|---|
| No changes | Step 1 → Step 2 → `No changes to save.` | **1** (Step 2 only, then early exit at Step 4) |
| Simple change (1-3 core settings) | Step 1 → Step 2 → Step 4 → Step 5 | **2** |
| Advanced change | Step 1 → Step 2 → Step 3 → Step 4 → Step 5 | **3** |
| Pattern add | Step 1 → Step 2 → Step 3 → Step 3a → Step 4 → Step 5 | **4** |
| Pattern remove (≤4 patterns) | Step 1 → Step 2 → Step 3 → Step 3b → Step 4 → Step 5 | **4** |
| Pattern remove (>4 patterns, paginated) | Step 1 → Step 2 → Step 3 → Step 3b (×N) → Step 4 → Step 5 | **4 + pagination** |
| Reset all | Step 1 → Step 2 → Step 3 (reset=Yes) → Step 4 → Step 5 | **3** |

Typical user session: **2 calls**. Compare to v0.1.2 which required 10-12 calls for the same work.

## Important conventions

**Keep-option labels**: Every settable question has `"Keep (<current_value>) (Recommended)"` as its first option. The `(Recommended)` suffix follows Anthropic's documented pattern for AskUserQuestion — placing the recommended option first and marking it guides users toward the default path (which for our case is "don't change this").

**Placeholder format**: Use `{{key_name}}` tokens in the JSON templates. Replace them with effective values at runtime before invoking AskUserQuestion. Examples:
- `{{auto_mode}}` → `True` or `False`
- `{{tool_count_threshold}}` → integer as string
- `{{default_save_location}}` → `"global"` or `"project"`
- `{{signal_pattern_count}}` → integer as string (length of effective patterns list)
- `{{pattern_0}}`, `{{pattern_1}}`, etc. → the actual phrase strings from effective_patterns

**Answer index parsing**: Always use string-keyed numeric indices: `answers["0"]`, `answers["1"]`, etc. Match to the position of the question in the `questions` array.

**Reset-all precedence**: If the user picks `"Yes, reset everything"` in the advanced form's reset tab, wipe pending and replace with defaults BEFORE processing any pattern add/remove. This means the user's patterns sub-flow selection is ignored — they can re-run the command if they want to make changes after a reset.

## Error handling

- **Step 1 Python failure**: print the error, tell user the config couldn't be loaded, exit. Do not proceed to the form.
- **AskUserQuestion malformed or errored**: print the error, exit. Do not try to resume mid-flow.
- **Invalid Other value on numeric inputs**: tell user the constraint (e.g., "tool_count_threshold must be a positive integer"), leave the setting unchanged, and continue. Don't re-prompt — this preserves the one-submit UX even when a single tab has a bad value.
- **Step 5 save failure**: print the error, clarify pending changes were NOT written, exit. User can re-run the command.
