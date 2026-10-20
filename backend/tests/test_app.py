"""Tests for the Flask deployment probe."""

from app import app


def test_health_check_returns_service_status():
    """The health route returns a successful JSON response."""
    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok", "service": "learning-platform-api"}


def test_health_check_rejects_post():
    """The read-only health route does not accept POST requests."""
    response = app.test_client().post("/api/health")

    assert response.status_code == 405


def test_unknown_route_returns_not_found():
    """Unknown API routes return a not-found response."""
    response = app.test_client().get("/api/missing")

    assert response.status_code == 404