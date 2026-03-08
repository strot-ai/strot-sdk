"""
STROT SDK — Shared Types
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionResult:
    """Result from executing a tool or query."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryResult:
    """Result from a query execution."""
    columns: List[Dict[str, str]] = field(default_factory=list)
    rows: List[Dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    query_id: Optional[int] = None
    data_source_id: Optional[int] = None

    def to_dicts(self) -> List[Dict[str, Any]]:
        """Return rows as list of dicts."""
        return self.rows

    def to_df(self):
        """Return rows as a pandas DataFrame (requires pandas)."""
        try:
            import pandas as pd
            return pd.DataFrame(self.rows, columns=[c.get("name", c.get("friendly_name", "")) for c in self.columns])
        except ImportError:
            raise ImportError("pandas is required: pip install strot-sdk[pandas]")


@dataclass
class DeployResult:
    """Result from deploying a function/agent."""
    success: bool
    id: Optional[int] = None
    name: Optional[str] = None
    url: Optional[str] = None
    action: Optional[str] = None  # "created" or "updated"
    error: Optional[str] = None


@dataclass
class Resource:
    """A STROT platform resource (query, tool, data source)."""
    id: int
    name: str
    type: str  # "query", "tool", "data_source"
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
