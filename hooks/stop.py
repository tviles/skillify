#!/usr/bin/env python3
"""Stop hook for skillify. Checks thresholds and signals analyzer if warranted."""
import json
import os
import sys


def main():
    try:
        input_data = json.loads(sys.stdin.read())

        plugin_root = os.environ.get(
            "CLAUDE_PLUGIN_ROOT",
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        sys.path.insert(0, plugin_root)

        from core.config_manager import load_config
        from core.threshold_checker import should_analyze, clean_flag

        config = load_config()

        if not config.get("auto_mode", True):
            print(json.dumps({}))
            return

        if not should_analyze(input_data, config):
            print(json.dumps({}))
            return

        clean_flag()

        result = {
            "systemMessage": (
                "**[skillify]** This conversation has patterns worth capturing as "
                "reusable skills. Please analyze the conversation using the skillify "
                "conversation-analyzer agent and present findings to the user for "
                "confirmation before saving."
            )
        }
        print(json.dumps(result))

    except Exception as e:
        # Fail-safe: never block Claude from stopping
        print(json.dumps({}))
        print(f"skillify stop hook error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
