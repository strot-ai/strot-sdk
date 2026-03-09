"""
STROT SDK — Registry

Typed access to STROT platform resources (queries, tools, data sources).
Uses lazy loading via the StrotClient HTTP API.
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class QueryProxy:
    """Lazy wrapper around a saved query."""

    def __init__(self, query_data: Dict[str, Any], client):
        self._data = query_data
        self._client = client

    @property
    def id(self) -> int:
        return self._data["id"]

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    @property
    def description(self) -> str:
        return self._data.get("description", "")

    @property
    def data_source_id(self) -> Optional[int]:
        return self._data.get("data_source_id")

    def execute(self, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute this query and return rows."""
        result = self._client.execute_query(self.id, params)
        return result.rows

    def __repr__(self) -> str:
        return f"QueryProxy(id={self.id}, name='{self.name}')"


class ToolProxy:
    """Lazy wrapper around a deployed tool."""

    def __init__(self, tool_data: Dict[str, Any], client):
        self._data = tool_data
        self._client = client

    @property
    def id(self) -> int:
        return self._data["id"]

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    @property
    def description(self) -> str:
        return self._data.get("description", "")

    @property
    def function_type(self) -> str:
        return self._data.get("function_type", "tool")

    def run(self, **kwargs) -> Any:
        """Execute this tool with parameters."""
        result = self._client.post(
            f"/api/arena/code-functions/{self.id}/execute",
            data={"params": kwargs},
        )
        return result

    def __repr__(self) -> str:
        return f"ToolProxy(id={self.id}, name='{self.name}')"


class DataSourceProxy:
    """Lazy wrapper around a data source."""

    def __init__(self, ds_data: Dict[str, Any], client):
        self._data = ds_data
        self._client = client

    @property
    def id(self) -> int:
        return self._data["id"]

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    @property
    def type(self) -> str:
        return self._data.get("type", "")

    def query(self, sql: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute SQL against this data source."""
        result = self._client.execute_sql(self.id, sql, params)
        return result.rows

    def query_df(self, sql: str, params: Optional[Dict] = None):
        """Execute SQL and return a pandas DataFrame."""
        result = self._client.execute_sql(self.id, sql, params)
        return result.to_df()

    def __repr__(self) -> str:
        return f"DataSourceProxy(id={self.id}, name='{self.name}')"


class EntityCollection:
    """
    Lazy-loaded collection of platform entities.

    Supports dict-like access by name and iteration.

    Usage:
        queries = strot.queries
        q = queries['monthly_sales']   # Access by name
        q = queries[42]                # Access by ID
        for q in queries:              # Iterate
            print(q.name)
    """

    def __init__(self, loader, proxy_class, client):
        self._loader = loader
        self._proxy_class = proxy_class
        self._client = client
        self._items: Optional[List] = None
        self._by_name: Optional[Dict[str, Any]] = None
        self._by_id: Optional[Dict[int, Any]] = None

    def _ensure_loaded(self):
        if self._items is None:
            raw_items = self._loader()
            self._items = [self._proxy_class(item, self._client) for item in raw_items]
            self._by_name = {item.name: item for item in self._items}
            self._by_id = {item.id: item for item in self._items}

    def reload(self):
        """Force reload from API."""
        self._items = None
        self._by_name = None
        self._by_id = None

    def __getitem__(self, key):
        self._ensure_loaded()
        if isinstance(key, int):
            if key in self._by_id:
                return self._by_id[key]
            raise KeyError(f"No item with ID {key}")
        if isinstance(key, str):
            if key in self._by_name:
                return self._by_name[key]
            raise KeyError(f"No item named '{key}'")
        raise TypeError(f"Key must be str or int, got {type(key)}")

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"No item named '{name}'")

    def __iter__(self):
        self._ensure_loaded()
        return iter(self._items)

    def __len__(self):
        self._ensure_loaded()
        return len(self._items)

    def __contains__(self, key):
        self._ensure_loaded()
        if isinstance(key, int):
            return key in self._by_id
        return key in self._by_name

    def __repr__(self):
        self._ensure_loaded()
        return f"EntityCollection({len(self._items)} items)"


class StrotRegistry:
    """
    Main registry providing typed access to STROT resources.

    Usage:
        from strot_ai import strot

        # Access queries
        q = strot.queries['monthly_sales']
        rows = q.execute()

        # Access data sources
        ds = strot.dataSources['production']
        rows = ds.query("SELECT * FROM users LIMIT 10")

        # Access tools
        tool = strot.tools['calculate_roi']
        result = tool.run(cost=1000, revenue=1500)
    """

    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None):
        from .client import StrotClient
        self._client = StrotClient(url=url, api_key=api_key)
        self._queries = None
        self._tools = None
        self._data_sources = None

    @property
    def queries(self) -> EntityCollection:
        if self._queries is None:
            self._queries = EntityCollection(
                loader=self._load_queries,
                proxy_class=QueryProxy,
                client=self._client,
            )
        return self._queries

    @property
    def tools(self) -> EntityCollection:
        if self._tools is None:
            self._tools = EntityCollection(
                loader=self._load_tools,
                proxy_class=ToolProxy,
                client=self._client,
            )
        return self._tools

    @property
    def dataSources(self) -> EntityCollection:
        if self._data_sources is None:
            self._data_sources = EntityCollection(
                loader=self._load_data_sources,
                proxy_class=DataSourceProxy,
                client=self._client,
            )
        return self._data_sources

    # Alias
    data_sources = dataSources

    def _load_queries(self) -> List[Dict]:
        data = self._client.get("/api/queries")
        return data.get("results", data) if isinstance(data, dict) else data

    def _load_tools(self) -> List[Dict]:
        data = self._client.get("/api/arena/code-functions")
        return data.get("results", data) if isinstance(data, dict) else data

    def _load_data_sources(self) -> List[Dict]:
        return self._client.get("/api/data_sources")

    def reload(self) -> None:
        """Force reload all collections."""
        if self._queries:
            self._queries.reload()
        if self._tools:
            self._tools.reload()
        if self._data_sources:
            self._data_sources.reload()


# Default registry instance (uses ~/.strot/credentials)
strot = StrotRegistry()
