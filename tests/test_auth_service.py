import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from auth_service.main import app

# Remove the SQLite database between test runs to ensure a clean state
DB_PATH = Path(__file__).resolve().parents[1] / "src" / "auth_service" / "auth.db"


