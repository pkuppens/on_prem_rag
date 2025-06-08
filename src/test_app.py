"""
Test application demonstrating authentication-required endpoints.

This module provides a simple FastAPI application with endpoints that require
user authentication. Unauthenticated users are redirected to a login page
with a return URL parameter.
"""

import os
from typing import Optional
from urllib.parse import quote

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Import authentication dependencies from auth service
from auth_service.main import get_current_user, get_db
from auth_service.models import User

app = FastAPI(title="Test Application with Authentication")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8001/login", auto_error=False)


def get_current_user_optional(db: Session = Depends(get_db), token: str | None = Depends(oauth2_scheme)) -> User | None:
    """
    Get current user if authenticated, return None if not authenticated.
    Does not raise HTTPException for unauthenticated users.
    """
    if not token:
        return None

    try:
        from auth_service.main import get_current_user

        return get_current_user(db, token)
    except HTTPException:
        return None


@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with login links."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Application</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .button {
                display: inline-block;
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 10px;
            }
            .oauth-button {
                background-color: #4285f4;
            }
            .microsoft-button {
                background-color: #0078d4;
            }
        </style>
    </head>
    <body>
        <h1>Test Application</h1>
        <p>This application demonstrates authentication flows.</p>

        <h2>Test Endpoints</h2>
        <p><a href="/login_test" class="button">Login Test (Requires Authentication)</a></p>

        <h2>Authentication Options</h2>
        <h3>OAuth2 Login</h3>
        <p><a href="http://localhost:8001/oauth/google" class="button oauth-button">Login with Google</a></p>
        <p><a href="http://localhost:8001/oauth/outlook" class="button microsoft-button">Login with Microsoft</a></p>

        <h3>Local Account</h3>
        <p><a href="/login" class="button">Login with Username/Password</a></p>
        <p><a href="/register" class="button">Register New Account</a></p>

        <h2>API Documentation</h2>
        <p><a href="/docs" class="button">FastAPI Documentation</a></p>
        <p><a href="http://localhost:8001/docs" class="button">Auth Service Documentation</a></p>
    </body>
    </html>
    """


@app.get("/login", response_class=HTMLResponse)
async def login_page(return_url: str = Query("/")):
    """Login page with username/password form and OAuth2 options."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Test Application</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .form-container {{ max-width: 400px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; }}
            input[type="text"], input[type="password"] {{
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin: 5px;
            }}
            .oauth-button {{ background-color: #4285f4; }}
            .microsoft-button {{ background-color: #0078d4; }}
            .divider {{ margin: 20px 0; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="form-container">
            <h1>Login</h1>

            <form id="loginForm">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="button">Login</button>
            </form>

            <div class="divider">--- OR ---</div>

            <div style="text-align: center;">
                <a href="http://localhost:8001/oauth/google?return_url={quote(return_url)}" class="button oauth-button">
                    Login with Google
                </a><br>
                <a href="http://localhost:8001/oauth/outlook?return_url={quote(return_url)}" class="button microsoft-button">
                    Login with Microsoft
                </a>
            </div>

            <div style="text-align: center; margin-top: 20px;">
                <p>Don't have an account? <a href="/register?return_url={quote(return_url)}">Register here</a></p>
            </div>
        </div>

        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;

                try {{
                    const response = await fetch('http://localhost:8001/login', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            username: username,
                            password: password,
                            email: "" // Required by the schema but not used for login
                        }})
                    }});

                    if (response.ok) {{
                        const data = await response.json();
                        localStorage.setItem('auth_token', data.token);
                        window.location.href = '{return_url}';
                    }} else {{
                        const error = await response.json();
                        alert('Login failed: ' + error.detail);
                    }}
                }} catch (error) {{
                    alert('Login failed: ' + error.message);
                }}
            }});
        </script>
    </body>
    </html>
    """


@app.get("/register", response_class=HTMLResponse)
async def register_page(return_url: str = Query("/")):
    """Registration page for creating new local accounts."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register - Test Application</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .form-container {{ max-width: 400px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; }}
            input[type="text"], input[type="email"], input[type="password"] {{
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #28a745;
                color: white;
                text-decoration: none;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="form-container">
            <h1>Register</h1>

            <form id="registerForm">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="button">Register</button>
            </form>

            <div style="text-align: center; margin-top: 20px;">
                <p>Already have an account? <a href="/login?return_url={quote(return_url)}">Login here</a></p>
            </div>
        </div>

        <script>
            document.getElementById('registerForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const username = document.getElementById('username').value;
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;

                try {{
                    const response = await fetch('http://localhost:8001/register', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            username: username,
                            email: email,
                            password: password
                        }})
                    }});

                    if (response.ok) {{
                        alert('Registration successful! Please login.');
                        window.location.href = '/login?return_url={quote(return_url)}';
                    }} else {{
                        const error = await response.json();
                        alert('Registration failed: ' + error.detail);
                    }}
                }} catch (error) {{
                    alert('Registration failed: ' + error.message);
                }}
            }});
        </script>
    </body>
    </html>
    """


@app.get("/login_test")
async def login_test(request: Request, current_user: User | None = Depends(get_current_user_optional)):
    """
    Test endpoint that requires authentication.

    If user is not authenticated, redirects to login page with return URL.
    If user is authenticated, shows welcome message with user details.
    """
    if not current_user:
        # Redirect to login page with return URL
        return_url = str(request.url)
        login_url = f"/login?return_url={quote(return_url)}"
        return RedirectResponse(url=login_url, status_code=302)

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login Test - Authenticated</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .success {{ color: #28a745; }}
            .info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #dc3545;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 10px 5px 0 0;
            }}
        </style>
    </head>
    <body>
        <h1>🎉 Authentication Successful!</h1>
        <p class="success">You have successfully accessed a protected endpoint.</p>

        <div class="info">
            <h3>User Information:</h3>
            <p><strong>Username:</strong> {current_user.username}</p>
            <p><strong>Email:</strong> {current_user.email or "Not provided"}</p>
            <p><strong>Roles:</strong> {current_user.roles}</p>
            <p><strong>User ID:</strong> {current_user.id}</p>
        </div>

        <h3>Test Results:</h3>
        <p>✅ Authentication middleware working correctly</p>
        <p>✅ User session validated successfully</p>
        <p>✅ Protected endpoint accessible to authenticated users</p>

        <div>
            <a href="/" class="button" style="background-color: #007bff;">Go Home</a>
            <button id="logoutBtn" class="button">Logout</button>
        </div>

        <script>
            document.getElementById('logoutBtn').addEventListener('click', async () => {{
                try {{
                    const token = localStorage.getItem('auth_token');
                    if (token) {{
                        await fetch('http://localhost:8001/logout', {{
                            method: 'POST',
                            headers: {{
                                'Authorization': 'Bearer ' + token
                            }}
                        }});
                        localStorage.removeItem('auth_token');
                    }}
                    window.location.href = '/';
                }} catch (error) {{
                    console.error('Logout error:', error);
                    // Still redirect even if logout fails
                    localStorage.removeItem('auth_token');
                    window.location.href = '/';
                }}
            }});
        </script>
    </body>
    </html>
    """)


@app.get("/api/login_test")
async def api_login_test(current_user: User = Depends(get_current_user)):
    """
    API version of login test endpoint.

    Returns JSON response for API clients.
    Requires valid authentication token in Authorization header.
    """
    return {
        "status": "success",
        "message": "Authentication successful",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "roles": current_user.roles,
        },
        "test_results": {
            "authentication_middleware": "✅ Working",
            "session_validation": "✅ Working",
            "protected_endpoint_access": "✅ Working",
        },
    }


def start_server() -> None:
    """Start the test application server."""
    import uvicorn

    uvicorn.run("test_app:app", host="0.0.0.0", port=8002, reload=True)


if __name__ == "__main__":
    start_server()
