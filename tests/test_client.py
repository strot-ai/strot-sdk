"""Tests for strot_ai.client."""
import pytest
import responses
from unittest.mock import patch
from strot_ai.client import StrotClient, StrotAPIError


@pytest.fixture
def client(clean_env):
    """Create a StrotClient with test credentials."""
    return StrotClient(
        url="https://test.strot.ai",
        api_key="sk_test_123",
        org="org-uuid-123",
        max_retries=0,  # Disable retries for most tests
    )


@pytest.fixture
def retry_client(clean_env):
    """Create a StrotClient with retries enabled but fast."""
    return StrotClient(
        url="https://test.strot.ai",
        api_key="sk_test_123",
        org="org-uuid-123",
        max_retries=2,
        retry_base_delay=0.01,  # Fast retries for tests
    )


class TestURLBuilding:
    def test_with_org(self, client):
        url = client._url("/api/queries")
        assert url == "https://test.strot.ai/org-uuid-123/api/queries"

    def test_without_org(self, clean_env):
        c = StrotClient(url="https://test.strot.ai", api_key="sk_test", max_retries=0)
        url = c._url("/api/queries")
        assert url == "https://test.strot.ai/api/queries"

    def test_trailing_slash_stripped(self, clean_env):
        c = StrotClient(url="https://test.strot.ai/", api_key="sk_test", org="org", max_retries=0)
        url = c._url("/api/queries")
        assert url == "https://test.strot.ai/org/api/queries"


class TestAuthHeaders:
    def test_auth_header_set(self, client):
        assert client._session.headers["Authorization"] == "Key sk_test_123"

    def test_content_type_set(self, client):
        assert client._session.headers["Content-Type"] == "application/json"


class TestHTTPMethods:
    @responses.activate
    def test_get(self, client):
        responses.add(
            responses.GET,
            "https://test.strot.ai/org-uuid-123/api/queries",
            json={"results": []},
            status=200,
        )
        result = client.get("/api/queries")
        assert result == {"results": []}

    @responses.activate
    def test_post(self, client):
        responses.add(
            responses.POST,
            "https://test.strot.ai/org-uuid-123/api/arena/llm/complete",
            json={"content": "Hello"},
            status=200,
        )
        result = client.post("/api/arena/llm/complete", data={"prompt": "Hi"})
        assert result == {"content": "Hello"}

    @responses.activate
    def test_204_returns_none(self, client):
        responses.add(
            responses.DELETE,
            "https://test.strot.ai/org-uuid-123/api/something",
            status=204,
        )
        result = client.delete("/api/something")
        assert result is None


class TestErrorHandling:
    @responses.activate
    def test_4xx_raises_immediately(self, client):
        responses.add(
            responses.GET,
            "https://test.strot.ai/org-uuid-123/api/queries",
            json={"message": "Not found"},
            status=404,
        )
        with pytest.raises(StrotAPIError, match="Not found") as exc_info:
            client.get("/api/queries")
        assert exc_info.value.status_code == 404

    @responses.activate
    def test_4xx_no_json_body(self, client):
        responses.add(
            responses.GET,
            "https://test.strot.ai/org-uuid-123/api/queries",
            body="Forbidden",
            status=403,
        )
        with pytest.raises(StrotAPIError, match="Forbidden"):
            client.get("/api/queries")

    @responses.activate
    def test_5xx_raises_without_retry(self, client):
        responses.add(
            responses.GET,
            "https://test.strot.ai/org-uuid-123/api/queries",
            json={"error": "Internal"},
            status=500,
        )
        with pytest.raises(StrotAPIError, match="Internal"):
            client.get("/api/queries")


