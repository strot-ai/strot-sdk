"""
STROT SDK — Cortex Pipeline Builder

Build Cortex pipelines in Python. The pipeline compiles to JSON DSL
that gets deployed to your STROT instance.

Usage:
    from strot_ai import cortex
    from strot_ai.cortex import Flow

    @cortex(name='daily_etl', description='Daily ETL pipeline', schedule='0 8 * * *')
    class DailyETL:
        def build(self, flow: Flow):
            data = flow.data_connector('load_sales', query_id=42)
            cleaned = flow.transform(data, prompt='Clean and normalize the data')
            enriched = flow.llm_transform(cleaned, prompt='Categorize each order', model='gpt-4o')
            flow.publish(enriched, name='daily_report', destination='slack', channel='#data')
"""
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Node:
    """A node in a Cortex pipeline."""
    id: str
    node_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.node_type,
            "position": self.position,
            "data": {"label": self.id, **self.data},
        }


@dataclass
class Edge:
    """A connection between two nodes."""
    source: str
    target: str
    condition: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "id": f"{self.source}-{self.target}",
            "source": self.source,
            "target": self.target,
        }
        if self.condition:
            d["data"] = {"condition": self.condition}
        return d


class Step:
    """
    A step reference returned by flow builder methods.
    Used to chain steps together.
    """
    def __init__(self, node_id: str, flow: "Flow"):
        self.node_id = node_id
        self._flow = flow

    def __repr__(self):
        return f"Step('{self.node_id}')"


