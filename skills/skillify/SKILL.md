---
name: skillify
description: >
  Detects when a conversation contains successful patterns worth capturing as reusable skills.
  TRIGGER when the user validates a multi-step workflow ("perfect", "that worked", "exactly"),
  repeats the same instruction multiple times, confirms a novel approach without pushback, or
  when the conversation shows a successful complex workflow with no backtracking. Also trigger
  when the user explicitly mentions wanting to save, capture, or reuse a workflow pattern.
  DO NOT trigger on short Q&A, simple file reads, casual conversation, or debugging sessions
  with no resolution.
---

# Skillify — Auto-Trigger Flag Setter

When you detect positive signals in the conversation (successful workflows, repeated instructions, validated approaches), set the skillify flag file so the Stop hook knows to analyze this conversation at the end.

## When to Set the Flag

Set the flag when you observe ANY of these:

1. **User validates a complex workflow** — "perfect", "that worked", "exactly what I wanted" after a multi-step sequence
2. **User repeats the same instruction** — same guidance given 2+ times in the conversation
3. **User confirms a novel approach** — positive reaction to an unusual solution

## How to Set the Flag

Run this command silently using the Bash tool:

```bash
touch /tmp/.skillify-active
```

Do NOT interrupt the conversation flow to set the flag. Do not narrate the action. Set it quietly and continue with the user's task.

## Important Constraints

- This skill ONLY sets the flag. The actual analysis happens in the Stop hook at conversation end.
- Do NOT analyze the conversation yourself.
- Do NOT suggest skills or commands to the user mid-conversation.
- Do NOT interrupt the user's task to mention skillify.
- If the flag file already exists, do nothing — no need to touch it again.
- Setting the flag is a lightweight signal. The Stop hook will independently verify thresholds (tool count + positive signals) before spawning the full analyzer agent.
