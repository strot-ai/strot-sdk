"""strot test — Test a STROT project locally."""
import click
import sys
from pathlib import Path
from rich.console import Console

console = Console()


@click.command()
@click.option("--mock", is_flag=True, help="Run with mocked STROT data")
@click.option("--params", "-p", multiple=True, help="Parameters as key=value pairs")
def test(mock, params):
    """Run the current project locally against a STROT instance.

    Reads strot.yaml, imports the entry file, finds the decorated class,
    and executes it with optional parameters.
    """
    from strot_cli.project import find_project_root, load_project_config, read_project_files

    root = find_project_root()
    if not root:
        console.print("[red]No strot.yaml found.[/red] Run 'strot init' to create a project.")
        raise SystemExit(1)

    config = load_project_config(root)
    console.print(f"[bold]Testing:[/bold] {config['name']} ({config['type']})")
    console.print()

    # Parse parameters
    run_params = {}
    for p in params:
        if "=" in p:
            key, value = p.split("=", 1)
            # Try to parse as number
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
            run_params[key.strip()] = value

    # Add project dir to path so imports work
    sys.path.insert(0, str(root))

    entry_file = root / config["entry"]
    if not entry_file.exists():
        console.print(f"[red]Entry file not found:[/red] {config['entry']}")
        raise SystemExit(1)

    # Import and execute
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("__strot_main__", entry_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find decorated classes
        from strot_sdk.decorators import get_registry
        registry = get_registry()

        target_type = config["type"]
        registered = registry.get(target_type, {})

        if not registered:
            # Check all types
            for rtype, items in registry.items():
                if items:
                    registered = items
                    target_type = rtype
                    break

        if not registered:
            console.print("[yellow]No decorated classes found.[/yellow]")
            console.print("[dim]Make sure your code uses @function, @agent, @cortex, or @page.[/dim]")
            raise SystemExit(1)

        for name, entry in registered.items():
            cls = entry["class"]
            cfg = entry["config"]

            console.print(f"[dim]Found @{target_type}:[/dim] {name}")

            if target_type == "function":
                _test_function(cls, cfg, run_params)
            elif target_type == "agent":
                _test_agent(cls, cfg)
            elif target_type == "cortex":
                _test_cortex(cls, cfg)
            elif target_type == "page":
                _test_page(cls, cfg)
            else:
                console.print(f"[yellow]Testing for @{target_type} not yet supported.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
    finally:
        sys.path.pop(0)


def _test_function(cls, cfg, params):
    """Test a @function decorated class."""
    # Instantiate if it's a class
    if isinstance(cls, type):
        instance = cls()
        run_method = getattr(instance, "run", None)
    else:
        run_method = cls

    if not run_method:
        console.print("[red]No 'run' method found on the class.[/red]")
        return

    # If no params provided, prompt for them
    if not params and cfg.parameters:
        console.print("[dim]Parameters required:[/dim]")
        for p in cfg.parameters:
            pname = p.get("name", "")
            ptype = p.get("type", "string")
            pdesc = p.get("description", "")
            default = _default_for_type(ptype)
            value = click.prompt(
                f"  {pname} ({ptype}){f' - {pdesc}' if pdesc else ''}",
                default=default,
            )
            # Type conversion
            if ptype in ("number", "integer", "int"):
                value = int(value)
            elif ptype in ("float",):
                value = float(value)
            elif ptype in ("boolean", "bool"):
                value = str(value).lower() in ("true", "1", "yes")
            params[pname] = value

    console.print(f"[dim]Running with params: {params}[/dim]")
    console.print()

    try:
        result = run_method(**params)
        console.print("[green]Result:[/green]")
        console.print(result)
    except Exception as e:
        console.print(f"[red]Execution failed:[/red] {e}")
        import traceback
        traceback.print_exc()


def _test_agent(cls, cfg):
    """Test an @agent decorated class."""
    console.print(f"[dim]Agent: {cfg.name}[/dim]")
    console.print(f"[dim]Model: {cfg.model}[/dim]")
    console.print(f"[dim]Tools: {', '.join(cfg.tools) if cfg.tools else 'none'}[/dim]")
    console.print(f"[dim]System prompt:[/dim]")
    if cfg.system_prompt:
        for line in cfg.system_prompt.split("\n")[:5]:
            console.print(f"  {line}")
        if cfg.system_prompt.count("\n") > 5:
            console.print("  ...")
    console.print()
    console.print("[green]Agent configuration is valid.[/green]")


def _test_cortex(cls, cfg):
    """Test a @cortex decorated class by compiling its pipeline DSL."""
    import json
    from strot_sdk.cortex import build_pipeline

    console.print(f"[dim]Compiling pipeline...[/dim]")

    try:
        dsl = build_pipeline(cls)
    except Exception as e:
        console.print(f"[red]Pipeline compilation failed:[/red] {e}")
        import traceback
        traceback.print_exc()
        return

    nodes = dsl.get("nodes", [])
    edges = dsl.get("edges", [])

    console.print(f"[green]Pipeline compiled successfully![/green]")
    console.print(f"  Nodes: {len(nodes)}")
    console.print(f"  Edges: {len(edges)}")
    console.print()

    # Show node summary
    for node in nodes:
        node_type = node.get("type", "unknown")
        node_id = node.get("id", "?")
        console.print(f"  [{node_type}] {node_id}")

    # Validate edges reference valid nodes
    node_ids = {n["id"] for n in nodes}
    for edge in edges:
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        if src not in node_ids:
            console.print(f"  [yellow]Warning: edge source '{src}' not found in nodes[/yellow]")
        if tgt not in node_ids:
            console.print(f"  [yellow]Warning: edge target '{tgt}' not found in nodes[/yellow]")

    console.print()
    console.print("[dim]Full DSL:[/dim]")
    console.print(json.dumps(dsl, indent=2))


def _test_page(cls, cfg):
    """Test a @page decorated class by compiling its layout."""
    import json
    from strot_sdk.pages import build_page

    console.print(f"[dim]Compiling page layout...[/dim]")

    try:
        layout = build_page(cls)
    except Exception as e:
        console.print(f"[red]Page compilation failed:[/red] {e}")
        import traceback
        traceback.print_exc()
        return

    rows = layout.get("layout", {}).get("rows", [])
    total_blocks = sum(len(row.get("columns", [])) for row in rows)

    console.print(f"[green]Page compiled successfully![/green]")
    console.print(f"  Rows: {len(rows)}")
    console.print(f"  Blocks: {total_blocks}")
    console.print()

    # Show layout summary
    for i, row in enumerate(rows):
        cols = row.get("columns", [])
        block_summary = ", ".join(
            f"{c.get('type', '?')}(span={c.get('span', '?')})" for c in cols
        )
        console.print(f"  Row {i + 1}: {block_summary}")

    # Validate spans sum to 12
    for i, row in enumerate(rows):
        cols = row.get("columns", [])
        total_span = sum(c.get("span", 0) for c in cols)
        if total_span != 12 and cols:
            console.print(f"  [yellow]Warning: Row {i + 1} spans sum to {total_span} (expected 12)[/yellow]")

    console.print()
    console.print("[dim]Full layout:[/dim]")
    console.print(json.dumps(layout, indent=2))


def _default_for_type(ptype: str) -> str:
    """Generate a default test value for a parameter type."""
    defaults = {
        "string": "test",
        "number": "0",
        "integer": "0",
        "int": "0",
        "float": "0.0",
        "boolean": "true",
        "bool": "true",
    }
    return defaults.get(ptype, "test")
