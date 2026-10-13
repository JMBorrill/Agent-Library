"""Run a library skill or command through the Claude Agent SDK.

    pip install claude-agent-sdk
    export ANTHROPIC_API_KEY=...
    python examples/agent_sdk_review.py "/professional-agent-library:select-frameworks threat model for a payments API"

The library is loaded as a local plugin, so its skills, subagents and commands are available
(namespaced as /professional-agent-library:<name>). The init message is checked to confirm the
plugin actually loaded (the SDK silently skips a missing plugin path).
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

LIBRARY = Path(__file__).resolve().parents[1]


async def main(prompt: str, workdir: Path) -> int:
    from claude_agent_sdk import ClaudeAgentOptions, query

    options = ClaudeAgentOptions(
        cwd=str(workdir),
        plugins=[{"type": "local", "path": str(LIBRARY)}],
        setting_sources=["project"],
        allowed_tools=["Skill", "Read", "Glob", "Grep", "Bash", "Write", "Edit", "Task"],
    )
    loaded = False
    async for message in query(prompt=prompt, options=options):
        if getattr(message, "subtype", None) == "init":
            plugins = (getattr(message, "data", {}) or {}).get("plugins", [])
            loaded = any("professional-agent-library" in str(p) for p in plugins)
            if not loaded:
                print("ERROR: plugin did not load; check the library path", file=sys.stderr)
                return 1
        print(message)
    return 0 if loaded else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(asyncio.run(main(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd())))
