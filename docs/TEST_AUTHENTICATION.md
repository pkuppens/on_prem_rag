# Authentication Testing Guide

This document provides a comprehensive manual testing guide for the authentication system, including setup steps and detailed test scenarios for all authentication methods.

## Table of Contents

1. [Prerequisites and Setup](#prerequisites-and-setup)
2. [Starting the Services](#starting-the-services)
3. [Test Scenarios](#test-scenarios)
4. [OAuth2 Configuration](#oauth2-configuration)
5. [Troubleshooting](#troubleshooting)
6. [Expected Results](#expected-results)

## Prerequisites and Setup

### System Requirements

- Python 3.12 or higher
- UV package manager (installed and configured)
- Active internet connection for OAuth2 providers
- Web browser for interactive testing

### Environment Setup

1. **Clone and navigate to the project:**

   ```bash
   cd /path/to/on_prem_rag
   ```

2. **Install dependencies:**

   ```bash
   uv sync
   ```

3. **Set up environment variables (optional for basic testing):**
   Copy the template and fill in your values:

   ```bash
   cp env.example .env
   # Then edit .env with your actual OAuth2 credentials
   ```

   **Note:** See the [OAuth2 Configuration](#oauth2-configuration) section below for detailed instructions on obtaining these credentials.

## Starting the Services

### Step 1: Start the Authentication Service

In your first terminal window:

```bash
uv run start-auth
```

**Expected output:**

```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verification:**

- Open http://localhost:8001/docs in your browser
- You should see the FastAPI documentation with authentication endpoints

### Step 2: Start the Test Application

In your second terminal window:

```bash
uv run start-test-app
```

**Expected output:**

```
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
INFO:     Started reloader process [12347] using WatchFiles
INFO:     Started server process [12348]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verification:**

- Open http://localhost:8002 in your browser
- You should see the test application homepage

## Test Scenarios

### Test Scenario 1: Username/Password Authentication Flow

**Objective:** Verify local account registration and login functionality

**Steps:**

1. **Access the test application:**

   - Navigate to http://localhost:8002
   - Click "Login Test (Requires Authentication)"

2. **Verify redirect behavior:**

   - You should be redirected to `/login?return_url=http://localhost:8002/login_test`
   - The login page should display with username/password form

3. **Register a new account:**

   - Click "Register here" link
   - Fill in the registration form:
     - Username: `testuser`
     - Email: `test@example.com`
     - Password: `securepassword123`
   - Click "Register"

4. **Complete login:**

   - After successful registration, you'll be redirected to login
   - Enter the same credentials
   - Click "Login"

5. **Verify authentication success:**
   - You should be redirected to the original `/login_test` page
   - The page should show "🎉 Authentication Successful!"
   - User information should be displayed correctly

**Expected Results:**

- ✅ Registration creates new user account
- ✅ Login returns valid JWT token
- ✅ Protected endpoint is accessible
- ✅ User information is displayed correctly
- ✅ Redirect after login works properly

### Test Scenario 2: Google OAuth2 Authentication

**Prerequisites:** Google OAuth2 credentials configured in environment

**Steps:**

1. **Initiate Google OAuth2 flow:**

   - Navigate to http://localhost:8002
   - Click "Login with Google"

2. **Complete Google authentication:**

   - You should be redirected to Google's login page
   - Enter your Google credentials
   - Grant permission to the application

3. **Verify callback handling:**

   - After Google authentication, you should be redirected back
   - Check that the response contains success status and user info

4. **Test protected endpoint:**
   - Navigate to http://localhost:8002/login_test
   - Should display user information from Google profile

**Expected Results:**

- ✅ Redirect to Google OAuth2 page works
- ✅ Google callback processes user information
- ✅ User account is created/updated from Google profile
- ✅ Session is established successfully
- ✅ Protected endpoints are accessible

### Test Scenario 3: Microsoft OAuth2 Authentication

**Prerequisites:** Microsoft OAuth2 credentials configured in environment

**Steps:**

1. **Initiate Microsoft OAuth2 flow:**

   - Navigate to http://localhost:8002
   - Click "Login with Microsoft"

2. **Complete Microsoft authentication:**

   - You should be redirected to Microsoft's login page
   - Enter your Microsoft credentials
   - Grant permission to the application

3. **Verify callback handling:**

   - After Microsoft authentication, you should be redirected back
   - Check that the response contains success status and user info

4. **Test protected endpoint:**
   - Navigate to http://localhost:8002/login_test
   - Should display user information from Microsoft profile

**Expected Results:**

- ✅ Redirect to Microsoft OAuth2 page works
- ✅ Microsoft callback processes user information
- ✅ User account is created/updated from Microsoft profile
- ✅ Session is established successfully
- ✅ Protected endpoints are accessible

### Test Scenario 4: Session Management and Expiration

**Objective:** Verify session timeout and refresh behavior

**Steps:**

1. **Login with any method:**

   - Complete authentication using username/password or OAuth2

2. **Test active session refresh:**

   - Navigate to different protected endpoints
   - Verify that sessions remain active with activity

3. **Test session expiration:**

   - Wait for 30+ minutes without any activity
   - Try to access `/login_test` endpoint
   - Should be redirected to login page

4. **Test logout functionality:**
   - Login again
   - Click "Logout" button on the `/login_test` page
   - Verify you're redirected to home page
   - Try to access `/login_test` again - should redirect to login

**Expected Results:**

- ✅ Active sessions refresh automatically on activity
- ✅ Inactive sessions expire after 30 minutes
- ✅ Expired sessions redirect to login page
- ✅ Logout properly invalidates sessions
- ✅ Database cleanup removes expired sessions

### Test Scenario 5: API Authentication Testing

**Objective:** Test authentication for API endpoints using tokens

**Tools needed:** curl, Postman, or similar HTTP client

**Steps:**

1. **Obtain authentication token:**

   ```bash
   curl -X POST "http://localhost:8001/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "testuser", "email": "", "password": "securepassword123"}'
   ```

2. **Test protected API endpoint:**

   ```bash
   curl -X GET "http://localhost:8002/api/login_test" \
        -H "Authorization: Bearer YOUR_TOKEN_HERE"
   ```

3. **Test without token:**
   ```bash
   curl -X GET "http://localhost:8002/api/login_test"
   ```

**Expected Results:**

- ✅ Login returns JWT token
- ✅ API endpoint accepts valid Bearer tokens
- ✅ API endpoint rejects requests without tokens
- ✅ API endpoint returns appropriate HTTP status codes

### Test Scenario 6: Error Handling and Edge Cases

**Objective:** Verify proper error handling for various failure scenarios

**Steps:**

1. **Test invalid credentials:**

   - Try to login with wrong username/password
   - Observe error message and HTTP status

2. **Test duplicate registration:**

   - Register a user
   - Try to register again with the same username
   - Should receive appropriate error message

3. **Test malformed requests:**

   - Send invalid JSON to API endpoints
   - Test with missing required fields

4. **Test OAuth2 without configuration:**
   - Remove OAuth2 environment variables
   - Try to access OAuth2 endpoints
   - Should receive 501 "Not Configured" errors

**Expected Results:**

- ✅ Clear error messages for authentication failures
- ✅ Appropriate HTTP status codes (401, 400, 501)
- ✅ No sensitive information exposed in errors
- ✅ Graceful degradation when OAuth2 is not configured

## OAuth2 Configuration

### Google OAuth2 Setup

**Prerequisites:** Google account with access to Google Cloud Console (may require admin permissions for organization accounts)

1. **Access Google Cloud Console:**

   - Visit https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create or Select Project:**

   - Click the project dropdown at the top
   - Either select an existing project or click "New Project"
   - If creating new: Enter project name (e.g., "On-Prem RAG Auth")
   - Click "Create" and wait for project creation

3. **Enable Required APIs:**

   - Navigate to "APIs & Services" > "Library"
   - Search for "Google+ API" and click on it
   - Click "Enable" button
   - **Alternative:** Also enable "People API" for better user profile access

4. **Configure OAuth Consent Screen:**

   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" for testing (unless you have G Suite/Workspace)
   - Fill in required fields:
     - App name: "On-Prem RAG Authentication"
     - User support email: Your email
     - Developer contact: Your email
   - Click "Save and Continue"
   - Add test users if needed (your own email for testing)

5. **Create OAuth2 Credentials:**

   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Application type: "Web application"
   - Name: "On-Prem RAG Web Client"
   - **Authorized JavaScript origins:** `http://localhost:8001`
   - **Authorized redirect URIs:** `http://localhost:8001/oauth/google/callback`
   - Click "Create"

6. **Copy Credentials:**
   - Copy the "Client ID" and "Client Secret" from the popup
   - Add to your `.env` file:
   ```bash
   GOOGLE_CLIENT_ID=your_client_id_from_google_console
   GOOGLE_CLIENT_SECRET=your_client_secret_from_google_console
   ```

**Important Notes:**

- Keep your Client Secret private and never commit it to version control
- For production, update redirect URIs to use your actual domain with HTTPS
- The consent screen will show a warning for unverified apps during testing

### Microsoft OAuth2 Setup

**Prerequisites:** Microsoft account or Azure AD access (may require admin permissions for organization accounts)

1. **Access Azure Portal:**

   - Visit https://portal.azure.com/
   - Sign in with your Microsoft account or organizational account

2. **Navigate to App Registrations:**

   - Go to "Azure Active Directory" (may be in the left sidebar)
   - Click on "App registrations" in the left menu

3. **Register New Application:**

   - Click "New registration" at the top
   - Fill in the registration form:
     - **Name:** "On-Prem RAG Authentication"
     - **Supported account types:** "Accounts in any organizational directory and personal Microsoft accounts (e.g. Skype, Xbox)"
     - **Redirect URI (optional):** Web - `http://localhost:8001/oauth/outlook/callback`
   - Click "Register"

4. **Note the Application Details:**

   - On the app overview page, copy the **Application (client) ID**
   - Copy the **Directory (tenant) ID** (or use "common" for multi-tenant)

5. **Configure Authentication Settings:**

   - Click "Authentication" in the left menu
   - Verify the redirect URI is listed: `http://localhost:8001/oauth/outlook/callback`
   - Under "Implicit grant and hybrid flows":
     - ✅ Check "ID tokens (used for implicit and hybrid flows)"
   - Click "Save" at the top

6. **Create Client Secret:**

   - Click "Certificates & secrets" in the left menu
   - Click "New client secret"
   - Add description: "On-Prem RAG Development Secret"
   - Choose expiration: "24 months" (recommended for development)
   - Click "Add"
   - **Important:** Copy the secret **Value** immediately (it's only shown once!)

7. **Configure API Permissions (Optional):**

   - Click "API permissions" in the left menu
   - Verify "User.Read" permission is granted (should be default)
   - Click "Grant admin consent" if you have admin rights

8. **Add to Environment File:**
   ```bash
   MICROSOFT_CLIENT_ID=your_application_client_id_from_azure
   MICROSOFT_CLIENT_SECRET=your_client_secret_value_from_step_6
   MICROSOFT_TENANT_ID=common
   ```

**Important Notes:**

- The client secret value is only displayed once - copy it immediately
- For organization accounts, you may need admin approval for the app
- Use "common" as tenant ID to allow both personal and organizational accounts
- For production, update redirect URIs to use your actual domain with HTTPS

## Troubleshooting

### Common Issues and Solutions

1. **"OAuth2 not configured" errors:**

   - Ensure environment variables are set correctly
   - Restart the auth service after setting environment variables
   - Check variable names match exactly (case-sensitive)

2. **OAuth2 redirect loops:**

   - Verify redirect URIs match exactly in provider configuration
   - Check for trailing slashes in URLs
   - Ensure the auth service is running on the correct port (8001)

3. **Session/token issues:**

   - Clear browser localStorage: `localStorage.clear()`
   - Delete SQLite database file to reset: `rm auth.db`
   - Check that both services are running on correct ports

4. **CORS errors:**

   - Both services should be running on localhost
   - Check that the test app is calling the correct auth service URL

5. **Database errors:**
   - Ensure SQLite is available on your system
   - Check file permissions in the project directory
   - Delete and recreate database: `rm auth.db` then restart auth service

### Logging and Debugging

1. **Enable detailed logging:**

   - Both services output to console by default
   - Check terminal windows for error messages

2. **Browser developer tools:**

   - Open browser DevTools (F12)
   - Check Console tab for JavaScript errors
   - Check Network tab for HTTP request/response details

3. **Database inspection:**
   ```bash
   sqlite3 auth.db
   .tables
   SELECT * FROM users;
   SELECT * FROM sessions;
   .quit
   ```

## Expected Results Summary

### Successful Test Completion

After completing all test scenarios, you should have verified:

- ✅ **Local Authentication:** Username/password registration and login works
- ✅ **Google OAuth2:** Google account login and user creation works
- ✅ **Microsoft OAuth2:** Microsoft account login and user creation works
- ✅ **Session Management:** Sessions expire and refresh correctly
- ✅ **Protected Endpoints:** Authentication is properly enforced
- ✅ **API Authentication:** Bearer token authentication works
- ✅ **Error Handling:** Proper error messages and status codes
- ✅ **Redirect Flow:** Login redirects work with return URLs
- ✅ **User Experience:** Intuitive and functional UI flows

### Performance Expectations

- Authentication requests should complete within 2-3 seconds
- OAuth2 flows should complete within 5-10 seconds (depending on provider)
- Session validation should be nearly instantaneous
- Database operations should complete within 100ms

### Security Verification

- Passwords are hashed and never stored in plaintext
- JWT tokens are properly signed and validated
- OAuth2 flows use secure HTTPS endpoints
- Session tokens are properly invalidated on logout
- No sensitive information is exposed in error messages

## Next Steps

After successful testing, consider:

1. **Production Configuration:**

   - Use environment-specific configuration
   - Implement proper secret management
   - Configure HTTPS for production OAuth2 flows

2. **Additional Features:**

   - LDAP/Active Directory integration
   - Role-based access control
   - Multi-factor authentication
   - Business account restrictions

3. **Monitoring:**
   - Add authentication event logging
   - Monitor failed login attempts
   - Track session usage patterns

This testing guide ensures that all authentication flows work correctly before deploying to production environments.
