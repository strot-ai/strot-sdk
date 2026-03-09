"""
STROT SDK — Data Access

Query data sources and saved queries via the STROT API.
"""
import logging
from typing import Any, Dict, List, Optional

from .types import QueryResult

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Lazy-load the StrotClient."""
    global _client
    if _client is None:
        from .client import StrotClient
        _client = StrotClient()
    return _client


def query(
    sql: str,
    data_source_id: int,
    params: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Execute SQL and return rows as a list of dicts.

    Args:
        sql: SQL query string
        data_source_id: ID of the data source
        params: Optional query parameters

    Returns:
        List of row dicts

    Example:
        rows = query("SELECT * FROM users LIMIT 10", data_source_id=1)
        for row in rows:
            print(row["name"])
    """
    client = _get_client()
    result = client.execute_sql(data_source_id, sql, params)
    return result.rows


def query_one(
    sql: str,
    data_source_id: int,
    params: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Execute SQL and return the first row, or None.

    Args:
        sql: SQL query string
        data_source_id: ID of the data source
        params: Optional query parameters

    Returns:
        First row as dict, or None
    """
    rows = query(sql, data_source_id, params)
    return rows[0] if rows else None


def query_df(
    sql: str,
    data_source_id: int,
    params: Optional[Dict[str, Any]] = None,
):
    """
    Execute SQL and return a pandas DataFrame.

    Requires: pip install strot-sdk[pandas]

    Args:
        sql: SQL query string
        data_source_id: ID of the data source
        params: Optional query parameters

    Returns:
        pandas DataFrame
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required: pip install strot-sdk[pandas]")

    client = _get_client()
    result = client.execute_sql(data_source_id, sql, params)
    return result.to_df()


def execute_saved_query(
    query_id: int,
    params: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Execute a saved query by ID.

    Args:
        query_id: ID of the saved query
        params: Optional query parameters

    Returns:
        List of row dicts
    """
    client = _get_client()
    result = client.execute_query(query_id, params)
    return result.rows
