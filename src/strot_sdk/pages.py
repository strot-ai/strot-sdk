"""
STROT SDK — Pages Builder

Build dashboards and pages in Python. The layout compiles to JSON
that gets deployed to your STROT instance.

Usage:
    from strot_sdk import page
    from strot_sdk.pages import Dashboard, Row, KPI, Chart, Table, Text

    @page(name='sales_dashboard', type='dashboard')
    class SalesDashboard:
        def layout(self):
            return Dashboard(
                Row(
                    KPI(query_id=1, label='Revenue', value_field='total'),
                    KPI(query_id=2, label='Orders', value_field='count'),
                    KPI(query_id=3, label='Customers', value_field='total'),
                ),
                Row(
                    Chart(query_id=4, type='line', title='Revenue Trend', span=8),
                    Chart(query_id=5, type='donut', title='By Region', span=4),
                ),
                Row(
                    Table(query_id=6, title='Top Customers'),
                ),
            )
"""
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ── Block Types ─────────────────────────────────────────────────


class Block:
    """Base class for all page blocks."""

    def __init__(self, block_type: str, span: int = 12, **kwargs):
        self.block_type = block_type
        self.span = span
        self.config = kwargs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.block_type,
            "span": self.span,
            **self.config,
        }


class KPI(Block):
    """
    KPI card block.

    Args:
        query_id: ID of query that provides the value
        label: Display label
        value_field: Column name for the value
        change_field: Column name for change percentage (optional)
        trend_field: Column name for sparkline data (optional)
        target_field: Column name for target/goal (optional)
        format: Value format ('number', 'currency', 'percent')
        span: Grid columns (1-12, default 3)
    """
    def __init__(
        self,
        query_id: Optional[int] = None,
        label: str = "",
        value_field: str = "value",
        change_field: Optional[str] = None,
        trend_field: Optional[str] = None,
        target_field: Optional[str] = None,
        format: str = "number",
        span: int = 3,
        **kwargs,
    ):
        variant = "kpi_card_simple"
        if trend_field:
            variant = "kpi_card_with_sparkline"
        elif target_field:
            variant = "kpi_card_with_progress"
        elif change_field:
            variant = "kpi_card_with_change"

        super().__init__(
            block_type=variant,
            span=span,
            query_id=query_id,
            label=label,
            value_field=value_field,
            change_field=change_field,
            trend_field=trend_field,
            target_field=target_field,
            format=format,
            **kwargs,
        )


class Chart(Block):
    """
    Chart block.

    Args:
        query_id: ID of query that provides the data
        type: Chart type ('line', 'bar', 'area', 'donut', 'scatter', 'stacked_bar', 'stacked_area')
        title: Chart title
        x_field: Column name for x-axis / categories
        y_field: Column name for y-axis / values
        series_field: Column name for series grouping (optional)
        span: Grid columns (1-12, default 6)
    """
    CHART_TYPE_MAP = {
        "line": "line_chart",
        "bar": "bar_chart_vertical",
        "area": "area_chart_stacked",
        "donut": "donut_chart",
        "pie": "donut_chart",
        "scatter": "scatter_chart",
        "stacked_bar": "bar_chart_stacked",
        "stacked_area": "area_chart_stacked",
        "funnel": "funnel_chart",
    }

    def __init__(
        self,
        query_id: Optional[int] = None,
        type: str = "line",
        title: str = "",
        x_field: str = "",
        y_field: str = "",
        series_field: Optional[str] = None,
        span: int = 6,
        **kwargs,
    ):
        block_type = self.CHART_TYPE_MAP.get(type, type)
        super().__init__(
            block_type=block_type,
            span=span,
            query_id=query_id,
            title=title,
            x_field=x_field,
            y_field=y_field,
            series_field=series_field,
            **kwargs,
        )


