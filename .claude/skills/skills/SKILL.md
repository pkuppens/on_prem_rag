---
name: skills
description: Create or update a repo-specific skill under .claude/skills. One SKILL.md per skill holds the full content; there are no delegate copies elsewhere.
argument-hint: [skill-name | create <name> | update <name>]
---

# Skills Skill

Create or update a repo-specific skill. `.claude/skills/<name>/SKILL.md` is the single source: full content, when to use, rules, examples.
Cross-repo skills come from `pkuppens/skills` (see [SKILLS_SETUP.md](../../../docs/technical/SKILLS_SETUP.md)); do not copy them here.

## When to Use

- User asks to "create a skill" or "add a command for X"
- A workflow is repeated often enough to deserve a `/name` entry point

## Steps

### 1. Create the skill

Create `.claude/skills/<name>/SKILL.md`:

```markdown
---
name: <name>
description: <one line: what it does and when to use it — this is what triggers the skill>
argument-hint: [<optional arguments>]
---

# <Display Name>

...
```

Include: purpose, when to invoke, related skills (delegate, do not duplicate), steps, output.
Relative links from `.claude/skills/<name>/` to the repo root start with `../../../`; to another skill, `../<other>/SKILL.md`.

### 2. Register it

Add a row to the commands table in [.claude/skills/README.md](../README.md).

### 3. Optional: add a rule

If the skill enforces rules, add `.cursor/rules/<name>.mdc` and reference it from the skill.

## References

- [README.md](../README.md) — skill index and issue workflow
- [ARCHITECTURE_RULES_SKILLS.md](../../../docs/technical/ARCHITECTURE_RULES_SKILLS.md) — rules/skills mapping
