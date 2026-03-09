"""Tests for strot_ai.types."""
from strot_ai.types import ExecutionResult, QueryResult, DeployResult, Resource


class TestExecutionResult:
    def test_success(self):
        r = ExecutionResult(success=True, data={"key": "value"})
        assert r.success is True
        assert r.data == {"key": "value"}
        assert r.error is None
        assert r.metadata == {}

    def test_failure(self):
        r = ExecutionResult(success=False, error="Something broke")
        assert r.success is False
        assert r.error == "Something broke"


class TestQueryResult:
    def test_to_dicts(self):
        r = QueryResult(
            columns=[{"name": "id"}, {"name": "name"}],
            rows=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            row_count=2,
        )
        assert r.to_dicts() == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    def test_empty_result(self):
        r = QueryResult()
        assert r.columns == []
        assert r.rows == []
        assert r.row_count == 0
        assert r.to_dicts() == []


class TestDeployResult:
    def test_created(self):
        r = DeployResult(success=True, id=42, name="my-tool", action="created")
        assert r.success is True
        assert r.id == 42
        assert r.action == "created"

    def test_failed(self):
        r = DeployResult(success=False, error="Deploy failed")
        assert r.success is False
        assert r.error == "Deploy failed"


class TestResource:
    def test_fields(self):
        r = Resource(id=1, name="monthly_sales", type="query", description="Sales data")
        assert r.id == 1
        assert r.name == "monthly_sales"
        assert r.type == "query"
        assert r.metadata == {}
