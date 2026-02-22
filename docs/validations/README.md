# Implementation Validations

Committed validation documents for features. These are permanent, version-controlled proofs that an implementation meets its acceptance criteria.

## Linkage Requirement

Every committed validation file must reference the GitHub issue or chore it validates. Add this to the frontmatter or the opening section:

```yaml
---
issue: "#NNN"                        # GitHub issue number, OR
chore: "short-description"           # if no issue was created (e.g. "dependency-upgrade-2026-02")
---
```

For session-scoped validations in `tmp/github/issue-NNN/validation.md`, the issue number is implicit from the directory name.

## When to Commit a Validation

Commit to `docs/validations/` when:
- The feature is significant enough that future developers need to re-run validation
- The validation is tied to a demo or portfolio requirement
- The acceptance criteria are non-trivial and the validation steps represent institutional knowledge

For most cases, use `tmp/github/issue-NNN/validation.md` (gitignored, issue-scoped) instead.

## File Naming

```
feature-<slug>-validation.md    # e.g. feature-document-upload-validation.md
issue-NNN-validation.md         # when permanently tied to a specific issue
```

## Format

See [VALIDATION_FORMAT.md](../technical/VALIDATION_FORMAT.md) for the full schema.

## Usage

```
/create-validation for <slug>   # Creates docs/validations/feature-<slug>-validation.md
/run-validation docs/validations/feature-<slug>-validation.md
```
