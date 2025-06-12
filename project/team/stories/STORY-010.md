# User Story: Subscription Validation

**ID**: STORY-010
**Feature**: [FEAT-007: Monetization Controls](../../program/features/FEAT-007.md)
**Team**: Backend Engineering
**Status**: Backlog
**Priority**: P2
**Points**: 3
**Created**: 2025-06-07
**Updated**: 2025-06-07

## User Story
As a **system**,
I want **to verify that a user's subscription has not expired**,
So that **only paying users can access the API**.

## Business Context
Paid features require enforcing subscription status on every request.

## Acceptance Criteria
- [ ] Requests from expired users return HTTP 402
- [ ] Valid subscriptions allow normal access
- [ ] Timestamps outside the allowed window return HTTP 400

## Solution Approach
Add middleware that checks `subscription_expires` and validates the `X-Client-Time` header.

## Tasks
- [ ] **[TASK-023](../tasks/TASK-023.md)**: Add subscription utilities and tests
- [ ] **[TASK-024](../tasks/TASK-024.md)**: Implement timestamp middleware

## Definition of Done
- [ ] Unit tests >80% coverage
- [ ] Linting and formatting pass
- [ ] Documentation updated
