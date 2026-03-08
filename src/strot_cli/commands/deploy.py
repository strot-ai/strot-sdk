"""strot deploy — Deploy project to a STROT instance."""
import click
from pathlib import Path
from rich.console import Console

console = Console()


@click.command()
@click.option("--dry-run", is_flag=True, help="Validate without deploying")
def deploy(dry_run):
    """Deploy the current project to your STROT instance.

    Reads strot.yaml, bundles files, and deploys to the connected instance.
    """
    from strot_cli.project import find_project_root, load_project_config, read_project_files

    root = find_project_root()
    if not root:
        console.print("[red]No strot.yaml found.[/red] Run 'strot init' to create a project.")
        raise SystemExit(1)

    config = load_project_config(root)
    project_type = config["type"]

    console.print(f"[bold]Deploying:[/bold] {config['name']} ({project_type})")

    if project_type in ("cortex", "page"):
        _deploy_compiled(root, config, dry_run)
    else:
        _deploy_function(root, config, dry_run)


def _deploy_function(root, config, dry_run):
    """Deploy a tool or agent (code-based)."""
    from strot_cli.project import read_project_files

    files = read_project_files(root)
    console.print(f"[dim]Files: {', '.join(files.keys())}[/dim]")

    if not files:
        console.print("[red]No files to deploy.[/red]")
        raise SystemExit(1)

    entry = config["entry"]
    if entry not in files:
        console.print(f"[red]Entry file '{entry}' not found.[/red]")
        raise SystemExit(1)

    code = files.pop(entry)

    if dry_run:
        console.print()
        console.print("[green]Dry run passed.[/green] Project is valid for deployment.")
        console.print(f"  Name: {config['name']}")
        console.print(f"  Type: {config['type']}")
        console.print(f"  Entry: {entry} ({len(code)} chars)")
        if files:
            console.print(f"  Additional files: {', '.join(files.keys())}")
        return

    try:
        from strot_sdk.client import StrotClient
        client = StrotClient()

        result = client.deploy_function(
            name=config["name"],
            code=code,
            function_type=config["type"],
            description=config.get("description", ""),
            category=config.get("category", "custom"),
            language=config.get("language", "python"),
            file_contents=files if files else None,
            config={
                "version": config.get("version", "1.0.0"),
            },
        )

        if result.success:
            console.print()
            console.print(f"[green]Deployed successfully![/green] ({result.action})")
            if result.url:
                console.print(f"[dim]URL: {result.url}[/dim]")
            if result.id:
                console.print(f"[dim]ID: {result.id}[/dim]")
        else:
            console.print(f"[red]Deploy failed:[/red] {result.error}")
            raise SystemExit(1)

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Deploy failed:[/red] {e}")
        raise SystemExit(1)


def _deploy_compiled(root, config, dry_run):
    """Deploy a cortex pipeline or page (compiled to JSON DSL)."""
    import sys
    import importlib.util

    entry = config["entry"]
    entry_file = root / entry

    if not entry_file.exists():
        console.print(f"[red]Entry file '{entry}' not found.[/red]")
        raise SystemExit(1)

    # Import the entry module to find decorated classes
    sys.path.insert(0, str(root))
    try:
        spec = importlib.util.spec_from_file_location("__strot_deploy__", entry_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        project_type = config["type"]

        if project_type == "cortex":
            dsl = _compile_cortex(module, config)
        else:
            dsl = _compile_page(module, config)

        if dry_run:
            import json
            console.print()
            console.print("[green]Dry run passed.[/green] Compiled successfully.")
            console.print(f"  Name: {config['name']}")
            console.print(f"  Type: {project_type}")
            console.print()
            console.print("[dim]Compiled DSL:[/dim]")
            console.print(json.dumps(dsl, indent=2))
            return

        # Deploy to STROT instance
        from strot_sdk.client import StrotClient
        client = StrotClient()

        if project_type == "cortex":
            result = client.deploy_orchestration(
                name=config["name"],
                dsl=dsl,
                description=config.get("description", ""),
            )
        else:
            result = client.deploy_page(
                name=config["name"],
                layout=dsl,
                description=config.get("description", ""),
            )

        if result.success:
            console.print()
            console.print(f"[green]Deployed successfully![/green] ({result.action})")
            if result.url:
                console.print(f"[dim]URL: {result.url}[/dim]")
            if result.id:
                console.print(f"[dim]ID: {result.id}[/dim]")
        else:
            console.print(f"[red]Deploy failed:[/red] {result.error}")
            raise SystemExit(1)

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Deploy failed:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
    finally:
        sys.path.pop(0)


def _compile_cortex(module, config):
    """Compile a @cortex decorated class to DSL."""
    from strot_sdk.decorators import get_registry
    from strot_sdk.cortex import build_pipeline

    registry = get_registry()
    cortex_items = registry.get("cortex", {})

    if not cortex_items:
        raise ValueError("No @cortex decorated class found in entry file.")

    # Use the first (or matching) cortex class
    target_name = config["name"]
    cls = None
    for name, entry in cortex_items.items():
        if name == target_name:
            cls = entry["class"]
            break
    if cls is None:
        cls = next(iter(cortex_items.values()))["class"]

    console.print(f"[dim]Compiling pipeline: {target_name}[/dim]")
    return build_pipeline(cls)


def _compile_page(module, config):
    """Compile a @page decorated class to layout JSON."""
    from strot_sdk.decorators import get_registry
    from strot_sdk.pages import build_page

    registry = get_registry()
    page_items = registry.get("page", {})

    if not page_items:
        raise ValueError("No @page decorated class found in entry file.")

    target_name = config["name"]
    cls = None
    for name, entry in page_items.items():
        if name == target_name:
            cls = entry["class"]
            break
    if cls is None:
        cls = next(iter(page_items.values()))["class"]

    console.print(f"[dim]Compiling page layout: {target_name}[/dim]")
    return build_page(cls)
