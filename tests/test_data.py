"""Tests for strot_sdk.data."""
import pytest
import responses
from strot_sdk.data import query, query_one, execute_saved_query


@pytest.fixture(autouse=True)
def inject_test_client(clean_env):
    """Inject a test client into the data module."""
    import strot_sdk.data as data_mod
    from strot_sdk.client import StrotClient
    data_mod._client = StrotClient(
        url="https://test.strot.ai", api_key="sk_test", max_retries=0,
    )
    yield
    data_mod._client = None


class TestQuery:
    @responses.activate
    def test_returns_rows(self):
        responses.add(
            responses.POST,
            "https://test.strot.ai/api/query_results",
            json={
                "query_result": {
                    "data": {
                        "columns": [{"name": "id"}, {"name": "name"}],
                        "rows": [{"id": 1, "name": "Alice"}],
                    }
                }
            },
        )
        rows = query("SELECT * FROM users", data_source_id=1)
        assert len(rows) == 1
        assert rows[0]["name"] == "Alice"


class TestQueryOne:
    @responses.activate
    def test_returns_first_row(self):
        responses.add(
            responses.POST,
            "https://test.strot.ai/api/query_results",
            json={
                "query_result": {
                    "data": {
                        "columns": [{"name": "id"}],
                        "rows": [{"id": 1}, {"id": 2}],
                    }
                }
            },
        )
        row = query_one("SELECT * FROM users", data_source_id=1)
        assert row["id"] == 1

    @responses.activate
    def test_returns_none_for_empty(self):
        responses.add(
            responses.POST,
            "https://test.strot.ai/api/query_results",
            json={"query_result": {"data": {"columns": [], "rows": []}}},
        )
        row = query_one("SELECT * FROM users WHERE 1=0", data_source_id=1)
        assert row is None


class TestExecuteSavedQuery:
    @responses.activate
    def test_returns_rows(self):
        responses.add(
            responses.POST,
            "https://test.strot.ai/api/query_results",
            json={
                "query_result": {
                    "data": {
                        "columns": [{"name": "total"}],
                        "rows": [{"total": 1000}],
                    }
                }
            },
        )
        rows = execute_saved_query(query_id=42)
        assert rows[0]["total"] == 1000
