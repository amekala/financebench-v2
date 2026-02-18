"""Tests for model.py retry logic and error handling."""

from unittest.mock import MagicMock, patch, PropertyMock

import httpx
import openai
import pytest

from financebench.model import (
    ElementLanguageModel,
    _MAX_RETRIES,
    _RETRYABLE_EXCEPTIONS,
)


def _make_model() -> ElementLanguageModel:
    """Create a model with a mocked client."""
    model = ElementLanguageModel.__new__(ElementLanguageModel)
    model._model_name = "test-model"
    model._client = MagicMock()
    return model


def _mock_response(content: str = "hello") -> MagicMock:
    """Create a mock API response."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


class TestSampleText:
    def test_successful_call(self):
        model = _make_model()
        model._client.chat.completions.create.return_value = (
            _mock_response("hello world")
        )
        result = model.sample_text("test prompt")
        assert result == "hello world"

    def test_null_content_returns_empty(self):
        """API can return null content. Should not crash."""
        model = _make_model()
        resp = _mock_response()
        resp.choices[0].message.content = None
        model._client.chat.completions.create.return_value = resp
        result = model.sample_text("test")
        assert result == ""

    def test_empty_choices_returns_empty(self):
        model = _make_model()
        resp = MagicMock()
        resp.choices = []
        model._client.chat.completions.create.return_value = resp
        result = model.sample_text("test")
        assert result == ""

    @patch("financebench.model.time.sleep")
    def test_retries_on_rate_limit(self, mock_sleep):
        model = _make_model()
        # Fail twice with rate limit, then succeed
        model._client.chat.completions.create.side_effect = [
            openai.RateLimitError(
                "rate limited",
                response=MagicMock(status_code=429),
                body=None,
            ),
            openai.RateLimitError(
                "rate limited",
                response=MagicMock(status_code=429),
                body=None,
            ),
            _mock_response("success after retry"),
        ]
        result = model.sample_text("test")
        assert result == "success after retry"
        assert mock_sleep.call_count == 2

    @patch("financebench.model.time.sleep")
    def test_retries_on_connection_error(self, mock_sleep):
        model = _make_model()
        model._client.chat.completions.create.side_effect = [
            openai.APIConnectionError(request=MagicMock()),
            _mock_response("recovered"),
        ]
        result = model.sample_text("test")
        assert result == "recovered"
        assert mock_sleep.call_count == 1

    @patch("financebench.model.time.sleep")
    def test_retries_on_timeout(self, mock_sleep):
        model = _make_model()
        model._client.chat.completions.create.side_effect = [
            httpx.ReadTimeout("timeout"),
            _mock_response("after timeout"),
        ]
        result = model.sample_text("test")
        assert result == "after timeout"

    @patch("financebench.model.time.sleep")
    def test_exhausts_retries_then_raises(self, mock_sleep):
        model = _make_model()
        model._client.chat.completions.create.side_effect = (
            openai.InternalServerError(
                "server error",
                response=MagicMock(status_code=500),
                body=None,
            )
        )
        with pytest.raises(openai.InternalServerError):
            model.sample_text("test")
        assert mock_sleep.call_count == _MAX_RETRIES - 1

    @patch("financebench.model.time.sleep")
    def test_exponential_backoff(self, mock_sleep):
        model = _make_model()
        model._client.chat.completions.create.side_effect = [
            openai.RateLimitError(
                "rate limited",
                response=MagicMock(status_code=429),
                body=None,
            ),
            openai.RateLimitError(
                "rate limited",
                response=MagicMock(status_code=429),
                body=None,
            ),
            openai.RateLimitError(
                "rate limited",
                response=MagicMock(status_code=429),
                body=None,
            ),
            _mock_response("ok"),
        ]
        model.sample_text("test")
        sleeps = [call.args[0] for call in mock_sleep.call_args_list]
        # Should be 1.0, 2.0, 4.0 (exponential)
        assert sleeps[0] == pytest.approx(1.0)
        assert sleeps[1] == pytest.approx(2.0)
        assert sleeps[2] == pytest.approx(4.0)


class TestSampleChoice:
    def test_exact_match(self):
        model = _make_model()
        model._client.chat.completions.create.return_value = (
            _mock_response("option_b")
        )
        idx, resp, info = model.sample_choice(
            "pick one", ["option_a", "option_b", "option_c"]
        )
        assert idx == 1
        assert resp == "option_b"

    def test_substring_fallback(self):
        model = _make_model()
        model._client.chat.completions.create.return_value = (
            _mock_response("I choose option_b because...")
        )
        idx, resp, _ = model.sample_choice(
            "pick one", ["option_a", "option_b"]
        )
        assert idx == 1
        assert resp == "option_b"
