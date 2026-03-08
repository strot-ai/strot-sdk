"""
STROT SDK — DSL Validation

Validates Cortex pipeline DSL and Page layout JSON before deployment.
Returns a list of error strings (empty list = valid).
"""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def validate_pipeline_dsl(dsl: Dict[str, Any]) -> List[str]:
    """Validate a Cortex pipeline DSL dict.

    Returns a list of error messages. Empty list means valid.
    """
    errors = []

    # Name
    if not dsl.get("name"):
        errors.append("Pipeline must have a non-empty 'name'.")

    # Nodes
    nodes = dsl.get("nodes")
    if nodes is None:
        errors.append("Pipeline must have a 'nodes' list.")
        return errors
    if not isinstance(nodes, list):
        errors.append("'nodes' must be a list.")
        return errors
    if len(nodes) == 0:
        errors.append("Pipeline must have at least one node.")

    node_ids = set()
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"Node at index {i} must be a dict.")
            continue

        node_id = node.get("id")
        if not node_id:
            errors.append(f"Node at index {i} must have a non-empty 'id'.")
        elif node_id in node_ids:
            errors.append(f"Duplicate node ID: '{node_id}'.")
        else:
            node_ids.add(node_id)

        if not node.get("type"):
            errors.append(f"Node '{node_id or i}' must have a 'type'.")

        if "data" not in node:
            errors.append(f"Node '{node_id or i}' must have a 'data' field.")

    # Edges
    edges = dsl.get("edges")
    if edges is None:
        errors.append("Pipeline must have an 'edges' list.")
        return errors
    if not isinstance(edges, list):
        errors.append("'edges' must be a list.")
        return errors

    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"Edge at index {i} must be a dict.")
            continue

        source = edge.get("source")
        target = edge.get("target")

        if not source:
            errors.append(f"Edge at index {i} must have a 'source'.")
        elif source not in node_ids:
            errors.append(f"Edge source '{source}' does not reference a valid node.")

        if not target:
            errors.append(f"Edge at index {i} must have a 'target'.")
        elif target not in node_ids:
            errors.append(f"Edge target '{target}' does not reference a valid node.")

    return errors


def validate_page_layout(layout: Dict[str, Any]) -> List[str]:
    """Validate a Page layout dict.

    Returns a list of error messages. Empty list means valid.
    """
    errors = []

    # Name
    if not layout.get("name"):
        errors.append("Page must have a non-empty 'name'.")

    # Layout structure
    layout_inner = layout.get("layout")
    if layout_inner is None:
        errors.append("Page must have a 'layout' dict.")
        return errors
    if not isinstance(layout_inner, dict):
        errors.append("'layout' must be a dict.")
        return errors

    rows = layout_inner.get("rows")
    if rows is None:
        errors.append("Layout must have a 'rows' list.")
        return errors
    if not isinstance(rows, list):
        errors.append("'rows' must be a list.")
        return errors

    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"Row at index {i} must be a dict.")
            continue

        columns = row.get("columns")
        if columns is None:
            errors.append(f"Row {i + 1} must have a 'columns' list.")
            continue
        if not isinstance(columns, list):
            errors.append(f"Row {i + 1} 'columns' must be a list.")
            continue

        total_span = 0
        for j, block in enumerate(columns):
            if not isinstance(block, dict):
                errors.append(f"Row {i + 1}, block {j + 1} must be a dict.")
                continue

            if not block.get("type"):
                errors.append(f"Row {i + 1}, block {j + 1} must have a 'type'.")

            span = block.get("span")
            if span is None:
                errors.append(f"Row {i + 1}, block {j + 1} must have a 'span'.")
            elif not isinstance(span, int) or span < 1 or span > 12:
                errors.append(f"Row {i + 1}, block {j + 1} span must be between 1 and 12, got {span}.")
            else:
                total_span += span

        if columns and total_span != 12:
            logger.warning(f"Row {i + 1} spans sum to {total_span} (expected 12).")

    return errors


def validate_or_raise(errors: List[str], context: str = "") -> None:
    """Raise ValueError if there are validation errors."""
    if errors:
        prefix = f"{context}: " if context else ""
        msg = f"{prefix}{len(errors)} validation error(s):\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(msg)