class Flow:
    """
    Fluent pipeline builder. Use inside a @cortex class's build() method.

    Each method adds a node and connects it to the previous step.
    """

    def __init__(self):
        self._nodes: List[Node] = []
        self._edges: List[Edge] = []
        self._node_count = 0

    def _add_node(self, node_id: str, node_type: str, data: Dict, after: Optional[Step] = None) -> Step:
        x = self._node_count * 250
        node = Node(id=node_id, node_type=node_type, data=data, position={"x": x, "y": 0})
        self._nodes.append(node)
        self._node_count += 1

        if after is not None:
            self._edges.append(Edge(source=after.node_id, target=node_id))

        return Step(node_id, self)

    # ── Data Input ──────────────────────────────────────────────

    def data_connector(
        self,
        step_id: str,
        query_id: Optional[int] = None,
        query_name: Optional[str] = None,
        **kwargs,
    ) -> Step:
        """
        Add a data connector node (loads data from a saved query).

        Args:
            step_id: Unique step name
            query_id: ID of the saved query
            query_name: Name of the saved query (alternative to query_id)
        """
        data = {}
        if query_id is not None:
            data["query_id"] = query_id
        if query_name:
            data["query_name"] = query_name
        data.update(kwargs)
        return self._add_node(step_id, "Data Connector", data)

    # ── Transform ───────────────────────────────────────────────

    def transform(
        self,
        after: Step,
        step_id: Optional[str] = None,
        prompt: str = "",
        operation: str = "transform",
        model: str = "gpt-4o",
        **kwargs,
    ) -> Step:
        """
        Add an LLM transform node.

        Args:
            after: Previous step to connect from
            step_id: Unique step name (auto-generated if omitted)
            prompt: LLM instruction for the transformation
            operation: Operation type (transform, merge, lookup, append, exclude)
            model: LLM model to use
        """
        sid = step_id or f"transform_{self._node_count}"
        data = {
            "llm_config": {
                "prompt": prompt,
                "model": model,
                "operation_type": operation,
            },
            "execute_transform": True,
        }
        data.update(kwargs)
        return self._add_node(sid, "LLM", data, after=after)

    # Alias
    llm_transform = transform

    # ── Arena Tool ──────────────────────────────────────────────

    def arena(
        self,
        after: Step,
        tool: str,
        step_id: Optional[str] = None,
        parameters: Optional[Dict] = None,
        **kwargs,
    ) -> Step:
        """
        Add an Arena tool node.

        Args:
            after: Previous step
            tool: Arena tool name (e.g., 'top_n', 'filter')
            step_id: Unique step name
            parameters: Tool parameters
        """
        sid = step_id or f"arena_{self._node_count}"
        data = {"tool": tool, "parameters": parameters or {}}
        data.update(kwargs)
        return self._add_node(sid, "Arena", data, after=after)

    # ── Router ──────────────────────────────────────────────────

    def router(
        self,
        after: Step,
        routes: List[Dict[str, str]],
        step_id: Optional[str] = None,
        prompt: Optional[str] = None,
        condition: Optional[str] = None,
        default_route: Optional[str] = None,
        **kwargs,
    ) -> Step:
        """
        Add a router node for conditional branching.

        Args:
            after: Previous step
            routes: List of route defs [{"name": "...", "description": "..."}]
            step_id: Unique step name
            prompt: LLM prompt for routing (LLM-based routing)
            condition: Static condition expression
            default_route: Default route name
        """
        sid = step_id or f"router_{self._node_count}"
        data = {"routes": routes}
        if prompt:
            data["prompt"] = prompt
        if condition:
            data["condition"] = condition
        if default_route:
            data["default_route"] = default_route
        data.update(kwargs)
        return self._add_node(sid, "Router", data, after=after)

    def route(self, router_step: Step, target_step: Step, condition: str) -> None:
        """Connect a router to a target step with a condition."""
        self._edges.append(Edge(
            source=router_step.node_id,
            target=target_step.node_id,
            condition=condition,
        ))

    # ── Gate ────────────────────────────────────────────────────

    def gate(
        self,
        after: Step,
        step_id: Optional[str] = None,
        condition: Optional[str] = None,
        approval_required: bool = False,
        approvers: Optional[List[str]] = None,
        timeout: int = 3600,
        **kwargs,
    ) -> Step:
        """
        Add a gate node (approval or quality check).

        Args:
            after: Previous step
            step_id: Unique step name
            condition: Quality condition (e.g., 'quality_score > 0.95')
            approval_required: Whether human approval is needed
            approvers: List of approver roles/names
            timeout: Timeout in seconds
        """
        sid = step_id or f"gate_{self._node_count}"
        data = {
            "approval_required": approval_required,
            "timeout": timeout,
        }
        if condition:
            data["condition"] = condition
        if approvers:
            data["approvers"] = approvers
        data.update(kwargs)
        return self._add_node(sid, "Gate", data, after=after)

    # ── Publish ─────────────────────────────────────────────────

    def publish(
        self,
        after: Step,
        name: str = "",
        step_id: Optional[str] = None,
        destination: Optional[str] = None,
        format: str = "json",
        **kwargs,
    ) -> Step:
        """
        Add a publish/output node.

        Args:
            after: Previous step
            name: Output name
            step_id: Unique step name
            destination: Where to publish (slack, email, s3, database)
            format: Output format (json, csv, html)
        """
        sid = step_id or f"publish_{self._node_count}"
        data = {"name": name, "format": format}
        if destination:
            data["destination"] = destination
        data.update(kwargs)
        return self._add_node(sid, "Publish", data, after=after)

    # ── Action ──────────────────────────────────────────────────

    def action(
        self,
        after: Step,
        action_type: str,
        target: str = "",
        step_id: Optional[str] = None,
        parameters: Optional[Dict] = None,
        **kwargs,
    ) -> Step:
        """
        Add an action node (notifications, triggers).

        Args:
            after: Previous step
            action_type: Action to perform (send_slack, send_email, call_webhook, trigger_cortex)
            target: Target channel/email/URL
            step_id: Unique step name
            parameters: Action parameters
        """
        sid = step_id or f"action_{self._node_count}"
        data = {
            "action": action_type,
            "target": target,
            "parameters": parameters or {},
        }
        data.update(kwargs)
        return self._add_node(sid, "Action", data, after=after)

    # ── AI Feeds ────────────────────────────────────────────────

    def ai_feeds(
        self,
        after: Step,
        prompt: str,
        step_id: Optional[str] = None,
        insight_count: int = 5,
        model: str = "gpt-4o",
        **kwargs,
    ) -> Step:
        """
        Add an AI feeds node (generate insights from data).

        Args:
            after: Previous step
            prompt: Instruction for insight generation
            step_id: Unique step name
            insight_count: Number of insights to generate
            model: LLM model
        """
        sid = step_id or f"insights_{self._node_count}"
        data = {
            "prompt": prompt,
            "insight_count": insight_count,
            "model": model,
        }
        data.update(kwargs)
        return self._add_node(sid, "AIFeeds", data, after=after)

    # ── Connect ─────────────────────────────────────────────────

    def connect(self, source: Step, target: Step, condition: Optional[str] = None) -> None:
        """Manually connect two steps."""
        self._edges.append(Edge(
            source=source.node_id,
            target=target.node_id,
            condition=condition,
        ))

    # ── DSL Output ──────────────────────────────────────────────

    def to_dsl(
        self,
        name: str = "",
        description: str = "",
        schedule: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Compile the pipeline to Cortex JSON DSL."""
        dsl = {
            "name": name,
            "description": description,
            "nodes": [n.to_dict() for n in self._nodes],
            "edges": [e.to_dict() for e in self._edges],
        }
        metadata = {}
        if schedule:
            metadata["schedule"] = schedule
        if tags:
            metadata["tags"] = tags
        if metadata:
            dsl["metadata"] = metadata
        return dsl

    def to_json(self, **kwargs) -> str:
        """Compile to JSON string."""
        return json.dumps(self.to_dsl(**kwargs), indent=2)


def build_pipeline(cls) -> Dict[str, Any]:
    """
    Build a pipeline from a @cortex decorated class.

    Instantiates the class, calls build(flow), and returns the DSL.
    """
    config = getattr(cls, "_strot_config", None)
    if config is None:
        raise ValueError(f"{cls.__name__} is not decorated with @cortex")

    instance = cls()
    flow = Flow()

    build_method = getattr(instance, "build", None)
    if build_method is None:
        raise ValueError(f"{cls.__name__} must have a build(self, flow) method")

    build_method(flow)

    dsl = flow.to_dsl(
        name=config.name,
        description=config.description,
    )

    from .validation import validate_pipeline_dsl, validate_or_raise
    errors = validate_pipeline_dsl(dsl)
    validate_or_raise(errors, context=f"Pipeline '{config.name}'")

    return dsl