class TestRetryBehavior:
    @responses.activate
    def test_5xx_retries_then_succeeds(self, retry_client):
        responses.add(responses.GET, "https://test.strot.ai/org-uuid-123/api/test", status=500)
        responses.add(responses.GET, "https://test.strot.ai/org-uuid-123/api/test", json={"ok": True}, status=200)
        result = retry_client.get("/api/test")
        assert result == {"ok": True}
        assert len(responses.calls) == 2

    @responses.activate
    def test_5xx_exhausts_retries(self, retry_client):
        for _ in range(3):
            responses.add(responses.GET, "https://test.strot.ai/org-uuid-123/api/test", status=500)
        with pytest.raises(StrotAPIError):
            retry_client.get("/api/test")
        assert len(responses.calls) == 3  # initial + 2 retries

    @responses.activate
    def test_4xx_no_retry(self, retry_client):
        responses.add(responses.GET, "https://test.strot.ai/org-uuid-123/api/test", status=400)
        with pytest.raises(StrotAPIError):
            retry_client.get("/api/test")
        assert len(responses.calls) == 1  # No retries

    @responses.activate
    def test_connection_error_retries(self, retry_client):
        import requests as req_lib
        responses.add(responses.GET, "https://test.strot.ai/org-uuid-123/api/test",
                       body=req_lib.ConnectionError("refused"))
        responses.add(responses.GET, "https://test.strot.ai/org-uuid-123/api/test",
                       json={"ok": True}, status=200)
        result = retry_client.get("/api/test")
        assert result == {"ok": True}


class TestDeployFunction:
    @responses.activate
    def test_deploy_creates_new(self, client):
        # List returns empty (no existing function)
        responses.add(
            responses.GET,
            "https://test.strot.ai/org-uuid-123/api/arena/code-functions",
            json={"results": []},
        )
        # Create
        responses.add(
            responses.POST,
            "https://test.strot.ai/org-uuid-123/api/arena/code-functions",
            json={"id": 42},
        )
        result = client.deploy_function(name="calc", code="print('hi')")
        assert result.success is True
        assert result.id == 42
        assert result.action == "created"

    @responses.activate
    def test_deploy_updates_existing(self, client):
        # List returns matching function
        responses.add(
            responses.GET,
            "https://test.strot.ai/org-uuid-123/api/arena/code-functions",
            json={"results": [{"id": 10, "name": "calc"}]},
        )
        # Update
        responses.add(
            responses.PUT,
            "https://test.strot.ai/org-uuid-123/api/arena/code-functions/10",
            json={"id": 10},
        )
        result = client.deploy_function(name="calc", code="print('hi')")
        assert result.success is True
        assert result.action == "updated"


class TestDeployOrchestration:
    @responses.activate
    def test_deploy_creates_new(self, client):
        responses.add(
            responses.GET,
            "https://test.strot.ai/org-uuid-123/api/cortex/orchestrations",
            json={"results": []},
        )
        responses.add(
            responses.POST,
            "https://test.strot.ai/org-uuid-123/api/cortex/orchestrations",
            json={"id": 5},
        )
        result = client.deploy_orchestration(name="etl", dsl={"nodes": [], "edges": []})
        assert result.success is True
        assert result.action == "created"


class TestDeployPage:
    @responses.activate
    def test_deploy_creates_new(self, client):
        responses.add(
            responses.GET,
            "https://test.strot.ai/org-uuid-123/api/pages",
            json={"results": []},
        )
        responses.add(
            responses.POST,
            "https://test.strot.ai/org-uuid-123/api/pages",
            json={"id": 7},
        )
        result = client.deploy_page(name="dash", layout={"layout": {"rows": []}})
        assert result.success is True
        assert result.action == "created"


class TestWhoami:
    @responses.activate
    def test_returns_user_info(self, client):
        responses.add(
            responses.GET,
            "https://test.strot.ai/org-uuid-123/api/session",
            json={"user": {"id": 1, "email": "test@x.com", "name": "Test"}},
        )
        info = client.whoami()
        assert info["email"] == "test@x.com"


class TestCheckAuth:
    @responses.activate
    def test_returns_true_when_valid(self, client):
        responses.add(
            responses.GET,
            "https://test.strot.ai/org-uuid-123/api/session",
            json={"user": {"id": 1}},
        )
        assert client.check_auth() is True

    @responses.activate
    def test_returns_false_on_error(self, client):
        responses.add(
            responses.GET,
            "https://test.strot.ai/org-uuid-123/api/session",
            status=401,
        )
        assert client.check_auth() is False
