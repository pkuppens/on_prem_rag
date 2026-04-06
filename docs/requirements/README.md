# Engineering requirements (UR / SR / SSR)

This folder holds **product engineering requirements** and the **requirements traceability matrix (RTM)**. It complements—but does not replace—SAFe portfolio artifacts:

| Location | Purpose |
|----------|---------|
| [project/portfolio/epics/](../../project/portfolio/epics/) | Portfolio epics (e.g. [EPIC-001](../../project/portfolio/epics/EPIC-001.md)) |
| [project/program/features/](../../project/program/features/) | Program features (e.g. [FEAT-001](../../project/program/features/FEAT-001.md)–[FEAT-006](../../project/program/features/FEAT-006.md)) |
| [project/team/stories/](../../project/team/stories/) | User stories and sprint-sized work |
| `docs/requirements/` here | **UR**, **SR**, **SSR**, optional **CR**, and **RTM** with validation IDs |

## Documents

| File | Content |
|------|---------|
| [SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md) | **SR-*** system requirements (parent: **UR-***) |
| [SOFTWARE_SUBSYSTEM_REQUIREMENTS.md](SOFTWARE_SUBSYSTEM_REQUIREMENTS.md) | **SSR-*** allocation to subsystems (parent: **SR-***) |
| [REQUIREMENTS_TRACEABILITY_MATRIX.md](REQUIREMENTS_TRACEABILITY_MATRIX.md) | RTM: UR–SR–SSR–**VAL-*** and optional EPIC/FEAT |

## Validation IDs

Validations use a **level prefix** that matches the requirement type:

- **VAL-UR-*** — acceptance / stakeholder-facing checks for **UR-***
- **VAL-SR-*** — system verification for **SR-*** (often primary for automated tests)
- **VAL-SSR-*** — mirrors **SSR-*** (e.g. `SSR-QRY-002` → `VAL-SSR-QRY-002`)

## Product scope note

**Speech (STT) and synthesis (TTS)** are treated as a **separate reusable product** in documentation. Core RAG requirements may **reference** that boundary; detailed STT/TTS subsystem requirements belong with that product line, not inside core SSR scope.

## References

- [PRODUCT_REQUIREMENTS_DOCUMENT.md](../PRODUCT_REQUIREMENTS_DOCUMENT.md) — high-level PRD with **UR-*** summary
- [requirements-design-test-traceability.md](../technical/requirements-design-test-traceability.md) — lightweight per-change traceability

Updated: 2026-04-06
