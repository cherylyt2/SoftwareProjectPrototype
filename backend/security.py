"""Authentication helpers and role-based access decorators."""

from functools import wraps
from typing import Any, Callable

from flask import jsonify, request, session

from database import db
from models import User


def user_payload(user: User) -> dict[str, Any]:
    """Return the public account fields safe to expose to the current user."""
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
        "must_change_password": user.must_change_password,
    }


def current_user() -> User | None:
    """Load the authenticated account referenced by the signed session cookie."""
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def require_roles(*roles: str) -> Callable:
    """Protect a route with authentication and an optional role allowlist."""

    def decorate(route: Callable) -> Callable:
        @wraps(route)
        def wrapped(*args: Any, **kwargs: Any):
            user = current_user()
            if user is None or not user.is_active:
                return jsonify(error="Authentication required."), 401
            if user.must_change_password and request.endpoint != "auth.change_password":
                return jsonify(error="Change your password before continuing.", must_change_password=True), 403
            if roles and user.role not in roles:
                return jsonify(error="You do not have permission to perform this action."), 403
            return route(*args, **kwargs)

        return wrapped

    return decorate