---
name: configure
description: View and modify skillify settings (auto-mode, thresholds, save location, etc).
---

# /skillify:configure

View and interactively modify skillify configuration.

## Instructions

1. Load current config by reading `~/.claude/skillify.config.json`.
   If the file doesn't exist, show defaults from `${CLAUDE_PLUGIN_ROOT}/core/config_manager.py` (DEFAULT_CONFIG).

2. Present current settings to the user:

```
Skillify Configuration (~/.claude/skillify.config.json):

  auto_mode:                            true
  tool_count_threshold:                 10
  positive_signal_patterns:             ["perfect", "that worked", ...]
  default_save_location:                global
  max_skill_scan:                       20
  description_optimization_iterations:  3
```

3. Ask: "Which setting would you like to change? (or 'done' to exit)"

4. For each change, validate the value matches the expected type:
   - `auto_mode`: boolean (true/false)
   - `tool_count_threshold`: positive integer
   - `positive_signal_patterns`: list of strings
   - `default_save_location`: one of "global", "project"
   - `max_skill_scan`: positive integer
   - `description_optimization_iterations`: positive integer (1-10)

5. Save the updated config using:
   ```python
   import sys
   sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}")
   from core.config_manager import load_config, save_config
   config = load_config()
   config[key] = new_value
   save_config(config)
   ```

6. Confirm: "Updated <setting> to <value>."

7. Loop back to step 3 until the user says "done".
