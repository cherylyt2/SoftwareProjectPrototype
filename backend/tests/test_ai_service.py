"""OpenRouter request and response validation tests without network access."""

import json

import pytest

import ai_service
from ai_service import GeneratedPath, generate_path


class FakeResponse:
    """A small context-managed HTTP response for mocked OpenRouter requests."""

    def __init__(self, body: dict):
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit: int) -> bytes:
        """Return the prepared response bytes."""
        return self.body


def test_openrouter_uses_required_model_and_validates_response(monkeypatch):
    """Provider output is parsed as typed JSON and uses the configured model."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret")
    captured = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data)
        captured["authorization"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        return FakeResponse({"choices": [{"message": {"content": '{"steps":[{"title":"Start","objective":"Understand the basics","activity":"Write one example"}]}'}}]})

    monkeypatch.setattr(ai_service, "urlopen", fake_urlopen)

    result = generate_path("Learn ecology", ["Habitats"])

    assert result[0]["title"] == "Start"
    assert captured["payload"]["model"] == "nvidia/nemotron-3.5-lightning:free"
    assert captured["authorization"] == "Bearer test-secret"
    assert captured["timeout"] == 45


def test_openrouter_requires_server_api_key(monkeypatch):
    """Missing credentials fail locally without attempting a provider request."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        ai_service._request_json("test", GeneratedPath)


def test_invalid_model_content_is_rejected(monkeypatch):
    """Malformed provider JSON is surfaced as a safe validation failure."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret")
    monkeypatch.setattr(ai_service, "urlopen", lambda *_args, **_kwargs: FakeResponse({"choices": [{"message": {"content": '{"steps":[]}'}}]}))

    with pytest.raises(RuntimeError, match="invalid response"):
        ai_service._request_json("test", GeneratedPath)