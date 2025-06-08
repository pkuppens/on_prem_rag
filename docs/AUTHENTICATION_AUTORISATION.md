# Authentication and Authorization

This document describes the lightweight authentication service used by the project and how it can be extended with OAuth2 providers.

## Overview

The project exposes a dedicated microservice (**auth_service**) written with FastAPI. It provides:

- Username/password registration and login.
- Session tokens that expire after 30 minutes of inactivity.
- OAuth2 endpoints for Google and Microsoft Outlook integration.
- Role information stored on the user record (initially all roles are allowed).

Accounts are persisted in a local SQLite database (`auth.db`). Tokens are stored in a `sessions` table and automatically refreshed on each authenticated request.

## Managing Accounts

1. **Register** – `POST /register` with a username, email and password.
2. **Login** – `POST /login` returns a session token.
3. **Check Session** – `GET /me` with `Authorization: Bearer <token>` returns the current user.
4. **Logout** – `POST /logout` invalidates the session token.

## OAuth2 Integration

### Google OAuth2 Implementation

The `/oauth/google` endpoint provides Google OAuth2 integration. For complete implementation:

**Required Environment Variables:**

```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8001/oauth/google/callback
```

**Complete Implementation Code:**

```python
import os
import httpx
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests

@app.get("/oauth/google")
async def oauth_google():
    """Redirect to Google OAuth2 authorization."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=openid email profile"
    )

    return RedirectResponse(url=google_auth_url)

@app.get("/oauth/google/callback")
async def google_callback(code: str, request: Request):
    """Handle Google OAuth2 callback and create user session."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    # Exchange code for tokens
    token_data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data=token_data
        )
        token_response = response.json()

    # Verify and extract user info
    id_token_value = token_response.get('id_token')
    user_info = id_token.verify_oauth2_token(
        id_token_value, requests.Request(), client_id
    )

    # Create or update user and session
    # Implementation depends on your user management logic

    return {"status": "success", "user": user_info}
```

**Documentation References:**

- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google OAuth2 FastAPI Implementation Guide](https://parlak-deniss.medium.com/fastapi-authentication-with-google-oauth-2-0-9bb93b784eee)
- [Google Cloud Console Setup](https://console.cloud.google.com/)

### Microsoft Outlook OAuth2 Implementation

The `/oauth/outlook` endpoint provides Microsoft OAuth2 integration. For complete implementation:

**Required Environment Variables:**

```bash
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
MICROSOFT_TENANT_ID=your_tenant_id_or_common
MICROSOFT_REDIRECT_URI=http://localhost:8001/oauth/outlook/callback
```

**Complete Implementation Code:**

```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name="microsoft",
    client_id=os.getenv("MICROSOFT_CLIENT_ID"),
    client_secret=os.getenv("MICROSOFT_CLIENT_SECRET"),
    authorize_url=f"https://login.microsoftonline.com/{os.getenv('MICROSOFT_TENANT_ID', 'common')}/oauth2/v2.0/authorize",
    access_token_url=f"https://login.microsoftonline.com/{os.getenv('MICROSOFT_TENANT_ID', 'common')}/oauth2/v2.0/token",
    client_kwargs={
        "scope": "openid profile email",
    },
)

@app.get("/oauth/outlook")
async def oauth_outlook(request: Request):
    """Redirect to Microsoft OAuth2 authorization."""
    redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI")
    return await oauth.microsoft.authorize_redirect(request, redirect_uri)

@app.get("/oauth/outlook/callback")
async def outlook_callback(request: Request):
    """Handle Microsoft OAuth2 callback."""
    try:
        token = await oauth.microsoft.authorize_access_token(request)
        user_info = token.get("userinfo")

        # Create or update user and session
        # Implementation depends on your user management logic

        return {"status": "success", "user": user_info}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Microsoft authentication failed")
```

**Documentation References:**

- [Microsoft Identity Platform OAuth2 Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)
- [FastAPI Microsoft OAuth2 Implementation Guide](https://medium.com/@v0220225/backend-integrate-fastapi-with-microsoft-azure-oauth2-0-f25c7114d90b)
- [Azure App Registration Portal](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)

## OAuth2 Flow Documentation

### Authorization Code Flow

Both Google and Microsoft implementations use the OAuth2 Authorization Code flow:

1. **Authorization Request**: User is redirected to the provider's authorization server
2. **User Consent**: User logs in and grants permissions
3. **Authorization Code**: Provider redirects back with an authorization code
4. **Token Exchange**: Backend exchanges the code for access and ID tokens
5. **User Information**: Extract user profile from the ID token
6. **Session Creation**: Create a local session for the authenticated user

### Security Considerations

- **HTTPS Required**: OAuth2 flows must use HTTPS in production
- **State Parameter**: Use state parameter to prevent CSRF attacks
- **PKCE**: Consider implementing PKCE for enhanced security
- **Token Validation**: Always verify tokens using provider's public keys
- **Secure Storage**: Store client secrets securely (environment variables)

## Best Practices

### Current Recommendations (2024)

1. **Use Latest Endpoints**:

   - Google: `https://accounts.google.com/o/oauth2/auth`
   - Microsoft: `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize`

2. **Implement Proper Error Handling**:

   ```python
   try:
       token = await oauth_provider.authorize_access_token(request)
   except Exception as e:
       logger.error(f"OAuth error: {e}")
       raise HTTPException(status_code=401, detail="Authentication failed")
   ```

3. **Use Session Middleware**:

   ```python
   from starlette.middleware.sessions import SessionMiddleware
   app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
   ```

4. **Validate Tokens Properly**:
   - Verify token signatures using provider's JWKS endpoints
   - Check token expiration and issuer
   - Validate audience matches your client ID

## Adding Authorisation

The `auth_service` exposes a helper dependency `get_current_user` which verifies the session token and can be reused in other FastAPI apps. Additional decorators can be added to enforce role based access.

Pages in the frontend should check the user context to decide which functionality to enable. Anonymous users are permitted but may have fewer privileges in future releases.

## Human User Testing Scenarios

### Test Case 1: Username/Password Authentication

**Objective**: Verify basic authentication flow works correctly

**Steps**:

1. Start auth service: `uv run start-auth`
2. Navigate to `http://localhost:8001/docs`
3. Use `/register` endpoint with test credentials:
   ```json
   {
     "username": "testuser",
     "email": "test@example.com",
     "password": "securepassword123"
   }
   ```
4. Use `/login` endpoint with same credentials
5. Copy the returned token
6. Use `/me` endpoint with `Authorization: Bearer <token>` header

**Expected Results**:

- Registration returns 200 with user details
- Login returns 200 with valid JWT token
- `/me` endpoint returns user information
- Token expires after 30 minutes of inactivity

### Test Case 2: Google OAuth2 Flow

**Objective**: Verify Google OAuth2 integration works end-to-end

**Prerequisites**:

- Google OAuth2 credentials configured
- Environment variables set

**Steps**:

1. Navigate to `/oauth/google` endpoint
2. Complete Google authentication flow
3. Verify redirect to callback endpoint
4. Check user session is created
5. Test protected endpoints with new session

**Expected Results**:

- Redirected to Google login page
- After authentication, redirected back to callback
- User profile extracted from Google ID token
- Local session created successfully

### Test Case 3: Microsoft OAuth2 Flow

**Objective**: Verify Microsoft OAuth2 integration works end-to-end

**Prerequisites**:

- Azure AD app registration completed
- Microsoft OAuth2 credentials configured

**Steps**:

1. Navigate to `/oauth/outlook` endpoint
2. Complete Microsoft authentication flow
3. Verify redirect to callback endpoint
4. Check user session is created
5. Test protected endpoints with new session

**Expected Results**:

- Redirected to Microsoft login page
- After authentication, redirected back to callback
- User profile extracted from Microsoft ID token
- Local session created successfully

### Test Case 4: Session Management

**Objective**: Verify session timeout and refresh behavior

**Steps**:

1. Login and obtain session token
2. Make API calls and verify token refresh
3. Wait for 30+ minutes without activity
4. Attempt to use expired token
5. Verify proper error handling

**Expected Results**:

- Active sessions refresh automatically
- Expired sessions return 401 error
- Expired sessions are cleaned up from database

### Test Case 5: Error Handling

**Objective**: Verify proper error handling for authentication failures

**Steps**:

1. Test with invalid credentials
2. Test with malformed OAuth2 responses
3. Test with network failures during OAuth2 flow
4. Test with invalid/expired tokens

**Expected Results**:

- Clear error messages for invalid credentials
- Graceful degradation for OAuth2 failures
- Proper HTTP status codes (401, 403, 500)
- No sensitive information exposed in errors

### Test Case 6: Cross-Origin Integration

**Objective**: Verify authentication works with frontend applications

**Prerequisites**:

- Frontend application running on different port

**Steps**:

1. Configure CORS settings
2. Test login from frontend application
3. Verify cookies are set correctly
4. Test API calls with authentication headers

**Expected Results**:

- CORS headers allow frontend requests
- Authentication cookies work across origins
- Protected API endpoints accessible from frontend

These test scenarios ensure the authentication system works reliably across different user flows and edge cases, providing confidence in the implementation before production deployment.
