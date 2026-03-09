"""Tests for strot_ai.pages."""
import json
from strot_ai.pages import (
    Block, KPI, Chart, Table, Text, StatGrid, ProgressList,
    Row, Dashboard, build_page,
)
from strot_ai.decorators import page


class TestKPI:
    def test_simple_variant(self):
        k = KPI(query_id=1, label="Revenue")
        d = k.to_dict()
        assert d["type"] == "kpi_card_simple"
        assert d["span"] == 3
        assert d["label"] == "Revenue"

    def test_with_change_variant(self):
        k = KPI(query_id=1, label="Revenue", change_field="change")
        assert k.to_dict()["type"] == "kpi_card_with_change"

    def test_with_sparkline_variant(self):
        k = KPI(query_id=1, label="Revenue", trend_field="sparkline")
        assert k.to_dict()["type"] == "kpi_card_with_sparkline"

    def test_with_progress_variant(self):
        k = KPI(query_id=1, label="Goal", target_field="target")
        assert k.to_dict()["type"] == "kpi_card_with_progress"

    def test_sparkline_takes_precedence(self):
        k = KPI(query_id=1, label="R", trend_field="spark", change_field="ch")
        assert k.to_dict()["type"] == "kpi_card_with_sparkline"

    def test_format_field(self):
        k = KPI(query_id=1, label="Revenue", format="currency")
        assert k.to_dict()["format"] == "currency"


class TestChart:
    def test_line_chart(self):
        c = Chart(query_id=1, type="line", title="Trend")
        d = c.to_dict()
        assert d["type"] == "line_chart"
        assert d["span"] == 6
        assert d["title"] == "Trend"

    def test_bar_chart(self):
        c = Chart(type="bar")
        assert c.to_dict()["type"] == "bar_chart_vertical"

    def test_donut_chart(self):
        c = Chart(type="donut")
        assert c.to_dict()["type"] == "donut_chart"

    def test_pie_maps_to_donut(self):
        c = Chart(type="pie")
        assert c.to_dict()["type"] == "donut_chart"

    def test_area_chart(self):
        c = Chart(type="area")
        assert c.to_dict()["type"] == "area_chart_stacked"

    def test_scatter_chart(self):
        c = Chart(type="scatter")
        assert c.to_dict()["type"] == "scatter_chart"

    def test_funnel_chart(self):
        c = Chart(type="funnel")
        assert c.to_dict()["type"] == "funnel_chart"

    def test_custom_span(self):
        c = Chart(type="line", span=8)
        assert c.to_dict()["span"] == 8


class TestTable:
    def test_simple_variant(self):
        t = Table(query_id=1, title="Orders")
        d = t.to_dict()
        assert d["type"] == "data_table_simple"
        assert d["span"] == 12
        assert d["sortable"] is True

    def test_with_status_variant(self):
        t = Table(query_id=1, title="Orders", status_field="status")
        assert t.to_dict()["type"] == "data_table_with_status"

    def test_pagination(self):
        t = Table(query_id=1, paginated=True, page_size=50)
        d = t.to_dict()
        assert d["paginated"] is True
        assert d["page_size"] == 50


class TestText:
    def test_static_content(self):
        t = Text(content="Hello world", title="Greeting")
        d = t.to_dict()
        assert d["type"] == "summary_text"
        assert d["content"] == "Hello world"

    def test_query_based(self):
        t = Text(query_id=1, title="Summary")
        assert t.to_dict()["query_id"] == 1


class TestStatGrid:
    def test_stats(self):
        s = StatGrid(stats=[{"label": "Users", "value": "1000"}])
        d = s.to_dict()
        assert d["type"] == "stat_grid"
        assert len(d["stats"]) == 1


class TestProgressList:
    def test_fields(self):
        p = ProgressList(query_id=1, title="Quotas", span=6)
        d = p.to_dict()
        assert d["type"] == "progress_list"
        assert d["name_field"] == "name"
        assert d["value_field"] == "value"
        assert d["target_field"] == "target"


class TestRow:
    def test_to_dict(self):
        r = Row(
            KPI(query_id=1, label="A"),
            KPI(query_id=2, label="B"),
        )
        d = r.to_dict()
        assert d["height"] == "auto"
        assert len(d["columns"]) == 2

    def test_custom_height(self):
        r = Row(KPI(query_id=1, label="A"), height="350px")
        assert r.to_dict()["height"] == "350px"


class TestDashboard:
    def test_to_dict_structure(self):
        d = Dashboard(
            Row(KPI(query_id=1, label="Rev")),
            Row(Chart(query_id=2, type="line", title="Trend")),
        )
        result = d.to_dict()
        assert "layout" in result
        assert len(result["layout"]["rows"]) == 2

    def test_to_json_valid(self):
        d = Dashboard(Row(KPI(query_id=1, label="Rev")))
        parsed = json.loads(d.to_json())
        assert "layout" in parsed

    def test_with_title(self):
        d = Dashboard(title="Sales Dashboard")
        assert d.to_dict()["title"] == "Sales Dashboard"

    def test_empty_dashboard(self):
        d = Dashboard()
        result = d.to_dict()
        assert result["layout"]["rows"] == []


class TestBuildPage:
    def test_builds_from_decorated_class(self):
        @page(name="test_dash", description="Test", type="dashboard")
        class TestDash:
            def layout(self):
                return Dashboard(
                    Row(
                        KPI(query_id=1, label="A", span=6),
                        KPI(query_id=2, label="B", span=6),
                    ),
                )

        result = build_page(TestDash)
        assert result["name"] == "test_dash"
        assert result["type"] == "dashboard"
        assert len(result["layout"]["rows"]) == 1

    def test_raises_without_decorator(self):
        class NoDeco:
            pass

        try:
            build_page(NoDeco)
            assert False, "Should have raised"
        except ValueError as e:
            assert "not decorated" in str(e)

    def test_raises_without_layout(self):
        @page(name="no_layout")
        class NoLayout:
            pass

        try:
            build_page(NoLayout)
            assert False, "Should have raised"
        except ValueError as e:
            assert "layout" in str(e)
