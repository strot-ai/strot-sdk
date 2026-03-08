"""Tests for strot_sdk.cortex."""
import json
from strot_sdk.cortex import Flow, Node, Edge, Step, build_pipeline
from strot_sdk.decorators import cortex


class TestNode:
    def test_to_dict(self):
        n = Node(id="load", node_type="Data Connector", data={"query_id": 1})
        d = n.to_dict()
        assert d["id"] == "load"
        assert d["type"] == "Data Connector"
        assert d["data"]["query_id"] == 1
        assert d["data"]["label"] == "load"


class TestEdge:
    def test_to_dict(self):
        e = Edge(source="a", target="b")
        d = e.to_dict()
        assert d["id"] == "a-b"
        assert d["source"] == "a"
        assert d["target"] == "b"
        assert "data" not in d

    def test_with_condition(self):
        e = Edge(source="a", target="b", condition="high")
        d = e.to_dict()
        assert d["data"]["condition"] == "high"


class TestFlowDataConnector:
    def test_creates_node(self):
        flow = Flow()
        step = flow.data_connector("load", query_id=42)
        assert isinstance(step, Step)
        assert step.node_id == "load"
        assert len(flow._nodes) == 1
        assert flow._nodes[0].node_type == "Data Connector"
        assert flow._nodes[0].data["query_id"] == 42

    def test_no_edge_for_first_node(self):
        flow = Flow()
        flow.data_connector("load", query_id=1)
        assert len(flow._edges) == 0


class TestFlowTransform:
    def test_creates_node_and_edge(self):
        flow = Flow()
        data = flow.data_connector("load", query_id=1)
        t = flow.transform(data, prompt="Clean it", model="gpt-4o")
        assert len(flow._nodes) == 2
        assert len(flow._edges) == 1
        assert flow._edges[0].source == "load"
        assert flow._edges[0].target == t.node_id
        assert flow._nodes[1].data["llm_config"]["prompt"] == "Clean it"

    def test_auto_step_id(self):
        flow = Flow()
        data = flow.data_connector("load", query_id=1)
        t = flow.transform(data, prompt="Clean")
        assert t.node_id.startswith("transform_")

    def test_llm_transform_alias(self):
        assert Flow.llm_transform is Flow.transform


class TestFlowArena:
    def test_creates_arena_node(self):
        flow = Flow()
        data = flow.data_connector("load", query_id=1)
        a = flow.arena(data, tool="top_n", parameters={"n": 10})
        assert flow._nodes[1].node_type == "Arena"
        assert flow._nodes[1].data["tool"] == "top_n"


class TestFlowRouter:
    def test_creates_router_with_routes(self):
        flow = Flow()
        data = flow.data_connector("load", query_id=1)
        routes = [
            {"name": "high", "description": "High value"},
            {"name": "low", "description": "Low value"},
        ]
        r = flow.router(data, routes=routes, prompt="Classify by value")
        assert flow._nodes[1].node_type == "Router"
        assert flow._nodes[1].data["routes"] == routes
        assert flow._nodes[1].data["prompt"] == "Classify by value"

    def test_route_creates_conditional_edge(self):
        flow = Flow()
        data = flow.data_connector("load", query_id=1)
        router = flow.router(data, routes=[{"name": "a"}])
        target = flow.transform(router, prompt="Process A")
        flow.route(router, target, condition="a")
        # Should have: load->router, router->target, router->target(condition=a)
        conditional = [e for e in flow._edges if e.condition == "a"]
        assert len(conditional) == 1


class TestFlowGate:
    def test_creates_gate_node(self):
        flow = Flow()
        data = flow.data_connector("load", query_id=1)
        g = flow.gate(data, condition="quality > 0.95", approval_required=True)
        assert flow._nodes[1].node_type == "Gate"
        assert flow._nodes[1].data["approval_required"] is True
        assert flow._nodes[1].data["condition"] == "quality > 0.95"


class TestFlowPublish:
    def test_creates_publish_node(self):
        flow = Flow()
        data = flow.data_connector("load", query_id=1)
        p = flow.publish(data, name="report", destination="slack")
        assert flow._nodes[1].node_type == "Publish"
        assert flow._nodes[1].data["destination"] == "slack"


class TestFlowAction:
    def test_creates_action_node(self):
        flow = Flow()
        data = flow.data_connector("load", query_id=1)
        a = flow.action(data, action_type="send_slack", target="#alerts")
        assert flow._nodes[1].node_type == "Action"
        assert flow._nodes[1].data["action"] == "send_slack"


class TestFlowAIFeeds:
    def test_creates_ai_feeds_node(self):
        flow = Flow()
        data = flow.data_connector("load", query_id=1)
        f = flow.ai_feeds(data, prompt="Generate insights", insight_count=3)
        assert flow._nodes[1].node_type == "AIFeeds"
        assert flow._nodes[1].data["insight_count"] == 3


class TestFlowConnect:
    def test_manual_connect(self):
        flow = Flow()
        a = flow.data_connector("a", query_id=1)
        b = flow.data_connector("b", query_id=2)
        flow.connect(a, b, condition="manual")
        assert len(flow._edges) == 1
        assert flow._edges[0].condition == "manual"


class TestFlowPositions:
    def test_positions_auto_increment(self):
        flow = Flow()
        flow.data_connector("a", query_id=1)
        flow.data_connector("b", query_id=2)
        flow.data_connector("c", query_id=3)
        assert flow._nodes[0].position == {"x": 0, "y": 0}
        assert flow._nodes[1].position == {"x": 250, "y": 0}
        assert flow._nodes[2].position == {"x": 500, "y": 0}


class TestFlowDSL:
    def test_to_dsl_structure(self):
        flow = Flow()
        data = flow.data_connector("load", query_id=1)
        flow.transform(data, prompt="Clean")
        dsl = flow.to_dsl(name="test", description="Test pipeline")
        assert dsl["name"] == "test"
        assert dsl["description"] == "Test pipeline"
        assert len(dsl["nodes"]) == 2
        assert len(dsl["edges"]) == 1

    def test_to_dsl_with_metadata(self):
        flow = Flow()
        flow.data_connector("load", query_id=1)
        dsl = flow.to_dsl(name="test", schedule="0 8 * * *", tags=["etl"])
        assert dsl["metadata"]["schedule"] == "0 8 * * *"
        assert dsl["metadata"]["tags"] == ["etl"]

    def test_to_json_valid(self):
        flow = Flow()
        flow.data_connector("load", query_id=1)
        j = flow.to_json(name="test")
        parsed = json.loads(j)
        assert parsed["name"] == "test"


class TestBuildPipeline:
    def test_builds_from_decorated_class(self):
        @cortex(name="my_etl", description="ETL pipeline")
        class MyETL:
            def build(self, flow: Flow):
                data = flow.data_connector("load", query_id=1)
                flow.publish(data, name="output")

        dsl = build_pipeline(MyETL)
        assert dsl["name"] == "my_etl"
        assert len(dsl["nodes"]) == 2
        assert len(dsl["edges"]) == 1

    def test_raises_without_decorator(self):
        class NoDeco:
            pass

        try:
            build_pipeline(NoDeco)
            assert False, "Should have raised"
        except ValueError as e:
            assert "not decorated" in str(e)

    def test_raises_without_build_method(self):
        @cortex(name="no_build")
        class NoBuild:
            pass

        try:
            build_pipeline(NoBuild)
            assert False, "Should have raised"
        except ValueError as e:
            assert "build" in str(e)
