# Cursor / Claude skills setup (canonical tree)

Created: 2026-03-21
Updated: 2026-03-21

This repo does **not** commit the contents of `.cursor/skills`. Skills live in the portfolio repo **[pkuppens/pkuppens](https://github.com/pkuppens/pkuppens)** under [`skills/`](https://github.com/pkuppens/pkuppens/tree/main/skills). That tree is the single source of truth (see upstream [`skills/README.md`](https://github.com/pkuppens/pkuppens/blob/main/skills/README.md)).

## Required disk layout

Clone **both** repositories under the same parent folder:

```text
<parent>/
  on_prem_rag/    # this repo
  pkuppens/       # clone of pkuppens/pkuppens (must contain skills/)
```

Example:

```bash
cd ~/Repos/pkuppens   # or your equivalent
git clone https://github.com/pkuppens/on_prem_rag.git
git clone https://github.com/pkuppens/pkuppens.git
```

## Link `.cursor/skills` (run once per clone)

**Windows (PowerShell)** — creates a **directory junction** (no admin):

```powershell
.\scripts\link_cursor_skills.ps1
```

**Git Bash / Linux / macOS**:

```bash
bash scripts/link_cursor_skills.sh
```

After linking, Cursor discovers skills under `.cursor/skills/` (same tree as `pkuppens/skills/`).

## Why not commit skills here?

A sibling **junction** or **symlink** avoids duplicating dozens of `SKILL.md` files and keeps Git from treating another repo’s files as untracked content. `.cursor/skills` is listed in `.gitignore`.

## Repo-specific Claude skills

Thin delegates under [`.claude/skills/`](../../.claude/skills/) (for example commands under [`.cursor/commands/`](../../.cursor/commands/)) stay in this repository. Canonical lifecycle skills come from `pkuppens/skills` via the link above.

## References

- [ARCHITECTURE_RULES_SKILLS.md](ARCHITECTURE_RULES_SKILLS.md) — competency mapping (paths resolve through `.cursor/skills` after linking)
- [pkuppens PR #49](https://github.com/pkuppens/pkuppens/pull/49) — skills ported from this repo into the canonical tree
