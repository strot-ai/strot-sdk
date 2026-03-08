"""Tests for strot_sdk.validation."""
import pytest
from strot_sdk.validation import validate_pipeline_dsl, validate_page_layout, validate_or_raise


class TestValidatePipelineDSL:
    def test_valid_pipeline(self):
        dsl = {
            "name": "test",
            "nodes": [
                {"id": "load", "type": "Data Connector", "data": {"query_id": 1}, "position": {"x": 0, "y": 0}},
                {"id": "transform", "type": "LLM", "data": {"prompt": "clean"}, "position": {"x": 250, "y": 0}},
            ],
            "edges": [
                {"id": "load-transform", "source": "load", "target": "transform"},
            ],
        }
        errors = validate_pipeline_dsl(dsl)
        assert errors == []

    def test_missing_name(self):
        dsl = {"name": "", "nodes": [{"id": "a", "type": "X", "data": {}}], "edges": []}
        errors = validate_pipeline_dsl(dsl)
        assert any("name" in e for e in errors)

    def test_missing_nodes(self):
        dsl = {"name": "test"}
        errors = validate_pipeline_dsl(dsl)
        assert any("nodes" in e for e in errors)

    def test_empty_nodes(self):
        dsl = {"name": "test", "nodes": [], "edges": []}
        errors = validate_pipeline_dsl(dsl)
        assert any("at least one node" in e for e in errors)

    def test_node_missing_id(self):
        dsl = {"name": "test", "nodes": [{"type": "X", "data": {}}], "edges": []}
        errors = validate_pipeline_dsl(dsl)
        assert any("id" in e for e in errors)

    def test_node_missing_type(self):
        dsl = {"name": "test", "nodes": [{"id": "a", "data": {}}], "edges": []}
        errors = validate_pipeline_dsl(dsl)
        assert any("type" in e for e in errors)

    def test_duplicate_node_ids(self):
        dsl = {
            "name": "test",
            "nodes": [
                {"id": "a", "type": "X", "data": {}},
                {"id": "a", "type": "Y", "data": {}},
            ],
            "edges": [],
        }
        errors = validate_pipeline_dsl(dsl)
        assert any("Duplicate" in e for e in errors)

    def test_edge_broken_source(self):
        dsl = {
            "name": "test",
            "nodes": [{"id": "a", "type": "X", "data": {}}],
            "edges": [{"source": "missing", "target": "a"}],
        }
        errors = validate_pipeline_dsl(dsl)
        assert any("source" in e and "missing" in e for e in errors)

    def test_edge_broken_target(self):
        dsl = {
            "name": "test",
            "nodes": [{"id": "a", "type": "X", "data": {}}],
            "edges": [{"source": "a", "target": "missing"}],
        }
        errors = validate_pipeline_dsl(dsl)
        assert any("target" in e and "missing" in e for e in errors)


class TestValidatePageLayout:
    def test_valid_page(self):
        layout = {
            "name": "test",
            "layout": {
                "rows": [
                    {
                        "height": "auto",
                        "columns": [
                            {"type": "kpi_card_simple", "span": 6},
                            {"type": "kpi_card_simple", "span": 6},
                        ],
                    },
                ],
            },
        }
        errors = validate_page_layout(layout)
        assert errors == []

    def test_missing_name(self):
        layout = {"name": "", "layout": {"rows": []}}
        errors = validate_page_layout(layout)
        assert any("name" in e for e in errors)

    def test_missing_layout(self):
        layout = {"name": "test"}
        errors = validate_page_layout(layout)
        assert any("layout" in e for e in errors)

    def test_missing_rows(self):
        layout = {"name": "test", "layout": {}}
        errors = validate_page_layout(layout)
        assert any("rows" in e for e in errors)

    def test_block_missing_type(self):
        layout = {
            "name": "test",
            "layout": {"rows": [{"columns": [{"span": 12}]}]},
        }
        errors = validate_page_layout(layout)
        assert any("type" in e for e in errors)

    def test_block_invalid_span(self):
        layout = {
            "name": "test",
            "layout": {"rows": [{"columns": [{"type": "kpi", "span": 15}]}]},
        }
        errors = validate_page_layout(layout)
        assert any("span" in e for e in errors)

    def test_block_zero_span(self):
        layout = {
            "name": "test",
            "layout": {"rows": [{"columns": [{"type": "kpi", "span": 0}]}]},
        }
        errors = validate_page_layout(layout)
        assert any("span" in e for e in errors)


class TestValidateOrRaise:
    def test_no_errors_passes(self):
        validate_or_raise([], "test")  # Should not raise

    def test_errors_raises(self):
        with pytest.raises(ValueError, match="2 validation error"):
            validate_or_raise(["error one", "error two"], "Pipeline 'x'")

    def test_context_in_message(self):
        with pytest.raises(ValueError, match="My context"):
            validate_or_raise(["bad"], "My context")
