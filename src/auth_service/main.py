from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import SessionLocal, init_db
from .models import Session as DBSession
from .models import User
from .schemas import OAuthRedirect, TokenOut, UserCreate, UserOut

ACCESS_TIMEOUT = timedelta(minutes=30)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(title="Auth Service")


def start_server() -> None:
    import uvicorn

    uvicorn.run("auth_service.main:app", host="0.0.0.0", port=8001, reload=True)


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


@app.on_event("startup")
def on_startup() -> None:
    init_db()


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


@app.get("/oauth/google", response_model=OAuthRedirect)
def oauth_google() -> OAuthRedirect:
    # Placeholder for OAuth2 redirect URL generation
    return OAuthRedirect(url="https://accounts.google.com/o/oauth2/v2/auth")


@app.get("/oauth/outlook", response_model=OAuthRedirect)
def oauth_outlook() -> OAuthRedirect:
    return OAuthRedirect(url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize")


if __name__ == "__main__":
    start_server()

