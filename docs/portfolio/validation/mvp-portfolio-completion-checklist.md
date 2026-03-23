# MVP portfolio completion checklist

Created: 2026-03-23
Updated: 2026-03-23

**Epic (optional):** https://github.com/pkuppens/on_prem_rag/issues/91  

Use this when the **portfolio MVP** is a tracking umbrella: close it when linked work and verifications are satisfied, not as a separate coding task.

## Epic acceptance criteria

- [ ] All **delivery** work items completed or legitimately superseded
- [ ] All **verification** items pass (automated + human as defined)
- [ ] Demo runnable from **cold start** in under 5 minutes (evidence in demo recording and README)

## Delivery buckets (reconcile against GitHub)

The epic body may list historical issue numbers. **Reconcile** against open/closed on GitHub before closing.

- [ ] Foundation — closed or tracked
- [ ] Depth — closed or tracked
- [ ] Demo-ready — closed or tracked

## Verification issues

- [ ] Technical / tooling checks as defined (#72 or successor)
- [ ] MVP flow — use [mvp-end-to-end-flow-verification.md](./mvp-end-to-end-flow-verification.md)
- [ ] Healthcare demo (#74) if still in scope

## Evidence to attach in epic comment

| Item | Link or “N/A” |
|------|----------------|
| Latest green CI | |
| Demo video | |
| MVP validation | |
| Security documentation milestone | |

## Close epic

When all boxes are checked:

```text
gh issue close 91 --comment "Epic criteria met: [short summary]. Evidence: [links]."
```
