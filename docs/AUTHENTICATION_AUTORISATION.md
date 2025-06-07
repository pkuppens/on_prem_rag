# Authentication and Authorisation

This document describes the lightweight authentication service used by the project and how it can be extended with OAuth2 providers.

## Overview

The project exposes a dedicated microservice (**auth_service**) written with FastAPI.  It provides:

- Username/password registration and login.
- Session tokens that expire after 30 minutes of inactivity.
- Placeholder OAuth2 endpoints for Google and Outlook.
- Role information stored on the user record (initially all roles are allowed).

Accounts are persisted in a local SQLite database (`auth.db`).  Tokens are stored in a `sessions` table and automatically refreshed on each authenticated request.

## Managing Accounts

1. **Register** – `POST /register` with a username, email and password.
2. **Login** – `POST /login` returns a session token.
3. **Check Session** – `GET /me` with `Authorization: Bearer <token>` returns the current user.
4. **Logout** – `POST /logout` invalidates the session token.

OAuth2 endpoints (`/oauth/google` and `/oauth/outlook`) currently return the remote authorisation URLs.  They can be expanded to handle the complete OAuth flow when the required client credentials are configured.

## Adding Authorisation

The `auth_service` exposes a helper dependency `get_current_user` which verifies the session token and can be reused in other FastAPI apps.  Additional decorators can be added to enforce role based access.

Pages in the frontend should check the user context to decide which functionality to enable.  Anonymous users are permitted but may have fewer privileges in future releases.

