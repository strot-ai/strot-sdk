"""Tests for strot_sdk.destinations."""
import pytest
import responses
from strot_sdk.destinations import EmailDestination, SlackDestination, WebhookDestination


def _make_destination(cls, clean_env):
    """Create a destination with an injected test client."""
    inst = cls()
    from strot_sdk.client import StrotClient
    inst._client = StrotClient(
        url="https://test.strot.ai", api_key="sk_test", max_retries=0,
    )
    return inst


class TestEmailDestination:
    @responses.activate
    def test_send(self, clean_env):
        dest = _make_destination(EmailDestination, clean_env)
        responses.add(
            responses.POST,
            "https://test.strot.ai/api/arena/destinations/email",
            json={"success": True},
        )
        result = dest.send(to="test@x.com", subject="Hi", body="Hello")
        assert result["success"] is True


class TestSlackDestination:
    @responses.activate
    def test_send(self, clean_env):
        dest = _make_destination(SlackDestination, clean_env)
        responses.add(
            responses.POST,
            "https://test.strot.ai/api/arena/destinations/slack",
            json={"success": True},
        )
        result = dest.send(channel="#test", message="Hello")
        assert result["success"] is True


class TestWebhookDestination:
    @responses.activate
    def test_post(self, clean_env):
        dest = _make_destination(WebhookDestination, clean_env)
        responses.add(
            responses.POST,
            "https://test.strot.ai/api/arena/destinations/webhook",
            json={"success": True},
        )
        result = dest.post(url="https://hook.example.com", data={"key": "value"})
        assert result["success"] is True

    @responses.activate
    def test_get(self, clean_env):
        dest = _make_destination(WebhookDestination, clean_env)
        responses.add(
            responses.POST,
            "https://test.strot.ai/api/arena/destinations/webhook",
            json={"success": True},
        )
        result = dest.get(url="https://hook.example.com")
        assert result["success"] is True
