---
name: skills
description: Create or update Cursor + Claude skill pairs. Ensures .cursor/skills and .claude/skills stay in sync; Claude skills reference Cursor skills by convention.
argument-hint: [skill-name | create <name> | update <name>]
---

# Skills Skill

Create or update a **skill pair**: one Cursor skill (source of truth) and one Claude skill (references Cursor).

## Convention

- **Cursor skill** (source of truth): `.cursor/skills/<name>/SKILL.md` — full content, when to use, rules, examples.
- **Claude skill** (delegate): `.claude/skills/<name>/SKILL.md` — minimal; contains `Follow [.cursor/skills/<name>/SKILL.md] exactly.`

## When to Use

- User asks to "create a skill" or "add a Claude skill for X"
- New domain/rule needs both Cursor and Claude coverage
- Ensuring a new Cursor skill gets a matching Claude delegate

## Steps

### 1. Create Cursor Skill

Create `.cursor/skills/<name>/SKILL.md`:

```markdown
---
name: <name>
description: <one line: when to use, what it enforces>
---

# <Display Name>

...
```

Include: when to invoke, core rules, checklist, references.

### 2. Create Claude Skill

Create `.claude/skills/<name>/SKILL.md`:

```markdown
---
name: <name>
description: <same or shortened description>
---

# <Display Name>

Follow [.cursor/skills/<name>/SKILL.md](../../../.cursor/skills/<name>/SKILL.md) exactly.
```

Use relative path `../../../.cursor/skills/<name>/SKILL.md` from `.claude/skills/<name>/`.

### 3. Optional: Add Rule

If the skill enforces rules, add `.cursor/rules/<name>.mdc` and reference it from the skill. Update `golden-rules.mdc` or `ARCHITECTURE_RULES_SKILLS.md` as needed.

## Examples

- `api-design`: Cursor skill has full API rules; Claude skill delegates.
- `create-validation`, `run-validation`: Same pattern — Claude references Cursor.

## References

- [.cursor/skills/api-design/SKILL.md](../../../.cursor/skills/api-design/SKILL.md) — example Cursor skill
- [.claude/skills/api-design/SKILL.md](../api-design/SKILL.md) — example Claude delegate
- [ARCHITECTURE_RULES_SKILLS.md](../../../docs/technical/ARCHITECTURE_RULES_SKILLS.md) — rules/skills mapping
