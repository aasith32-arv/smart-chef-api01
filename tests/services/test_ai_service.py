import json
from unittest.mock import patch

import pytest

from app.services.ai_service import AIService


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.body).encode("utf-8")


def test_gemini_provider_status(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-flash-latest")

    status = AIService.status()

    assert status["configured"] is True
    assert status["provider"] == "gemini"
    assert status["model"] == "gemini-flash-latest"
    assert "Gemini ready" in status["message"]


def test_gemini_chat_uses_generate_content_api(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-flash-latest")
    response = FakeResponse(
        {
            "candidates": [
                {"content": {"parts": [{"text": '{"dish":"Test curry"}'}]}}
            ]
        }
    )

    with patch("urllib.request.urlopen", return_value=response) as urlopen:
        result = AIService._chat("Return JSON", "Make curry")

    request = urlopen.call_args.args[0]
    payload = json.loads(request.data)
    assert request.full_url.endswith(
        "/models/gemini-flash-latest:generateContent"
    )
    assert request.headers["X-goog-api-key"] == "test-gemini-key"
    assert payload["systemInstruction"]["parts"][0]["text"] == "Return JSON"
    assert payload["contents"][0]["parts"][0]["text"] == "Make curry"
    assert payload["generationConfig"]["responseMimeType"] == "application/json"
    assert result == {"dish": "Test curry"}


def test_invalid_gemini_json_has_clear_error(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    response = FakeResponse(
        {"candidates": [{"content": {"parts": [{"text": "not json"}]}}]}
    )

    with patch("urllib.request.urlopen", return_value=response):
        with pytest.raises(RuntimeError, match="invalid JSON response"):
            AIService._chat("Return JSON", "Make curry")


def test_auto_provider_preserves_openai_priority(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "auto")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

    assert AIService.provider() == "openai"
