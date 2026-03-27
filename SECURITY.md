# Security policy

**Created:** 2026-03-27

## Reporting a vulnerability

Please **do not** open a public GitHub issue for undisclosed security vulnerabilities.

1. **Preferred:** Use [GitHub Security Advisories](https://github.com/pkuppens/on_prem_rag/security/advisories) for this repository (report a vulnerability privately).
2. **Alternative:** Contact the repository maintainer via GitHub (e.g. direct message or email shown on the profile), with a clear subject line such as `Security: on_prem_rag`.

Include enough detail to reproduce or understand the issue (affected component, version or commit, steps, impact). We aim to acknowledge reports within a few business days.

## Scope

This policy applies to the `on_prem_rag` codebase and its documented deployment patterns. Third-party services you configure yourself (cloud APIs, external identity providers) follow those vendors’ policies.

## Supported versions

Security fixes are applied on the active development line (`main`). For production deployments, pin a commit or release tag and track upstream updates.

## Technical documentation

For security architecture, data flows, and compliance notes (informational, not legal advice), see:

- [docs/technical/SECURITY.md](docs/technical/SECURITY.md) — components and controls in this repository
- [docs/technical/SECURITY_DATA_FLOW_AND_COMPLIANCE.md](docs/technical/SECURITY_DATA_FLOW_AND_COMPLIANCE.md) — data lifecycle diagram and GDPR / NEN 7510 / DPIA readiness

## Authentication and API usage

End-user authentication and session handling are described in [docs/AUTHENTICATION_AUTORISATION.md](docs/AUTHENTICATION_AUTORISATION.md).
