import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .database import SessionLocal, init_db
from .models import Session as DBSession
from .models import User
from .schemas import TokenOut, UserCreate, UserOut

ACCESS_TIMEOUT = timedelta(minutes=30)
SERVER_DEBUG = os.getenv("SERVER_DEBUG", "False").lower() == "true"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# OAuth2 setup for external providers
oauth = OAuth()

# Google OAuth2 configuration
if os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"):
    oauth.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        authorize_url="https://accounts.google.com/o/oauth2/auth",
        access_token_url="https://oauth2.googleapis.com/token",
        client_kwargs={
            "scope": "openid email profile",
        },
    )

# Microsoft OAuth2 configuration
if os.getenv("MICROSOFT_CLIENT_ID") and os.getenv("MICROSOFT_CLIENT_SECRET"):
    tenant_id = os.getenv("MICROSOFT_TENANT_ID", "common")
    oauth.register(
        name="microsoft",
        client_id=os.getenv("MICROSOFT_CLIENT_ID"),
        client_secret=os.getenv("MICROSOFT_CLIENT_SECRET"),
        authorize_url=f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
        access_token_url=f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        client_kwargs={
            "scope": "openid profile email",
        },
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    init_db()
    yield


app = FastAPI(title="Auth Service", lifespan=lifespan)

# Add CORS middleware to allow cross-origin requests from test app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8002", "http://localhost:5173"],  # Test app and React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware for OAuth2 flows
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "your-secret-key-change-this"))


def start_server() -> None:

    import uvicorn

    # Configure uvicorn logging to include timestamps
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s.%(msecs)03d %(levelprefix)s %(message)s"
    log_config["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    log_config["formatters"]["access"]["fmt"] = (
        '%(asctime)s.%(msecs)03d INFO:     %(client_addr)s - "%(request_line)s" %(status_code)s'
    )
    log_config["formatters"]["access"]["datefmt"] = "%Y-%m-%d %H:%M:%S"

    uvicorn.run("backend.auth_service.main:app", host="0.0.0.0", port=8001, reload=True, log_config=log_config)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_password_hash(password: str) -> str:
    import hashlib

    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return get_password_hash(password) == hashed


def create_session(db: Session, user: User) -> DBSession:
    session = DBSession(user=user)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    session = db.query(DBSession).filter(DBSession.token == token).first()
    if not session or datetime.utcnow() - session.last_active > ACCESS_TIMEOUT:
        if session:
            db.delete(session)
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    session.last_active = datetime.utcnow()
    db.commit()
    return session.user


@app.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> User:
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    user = User(username=user_in.username, email=user_in.email, password_hash=get_password_hash(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=TokenOut)
def login(form: UserCreate, db: Session = Depends(get_db)) -> TokenOut:
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    session = create_session(db, user)
    return TokenOut(token=session.token)


@app.post("/logout")
def logout(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> None:
    session = db.query(DBSession).filter(DBSession.token == token).first()
    if session:
        db.delete(session)
        db.commit()


@app.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@app.get("/oauth/google")
async def oauth_google(request: Request):
    """Initiate Google OAuth2 authentication flow."""
    if "google" not in oauth._clients:
        raise HTTPException(
            status_code=501,
            detail="Google OAuth2 not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.",
        )

    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/oauth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth2 callback and create user session."""
    if "google" not in oauth._clients:
        raise HTTPException(status_code=501, detail="Google OAuth2 not configured")

    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info or not user_info.get("email"):
            raise HTTPException(status_code=400, detail="Failed to get user information from Google")

        # Create or get existing user
        email = user_info.get("email")
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Create new user from OAuth2 data
            user = User(
                username=user_info.get("name", email.split("@")[0]),
                email=email,
                password_hash=None,  # OAuth2 users don't have local passwords
                roles="user",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Create session
        session = create_session(db, user)

        return {"status": "success", "token": session.token, "user": {"username": user.username, "email": user.email}}

    except Exception as e:
        error_detail = f"Google authentication failed: {str(e)}" if SERVER_DEBUG else "Google authentication failed"
        raise HTTPException(status_code=401, detail=error_detail) from e


@app.get("/oauth/outlook")
async def oauth_outlook(request: Request):
    """Initiate Microsoft OAuth2 authentication flow."""
    if "microsoft" not in oauth._clients:
        raise HTTPException(
            status_code=501,
            detail="Microsoft OAuth2 not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET environment variables.",
        )

    redirect_uri = request.url_for("outlook_callback")
    return await oauth.microsoft.authorize_redirect(request, redirect_uri)


@app.get("/oauth/outlook/callback")
async def outlook_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Microsoft OAuth2 callback and create user session."""
    if "microsoft" not in oauth._clients:
        raise HTTPException(status_code=501, detail="Microsoft OAuth2 not configured")

    try:
        token = await oauth.microsoft.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info or not user_info.get("email"):
            raise HTTPException(status_code=400, detail="Failed to get user information from Microsoft")

        # Create or get existing user
        email = user_info.get("email")
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Create new user from OAuth2 data
            user = User(
                username=user_info.get("name", email.split("@")[0]),
                email=email,
                password_hash=None,  # OAuth2 users don't have local passwords
                roles="user",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Create session
        session = create_session(db, user)

        return {"status": "success", "token": session.token, "user": {"username": user.username, "email": user.email}}

    except Exception as e:
        error_detail = f"Microsoft authentication failed: {str(e)}" if SERVER_DEBUG else "Microsoft authentication failed"
        raise HTTPException(status_code=401, detail=error_detail) from e


@app.get("/oauth/providers")
def get_oauth_providers():
    """Get list of configured OAuth2 providers."""
    providers = []
    if "google" in oauth._clients:
        providers.append({"name": "google", "url": "/oauth/google"})
    if "microsoft" in oauth._clients:
        providers.append({"name": "microsoft", "url": "/oauth/outlook"})
    return {"providers": providers}


if __name__ == "__main__":
    start_server()
