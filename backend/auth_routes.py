"""Login, logout, session, and administrator account endpoints."""

from flask import Blueprint, jsonify, request, session
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models import User
from schemas import AccountCreateRequest, LoginRequest, PasswordChangeRequest, ProfileUpdateRequest
from security import current_user, require_roles, user_payload

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
users_bp = Blueprint("users", __name__, url_prefix="/api/users")


def parse_payload(schema):
    """Parse JSON using a Pydantic schema and return a standard 400 response on errors."""
    try:
        return schema.model_validate(request.get_json(silent=True) or {}), None
    except ValidationError as error:
        details = [{"field": ".".join(map(str, item["loc"])), "message": item["msg"]} for item in error.errors()]
        return None, (jsonify(error="Invalid request.", details=details), 400)


@auth_bp.post("/login")
def login():
    """Authenticate a user and issue a secure signed session cookie."""
    payload, error = parse_payload(LoginRequest)
    if error:
        return error

    user = db.session.execute(db.select(User).filter_by(username=payload.username.lower())).scalar_one_or_none()
    if (
        user is None
        or not user.is_active
        or user.role != payload.role
        or not check_password_hash(user.password_hash, payload.password)
    ):
        return jsonify(error="Username, password, or role is incorrect."), 401

    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    return jsonify(user=user_payload(user))


@auth_bp.get("/session")
def get_session():
    """Return the current account or an empty session response."""
    user = current_user()
    if user is None or not user.is_active:
        session.clear()
        return jsonify(user=None)
    return jsonify(user=user_payload(user))


@auth_bp.post("/logout")
def logout():
    """Clear the current browser session."""
    session.clear()
    return jsonify(ok=True)


@auth_bp.post("/password")
@require_roles("admin", "instructor", "student")
def change_password():
    """Change the current account password and clear its forced-change flag."""
    payload, error = parse_payload(PasswordChangeRequest)
    if error:
        return error
    user = current_user()
    if not check_password_hash(user.password_hash, payload.current_password):
        return jsonify(error="Current password is incorrect."), 400
    user.password_hash = generate_password_hash(payload.new_password)
    user.must_change_password = False
    db.session.commit()
    return jsonify(user=user_payload(user))


@auth_bp.patch("/profile")
@require_roles("admin", "instructor", "student")
def update_profile():
    """Update the display name for the authenticated account."""
    payload, error = parse_payload(ProfileUpdateRequest)
    if error:
        return error
    user = current_user()
    user.display_name = payload.display_name
    db.session.commit()
    return jsonify(user=user_payload(user))


@users_bp.get("")
@require_roles("admin")
def list_users():
    """List accounts for the administrator account-management view."""
    users = db.session.execute(db.select(User).order_by(User.created_at.desc())).scalars()
    return jsonify(users=[user_payload(user) for user in users])


@users_bp.get("/students")
@require_roles("admin", "instructor")
def list_students():
    """List student accounts available for course enrollment."""
    students = db.session.execute(
        db.select(User).filter_by(role="student", is_active=True).order_by(User.display_name)
    ).scalars()
    return jsonify(students=[user_payload(student) for student in students])


@users_bp.post("")
@require_roles("admin")
def create_user():
    """Create an instructor or student account from administrator input."""
    payload, error = parse_payload(AccountCreateRequest)
    if error:
        return error
    user = User(
        username=payload.username,
        display_name=payload.display_name,
        role=payload.role,
        password_hash=generate_password_hash(payload.password),
        must_change_password=True,
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="That username is already in use."), 409
    return jsonify(user=user_payload(user)), 201