import os
import shutil
import tempfile
import uuid

import bcrypt
import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

_test_uploads = os.path.join(tempfile.mkdtemp(), "uploads")

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["PDF_UPLOAD_DIR"] = _test_uploads

from app.core.database import Base, get_db
from app.main import app
from app.models.models import User, Keyword

# Single shared in-memory SQLite for all threads
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def _hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    os.makedirs(_test_uploads, exist_ok=True)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    db = TestSession()
    user = User(
        id=uuid.uuid4(),
        email="admin@clsepa.org",
        hashed_password=_hash_pw("testpass123"),
        full_name="Test Admin",
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.close()

    res = client.post("/api/auth/login", data={"username": "admin@clsepa.org", "password": "testpass123"})
    return res.json()["access_token"]


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sample_keywords():
    db = TestSession()
    keywords = []
    for name in ["Mold", "Plumbing", "Electrical", "Heat", "Rent Overcharge"]:
        kw = Keyword(id=uuid.uuid4(), name=name)
        db.add(kw)
        keywords.append(kw)
    db.commit()
    for kw in keywords:
        db.refresh(kw)
    result = [(str(kw.id), kw.name) for kw in keywords]
    db.close()
    return result
