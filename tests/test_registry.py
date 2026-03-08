"""Tests for strot_sdk.registry."""
import pytest
import responses
from strot_sdk.registry import (
    StrotRegistry, EntityCollection, QueryProxy, ToolProxy, DataSourceProxy,
)


@pytest.fixture
def registry(clean_env):
    """Create a StrotRegistry with test client."""
    return StrotRegistry(url="https://test.strot.ai", api_key="sk_test_123")


class TestQueryProxy:
    def test_properties(self):
        from unittest.mock import MagicMock
        client = MagicMock()
        q = QueryProxy({"id": 1, "name": "sales", "description": "Sales data", "data_source_id": 5}, client)
        assert q.id == 1
        assert q.name == "sales"
        assert q.description == "Sales data"
        assert q.data_source_id == 5

    def test_repr(self):
        from unittest.mock import MagicMock
        q = QueryProxy({"id": 1, "name": "sales"}, MagicMock())
        assert "sales" in repr(q)


class TestToolProxy:
    def test_properties(self):
        from unittest.mock import MagicMock
        t = ToolProxy({"id": 2, "name": "calc", "function_type": "tool"}, MagicMock())
        assert t.id == 2
        assert t.name == "calc"
        assert t.function_type == "tool"


class TestDataSourceProxy:
    def test_properties(self):
        from unittest.mock import MagicMock
        ds = DataSourceProxy({"id": 3, "name": "prod", "type": "pg"}, MagicMock())
        assert ds.id == 3
        assert ds.name == "prod"
        assert ds.type == "pg"


class TestEntityCollection:
    def test_access_by_name(self):
        from unittest.mock import MagicMock
        client = MagicMock()
        loader = lambda: [{"id": 1, "name": "alpha"}, {"id": 2, "name": "beta"}]
        coll = EntityCollection(loader, QueryProxy, client)
        q = coll["alpha"]
        assert q.name == "alpha"

    def test_access_by_id(self):
        from unittest.mock import MagicMock
        client = MagicMock()
        loader = lambda: [{"id": 1, "name": "alpha"}]
        coll = EntityCollection(loader, QueryProxy, client)
        q = coll[1]
        assert q.id == 1

    def test_key_error_on_missing(self):
        from unittest.mock import MagicMock
        loader = lambda: []
        coll = EntityCollection(loader, QueryProxy, MagicMock())
        with pytest.raises(KeyError):
            coll["missing"]

    def test_iteration(self):
        from unittest.mock import MagicMock
        loader = lambda: [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        coll = EntityCollection(loader, QueryProxy, MagicMock())
        names = [q.name for q in coll]
        assert names == ["a", "b"]

    def test_len(self):
        from unittest.mock import MagicMock
        loader = lambda: [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        coll = EntityCollection(loader, QueryProxy, MagicMock())
        assert len(coll) == 2

    def test_contains(self):
        from unittest.mock import MagicMock
        loader = lambda: [{"id": 1, "name": "alpha"}]
        coll = EntityCollection(loader, QueryProxy, MagicMock())
        assert "alpha" in coll
        assert 1 in coll
        assert "beta" not in coll

    def test_reload_clears_cache(self):
        from unittest.mock import MagicMock
        call_count = [0]

        def loader():
            call_count[0] += 1
            return [{"id": 1, "name": f"v{call_count[0]}"}]

        coll = EntityCollection(loader, QueryProxy, MagicMock())
        assert coll[1].name == "v1"
        coll.reload()
        assert coll[1].name == "v2"

    def test_attribute_access(self):
        from unittest.mock import MagicMock
        loader = lambda: [{"id": 1, "name": "alpha"}]
        coll = EntityCollection(loader, QueryProxy, MagicMock())
        q = coll.alpha
        assert q.name == "alpha"

    def test_attribute_error_on_missing(self):
        from unittest.mock import MagicMock
        loader = lambda: []
        coll = EntityCollection(loader, QueryProxy, MagicMock())
        with pytest.raises(AttributeError):
            coll.missing


class TestStrotRegistry:
    @responses.activate
    def test_queries_property(self, registry):
        responses.add(
            responses.GET,
            "https://test.strot.ai/api/queries",
            json={"results": [{"id": 1, "name": "sales"}]},
        )
        q = registry.queries["sales"]
        assert q.name == "sales"

    @responses.activate
    def test_tools_property(self, registry):
        responses.add(
            responses.GET,
            "https://test.strot.ai/api/arena/code-functions",
            json={"results": [{"id": 1, "name": "calc", "function_type": "tool"}]},
        )
        t = registry.tools["calc"]
        assert t.name == "calc"

    @responses.activate
    def test_data_sources_alias(self, registry):
        responses.add(
            responses.GET,
            "https://test.strot.ai/api/data_sources",
            json=[{"id": 1, "name": "prod", "type": "pg"}],
        )
        ds = registry.data_sources["prod"]
        assert ds.name == "prod"
