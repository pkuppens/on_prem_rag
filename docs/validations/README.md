# Implementation Validations

Committed validation documents for features. These are permanent, version-controlled proofs that an implementation meets its acceptance criteria.

## When to Commit a Validation

Commit to `docs/validations/` when:
- The feature is significant enough that future developers need to re-run validation
- The validation is tied to a demo or portfolio requirement
- The acceptance criteria are non-trivial and the validation steps represent institutional knowledge

For session-scoped, ephemeral validations (most cases), use `tmp/validations/` instead.

## File Naming

```
feature-<slug>-validation.md    # e.g. feature-document-upload-validation.md
issue-NNN-validation.md         # when tied to a specific issue permanently
```

## Format

See [VALIDATION_FORMAT.md](../technical/VALIDATION_FORMAT.md) for the full schema.

## Usage

```
/create-validation for <slug>   # Creates docs/validations/feature-<slug>-validation.md
/run-validation docs/validations/feature-<slug>-validation.md
```
