# Codex and Cursor Rules

These rules guide AI-assisted development using OpenAI Codex and Cursor.
They are referenced from `AGENTS.md` and `.cursor/rules`.

## Workflow Integration
- Work on the `main` branch with regular merges from feature branches.
- Keep commits small and atomic.
- All GitHub Actions must pass, including `ruff` linting.

## Package Management
- **Never** run `pip install`; use `uv add package-name` or `uv add --dev package-name`.
- Ensure new dependencies appear in `pyproject.toml` before importing.

## Documentation
- Architectural decisions live in `docs/technical/DOMAIN_DRIVEN_DESIGN.md`.
- Track progress in `docs/project/` files (`STORY-xxx`, `TASK-xxx`, `FEAT-xxx`).

## Testing
- Run `uv run pytest` to execute all tests.
- Add coverage where possible.
