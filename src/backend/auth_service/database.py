
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.rag_pipeline.utils.directory_utils import ensure_directory_exists, get_database_dir

# Ensure database directory exists
database_dir = get_database_dir()
ensure_directory_exists(database_dir)

DATABASE_URL = f"sqlite:///{database_dir / 'auth.db'}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
