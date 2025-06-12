# Monetization Approach

This document outlines simple monetization options and anti-abuse controls for the project.

## Options

- **Paid usage**: charge per API call or per uploaded document.
- **Subscription**: associate each user with an expiration date.
- **Lifetime license**: flag a user as exempt from subscription checks.

## Implementation Hints

- Add a `subscription_expires` field to the `User` model.
- Validate the subscription for each request in middleware.
- Use UTC time from the server to prevent client-side time manipulation.
- Consider storing request timestamps and rate limiting.

### Anti-abuse Controls

- Reject requests when the client timestamp deviates too much from the server time.
- Re-check subscription status on every authenticated request.

## References

- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)

## Code Files

- [src/backend/monetization/subscription.py](../../src/backend/monetization/subscription.py) - Subscription validity helpers
