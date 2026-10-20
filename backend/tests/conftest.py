"""Shared app, database, account, and session fixtures."""

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from database import db
from models import User


@pytest.fixture
def app():
    """Create an isolated application with an in-memory SQLite database."""
    test_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-session-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SESSION_COOKIE_SECURE": False,
    })
    with test_app.app_context():
        db.create_all()
    yield test_app
    with test_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Return a test client for the isolated application."""
    return app.test_client()


@pytest.fixture
def accounts(app):
    """Create one account per role and a second instructor for ownership tests."""
    users = {
        "admin": ("admin", "Administrator", "admin"),
        "instructor": ("teacher", "Tara Teacher", "instructor"),
        "other_instructor": ("other", "Omar Other", "instructor"),
        "student": ("learner", "Sam Student", "student"),
    }
    with app.app_context():
        for username, display_name, role in users.values():
            db.session.add(User(
                username=username,
                display_name=display_name,
                role=role,
                password_hash=generate_password_hash("correct-horse-battery"),
            ))
        db.session.commit()
        return {
            key: db.session.execute(db.select(User).filter_by(username=values[0])).scalar_one().id
            for key, values in users.items()
        }


def login(client, role: str, username: str = "teacher", password: str = "correct-horse-battery"):
    """Authenticate a test account using the public login endpoint."""
    return client.post("/api/auth/login", json={"username": username, "password": password, "role": role})