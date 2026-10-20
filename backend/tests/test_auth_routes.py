"""Authentication and account-management behavior tests."""

from tests.conftest import login
from database import db
from models import User


def test_login_session_and_logout(client, accounts):
    """A valid role-specific login creates a session that logout clears."""
    response = login(client, "instructor")

    assert response.status_code == 200
    assert response.json["user"]["role"] == "instructor"
    assert "password_hash" not in response.json["user"]
    assert client.get("/api/auth/session").json["user"]["username"] == "teacher"
    assert client.post("/api/auth/logout").json["ok"] is True
    assert client.get("/api/auth/session").json["user"] is None


def test_login_rejects_wrong_password_or_selected_role(client, accounts):
    """Invalid credentials and role spoofing do not create a session."""
    wrong_password = login(client, "instructor", password="not-the-password")
    wrong_role = login(client, "admin")

    assert wrong_password.status_code == 401
    assert wrong_role.status_code == 401
    assert client.get("/api/auth/session").json["user"] is None


def test_login_validates_payload(client):
    """Malformed credentials fail validation with a useful client error."""
    response = client.post("/api/auth/login", json={"username": "", "password": "x", "role": "root"})

    assert response.status_code == 400
    assert response.json["error"] == "Invalid request."


def test_only_admin_can_create_accounts(client, accounts):
    """An instructor cannot create accounts through the admin endpoint."""
    login(client, "instructor")
    response = client.post("/api/users", json={
        "username": "newstudent",
        "display_name": "New Student",
        "password": "long-enough-password",
        "role": "student",
    })

    assert response.status_code == 403


def test_admin_creates_student_and_duplicate_username_fails(client, accounts):
    """Admins can create a student once, and duplicate usernames are rejected."""
    login(client, "admin", username="admin")
    payload = {
        "username": "newstudent",
        "display_name": "New Student",
        "password": "long-enough-password",
        "role": "student",
    }
    created = client.post("/api/users", json=payload)
    duplicate = client.post("/api/users", json=payload)

    assert created.status_code == 201
    assert created.json["user"]["must_change_password"] is True
    assert duplicate.status_code == 409


def test_password_change_requires_current_password(client, accounts):
    """The forced-change flow refuses an incorrect current password."""
    login(client, "admin", username="admin")
    response = client.post("/api/auth/password", json={
        "current_password": "wrong-password",
        "new_password": "a-strong-new-password",
    })

    assert response.status_code == 400


def test_forced_password_change_unlocks_protected_routes(client, app, accounts):
    """Accounts flagged for rotation remain restricted until they update a password."""
    with app.app_context():
        admin = db.session.get(User, accounts["admin"])
        admin.must_change_password = True
        db.session.commit()
    login(client, "admin", username="admin")

    assert client.get("/api/users").status_code == 403
    changed = client.post("/api/auth/password", json={
        "current_password": "correct-horse-battery",
        "new_password": "a-strong-new-password",
    })

    assert changed.status_code == 200
    assert changed.json["user"]["must_change_password"] is False
    assert client.get("/api/users").status_code == 200


def test_instructor_can_list_students_for_enrollment(client, accounts):
    """Instructors can find student accounts without gaining admin account access."""
    login(client, "instructor")

    assert client.get("/api/users/students").status_code == 200
    assert len(client.get("/api/users/students").json["students"]) == 1
    assert client.get("/api/users").status_code == 403


def test_user_can_update_profile_display_name(client, accounts):
    """Authenticated users can update their own display name."""
    login(client, "student", username="learner")
    response = client.patch("/api/auth/profile", json={"display_name": "Sam Learner"})

    assert response.status_code == 200
    assert response.json["user"]["display_name"] == "Sam Learner"


def test_profile_update_requires_authentication(client):
    """Unauthenticated requests cannot change profile details."""
    assert client.patch("/api/auth/profile", json={"display_name": "Someone Else"}).status_code == 401


def test_bootstrap_admin_requires_private_environment_values(app, monkeypatch):
    """The production bootstrap command refuses to invent default credentials."""
    monkeypatch.delenv("INITIAL_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("INITIAL_ADMIN_PASSWORD", raising=False)

    result = app.test_cli_runner().invoke(args=["bootstrap-admin"])

    assert result.exit_code != 0
    assert "12-character" in result.output


def test_bootstrap_admin_creates_one_forced_rotation_account(app, monkeypatch):
    """A trusted environment can create one initial admin with a forced password change."""
    monkeypatch.setenv("INITIAL_ADMIN_USERNAME", "RootAdmin")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "a-long-initial-secret")

    result = app.test_cli_runner().invoke(args=["bootstrap-admin"])

    assert result.exit_code == 0
    with app.app_context():
        admin = db.session.execute(db.select(User).filter_by(username="rootadmin")).scalar_one()
        assert admin.must_change_password is True
        assert admin.password_hash != "a-long-initial-secret"