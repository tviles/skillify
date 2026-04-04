---
name: skillify
description: Analyze the current conversation and suggest reusable skills or commands to create from successful patterns.
---

# /skillify — Manual Mode

Analyze this conversation for patterns worth capturing as reusable skills or commands.

## Instructions

1. **Spawn the conversation-analyzer agent** using the Agent tool:
   - Agent definition: `${CLAUDE_PLUGIN_ROOT}/agents/conversation-analyzer.md`
   - Mode: **manual mode** — return a ranked menu of suggestions
   - Pass the current conversation context

2. **Present the menu** returned by the analyzer to the user.

3. **For each skill the user selects:**
   - Ask: "Save to project (.claude/) or global (~/.claude/)?"
   - Generate the file content using the appropriate template from `${CLAUDE_PLUGIN_ROOT}/templates/`
   - Write the file to the chosen location:
     - Skill: `<base>/skills/<name>/SKILL.md`
     - Command: `<base>/commands/<name>.md`
   - Ask: "Refine with skill-creator, or save as-is?"
     - If refine: invoke the skill-creator skill with the generated file path
     - If as-is: confirm save and report the file path

4. **After saving** (for each skill, optionally):
   - Generate trigger eval queries using `${CLAUDE_PLUGIN_ROOT}/core/eval_generator.py`
   - Run description optimization: `python3 ${CLAUDE_PLUGIN_ROOT}/core/eval/run_loop.py --eval-set <path> --skill-path <path> --max-iterations 2 --model <model>`
   - Update the skill description with the optimized version if it improved

5. **Report** what was created, where it was saved, and any optimization results.

## Notes

- The conversation-analyzer returns content — this command is responsible for file writes.
- If no patterns are found, the analyzer will say so; report that to the user and exit.
- Confidence levels in the menu help the user decide which to prioritize.