class Table(Block):
    """
    Data table block.

    Args:
        query_id: ID of query that provides the data
        title: Table title
        columns: List of column names to display (optional, shows all if omitted)
        sortable: Enable sorting
        filterable: Enable filtering
        paginated: Enable pagination
        page_size: Rows per page
        status_field: Column name for status badges (optional)
        span: Grid columns (1-12, default 12)
    """
    def __init__(
        self,
        query_id: Optional[int] = None,
        title: str = "",
        columns: Optional[List[str]] = None,
        sortable: bool = True,
        filterable: bool = False,
        paginated: bool = True,
        page_size: int = 25,
        status_field: Optional[str] = None,
        span: int = 12,
        **kwargs,
    ):
        variant = "data_table_with_status" if status_field else "data_table_simple"
        super().__init__(
            block_type=variant,
            span=span,
            query_id=query_id,
            title=title,
            columns=columns,
            sortable=sortable,
            filterable=filterable,
            paginated=paginated,
            page_size=page_size,
            status_field=status_field,
            **kwargs,
        )


class Text(Block):
    """
    Text/summary block.

    Args:
        content: Text content (or AI-generated from query)
        title: Block title
        query_id: Optional query for AI-generated summaries
        span: Grid columns (1-12, default 12)
    """
    def __init__(
        self,
        content: str = "",
        title: str = "",
        query_id: Optional[int] = None,
        span: int = 12,
        **kwargs,
    ):
        super().__init__(
            block_type="summary_text",
            span=span,
            content=content,
            title=title,
            query_id=query_id,
            **kwargs,
        )


class StatGrid(Block):
    """
    Grid of stat values.

    Args:
        stats: List of stat dicts [{"label": "...", "value": "..."}]
        title: Block title
        span: Grid columns (1-12, default 12)
    """
    def __init__(
        self,
        stats: Optional[List[Dict[str, str]]] = None,
        title: str = "",
        span: int = 12,
        **kwargs,
    ):
        super().__init__(
            block_type="stat_grid",
            span=span,
            stats=stats or [],
            title=title,
            **kwargs,
        )


class ProgressList(Block):
    """
    Progress bars list (e.g., team quotas).

    Args:
        query_id: Query providing the data
        name_field: Column for item names
        value_field: Column for current values
        target_field: Column for target values
        title: Block title
        span: Grid columns (1-12, default 6)
    """
    def __init__(
        self,
        query_id: Optional[int] = None,
        name_field: str = "name",
        value_field: str = "value",
        target_field: str = "target",
        title: str = "",
        span: int = 6,
        **kwargs,
    ):
        super().__init__(
            block_type="progress_list",
            span=span,
            query_id=query_id,
            name_field=name_field,
            value_field=value_field,
            target_field=target_field,
            title=title,
            **kwargs,
        )


# ── Layout ──────────────────────────────────────────────────────


class Row:
    """
    A row of blocks in a dashboard layout.

    Args:
        *blocks: Block instances (KPI, Chart, Table, etc.)
        height: Row height ('auto' or CSS value like '350px')
    """
    def __init__(self, *blocks: Block, height: str = "auto"):
        self.blocks = list(blocks)
        self.height = height

    def to_dict(self) -> Dict[str, Any]:
        return {
            "height": self.height,
            "columns": [block.to_dict() for block in self.blocks],
        }


class Dashboard:
    """
    Dashboard layout composed of rows.

    Args:
        *rows: Row instances containing blocks
        title: Dashboard title (optional, uses @page name by default)
    """
    def __init__(self, *rows: Row, title: str = ""):
        self.rows = list(rows)
        self.title = title

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "layout": {
                "rows": [row.to_dict() for row in self.rows],
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def build_page(cls) -> Dict[str, Any]:
    """
    Build a page layout from a @page decorated class.

    Instantiates the class, calls layout(), and returns the layout dict.
    """
    config = getattr(cls, "_strot_config", None)
    if config is None:
        raise ValueError(f"{cls.__name__} is not decorated with @page")

    instance = cls()
    layout_method = getattr(instance, "layout", None)
    if layout_method is None:
        raise ValueError(f"{cls.__name__} must have a layout(self) method")

    result = layout_method()

    if isinstance(result, Dashboard):
        layout_dict = result.to_dict()
    elif isinstance(result, dict):
        layout_dict = result
    else:
        raise ValueError(f"layout() must return a Dashboard or dict, got {type(result)}")

    layout_dict["name"] = config.name
    layout_dict["description"] = config.description
    layout_dict["type"] = config.type
    layout_dict["public"] = config.public

    from .validation import validate_page_layout, validate_or_raise
    errors = validate_page_layout(layout_dict)
    validate_or_raise(errors, context=f"Page '{config.name}'")

    return layout_dict
