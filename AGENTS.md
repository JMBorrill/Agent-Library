# Agent guidance (tool-agnostic)

Follow the rules in `CLAUDE.md`; they apply to any coding agent. Skills in `.claude/skills/` are portable
Agent Skills (spec frontmatter only) and can be installed into any directory with
`python3 scripts/install_packs.py --no-agents --skills-dir <dir>`. Files in `.claude/agents/` are Claude
Code subagent definitions; other tools can use their bodies as role instructions — keep reviewer roles
read-only. Start with `docs/INSTALL.md` and `docs/CAPABILITY_GUIDE.md`.
