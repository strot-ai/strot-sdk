"""strot resources — List available STROT resources."""
import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.command()
@click.argument("resource_type", required=False, default=None)
def resources(resource_type):
    """List available STROT resources.

    RESOURCE_TYPE can be: queries, datasources, tools, or omit for all.
    """
    from strot_sdk.client import StrotClient

    try:
        client = StrotClient()
    except Exception as e:
        console.print(f"[red]Not authenticated:[/red] {e}")
        console.print("[dim]Run 'strot login' first.[/dim]")
        raise SystemExit(1)

    types_to_show = []
    if resource_type:
        normalized = resource_type.lower().replace("-", "").replace("_", "")
        if normalized in ("queries", "query", "q"):
            types_to_show = ["queries"]
        elif normalized in ("datasources", "datasource", "ds"):
            types_to_show = ["datasources"]
        elif normalized in ("tools", "tool", "functions", "t"):
            types_to_show = ["tools"]
        else:
            console.print(f"[red]Unknown resource type:[/red] {resource_type}")
            console.print("[dim]Valid types: queries, datasources, tools[/dim]")
            raise SystemExit(1)
    else:
        types_to_show = ["queries", "datasources", "tools"]

    for rtype in types_to_show:
        try:
            if rtype == "queries":
                _show_queries(client)
            elif rtype == "datasources":
                _show_data_sources(client)
            elif rtype == "tools":
                _show_tools(client)
        except Exception as e:
            console.print(f"[red]Error listing {rtype}:[/red] {e}")

        if len(types_to_show) > 1:
            console.print()


def _show_queries(client):
    items = client.list_queries()
    table = Table(title="Queries", show_lines=False)
    table.add_column("ID", style="dim", width=6)
    table.add_column("Name", style="bold")
    table.add_column("Data Source", style="dim")

    for item in items:
        ds_id = item.metadata.get("data_source_id", "")
        table.add_row(str(item.id), item.name, str(ds_id) if ds_id else "")

    console.print(table)
    console.print(f"[dim]{len(items)} queries[/dim]")


def _show_data_sources(client):
    items = client.list_data_sources()
    table = Table(title="Data Sources", show_lines=False)
    table.add_column("ID", style="dim", width=6)
    table.add_column("Name", style="bold")
    table.add_column("Type", style="dim")

    for item in items:
        table.add_row(str(item.id), item.name, item.metadata.get("type", ""))

    console.print(table)
    console.print(f"[dim]{len(items)} data sources[/dim]")


def _show_tools(client):
    items = client.list_tools()
    table = Table(title="Tools", show_lines=False)
    table.add_column("ID", style="dim", width=6)
    table.add_column("Name", style="bold")
    table.add_column("Type", style="dim")
    table.add_column("Category", style="dim")

    for item in items:
        table.add_row(
            str(item.id),
            item.name,
            item.metadata.get("function_type", ""),
            item.metadata.get("category", ""),
        )

    console.print(table)
    console.print(f"[dim]{len(items)} tools[/dim]")
