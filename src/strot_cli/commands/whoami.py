"""strot whoami — Show current authentication info."""
import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.command()
def whoami():
    """Show current user, organization, and instance info."""
    from strot_sdk.config import StrotConfig

    config = StrotConfig()
    if not config.is_configured:
        console.print("[yellow]Not authenticated. Run 'strot login' first.[/yellow]")
        raise SystemExit(1)

    profile_name = config.get_current_profile_name()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")

    table.add_row("Profile", profile_name)
    table.add_row("Instance", config.url)
    table.add_row("Org ID", config.org or "[dim]not set[/dim]")

    # Try to get live user info from the org-scoped API
    try:
        from strot_sdk.client import StrotClient
        client = StrotClient()
        user_info = client.whoami()
        table.add_row("Email", user_info.get("email", ""))
        table.add_row("Name", user_info.get("name", ""))
        table.add_row("Status", "[green]Connected[/green]")
    except Exception:
        table.add_row("Email", config.user_email or "[dim]unknown[/dim]")
        table.add_row("Status", "[yellow]Cannot reach instance[/yellow]")

    console.print(table)
