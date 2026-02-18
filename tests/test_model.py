"""Tests for model.py retry logic and error handling.

Tests target the httpx-based ElementLanguageModel, which uses
self._client.post() — NOT the OpenAI SDK.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from financebench.model import (
    ElementLanguageModel,
    _MAX_RETRIES,
    _RETRYABLE_STATUS_CODES,
    _MAX_CHOICE_ATTEMPTS,
)


def _make_model() -> ElementLanguageModel:
    """Create a model with a mocked httpx client."""
    model = ElementLanguageModel.__new__(ElementLanguageModel)
    model._model_name = "gpt-4.1"
    model._base_url = "https://fake-gateway.example.com"
    model._provider = "openai"
    model._builder = __import__(
        "financebench.model", fromlist=["_build_openai_request"]
    )._build_openai_request
    model._client = MagicMock(spec=httpx.Client)
    return model


def _ok_response(content: str = "hello world") -> MagicMock:
    """Create a mock httpx.Response with 200 status and OpenAI JSON."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    resp.request = MagicMock()
    return resp


def _error_response(status_code: int, text: str = "error") -> MagicMock:
    """Create a mock httpx.Response with an error status."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text
    resp.request = MagicMock()
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        f"{status_code}: {text}",
        request=resp.request,
        response=resp,
    )
    return resp


class TestSampleText:
    @patch("financebench.model.time.sleep")
    def test_successful_call(self, mock_sleep):
        model = _make_model()
        model._client.post.return_value = _ok_response("hello world")
        result = model.sample_text("test prompt")
        assert result == "hello world"
        model._client.post.assert_called_once()

    @patch("financebench.model.time.sleep")
    def test_empty_choices_returns_empty(self, mock_sleep):
        model = _make_model()
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        resp.json.return_value = {"choices": []}
        resp.request = MagicMock()
        model._client.post.return_value = resp
        result = model.sample_text("test")
        assert result == ""

    @patch("financebench.model.time.sleep")
    def test_retries_on_rate_limit(self, mock_sleep):
        model = _make_model()
        rate_limit = _error_response(429, "rate limited")
        ok = _ok_response("success after retry")
        model._client.post.side_effect = [rate_limit, rate_limit, ok]
        result = model.sample_text("test")
        assert result == "success after retry"
        assert model._client.post.call_count == 3

    @patch("financebench.model.time.sleep")
    def test_retries_on_server_error(self, mock_sleep):
        model = _make_model()
        server_err = _error_response(500, "internal error")
        ok = _ok_response("recovered")
        model._client.post.side_effect = [server_err, ok]
        result = model.sample_text("test")
        assert result == "recovered"

    @patch("financebench.model.time.sleep")
    def test_retries_on_timeout(self, mock_sleep):
        model = _make_model()
        model._client.post.side_effect = [
            httpx.ReadTimeout("timeout"),
            _ok_response("after timeout"),
        ]
        result = model.sample_text("test")
        assert result == "after timeout"

    @patch("financebench.model.time.sleep")
    def test_retries_on_connect_error(self, mock_sleep):
        model = _make_model()
        model._client.post.side_effect = [
            httpx.ConnectError("connection refused"),
            _ok_response("reconnected"),
        ]
        result = model.sample_text("test")
        assert result == "reconnected"

    @patch("financebench.model.time.sleep")
    def test_exhausts_retries_then_raises(self, mock_sleep):
        model = _make_model()
        err_resp = _error_response(500, "server error")
        model._client.post.return_value = err_resp
        with pytest.raises(httpx.HTTPStatusError):
            model.sample_text("test")
        assert model._client.post.call_count == _MAX_RETRIES

    @patch("financebench.model.time.sleep")
    def test_non_retryable_fails_immediately(self, mock_sleep):
        model = _make_model()
        err_resp = _error_response(401, "unauthorized")
        model._client.post.return_value = err_resp
        with pytest.raises(httpx.HTTPStatusError):
            model.sample_text("test")
        # Should fail on first attempt, no retries
        assert model._client.post.call_count == 1

    @patch("financebench.model.time.sleep")
    def test_exponential_backoff(self, mock_sleep):
        model = _make_model()
        err_resp = _error_response(429, "rate limited")
        ok = _ok_response("ok")
        model._client.post.side_effect = [
            err_resp, err_resp, err_resp, ok
        ]
        model.sample_text("test")
        # Backoff sleeps (not counting the inter-call delay)
        backoff_sleeps = [
            call.args[0]
            for call in mock_sleep.call_args_list
            if call.args[0] > 0.5  # Filter out inter-call delays
        ]
        assert len(backoff_sleeps) == 3
        # Should be exponential: 2.0, 4.0, 8.0
        assert backoff_sleeps[0] == pytest.approx(2.0)
        assert backoff_sleeps[1] == pytest.approx(4.0)
        assert backoff_sleeps[2] == pytest.approx(8.0)


class TestSampleChoice:
    @patch("financebench.model.time.sleep")
    def test_exact_match(self, mock_sleep):
        model = _make_model()
        model._client.post.return_value = _ok_response("option_b")
        idx, resp, info = model.sample_choice(
            "pick one", ["option_a", "option_b", "option_c"]
        )
        assert idx == 1
        assert resp == "option_b"

    @patch("financebench.model.time.sleep")
    def test_substring_fallback(self, mock_sleep):
        model = _make_model()
        model._client.post.return_value = _ok_response(
            "I choose option_b because..."
        )
        idx, resp, _ = model.sample_choice(
            "pick one", ["option_a", "option_b"]
        )
        assert idx == 1
        assert resp == "option_b"

    @patch("financebench.model.time.sleep")
    def test_unbound_answer_does_not_crash(self, mock_sleep):
        """If all attempts throw, should still raise cleanly."""
        model = _make_model()
        model._client.post.side_effect = httpx.ReadTimeout("boom")
        from concordia.language_model import language_model
        with pytest.raises(language_model.InvalidResponseError):
            model.sample_choice("pick one", ["a", "b"])


class TestProviderDetection:
    def test_openai_models(self):
        from financebench.model import detect_provider, PROVIDER_OPENAI
        assert detect_provider("gpt-4o") == PROVIDER_OPENAI
        assert detect_provider("gpt-4.1") == PROVIDER_OPENAI
        assert detect_provider("o3") == PROVIDER_OPENAI

    def test_anthropic_models(self):
        from financebench.model import detect_provider, PROVIDER_ANTHROPIC
        assert detect_provider("claude-opus-4-6") == PROVIDER_ANTHROPIC
        assert detect_provider("claude-sonnet-4-5") == PROVIDER_ANTHROPIC

    def test_google_models(self):
        from financebench.model import detect_provider, PROVIDER_GOOGLE
        assert detect_provider("gemini-3-pro-preview") == PROVIDER_GOOGLE


class TestRetryableStatusCodes:
    def test_retryable_codes_are_correct(self):
        assert 429 in _RETRYABLE_STATUS_CODES  # rate limit
        assert 500 in _RETRYABLE_STATUS_CODES  # server error
        assert 502 in _RETRYABLE_STATUS_CODES  # bad gateway
        assert 503 in _RETRYABLE_STATUS_CODES  # service unavailable
        assert 504 in _RETRYABLE_STATUS_CODES  # gateway timeout

    def test_auth_errors_not_retryable(self):
        assert 401 not in _RETRYABLE_STATUS_CODES
        assert 403 not in _RETRYABLE_STATUS_CODES
