"""strot logout — Clear stored credentials."""
import click
from rich.console import Console

console = Console()


@click.command()
@click.option("--profile", "-p", help="Profile to remove (default: current profile)")
@click.option("--all", "clear_all", is_flag=True, help="Remove all profiles")
def logout(profile, clear_all):
    """Clear stored credentials."""
    from strot_ai.config import StrotConfig, DEFAULT_CREDENTIALS_FILE

    if clear_all:
        if DEFAULT_CREDENTIALS_FILE.exists():
            DEFAULT_CREDENTIALS_FILE.unlink()
            console.print("[green]All credentials cleared.[/green]")
        else:
            console.print("[dim]No credentials file found.[/dim]")
        return

    target = profile or StrotConfig.get_current_profile_name()
    if StrotConfig.delete_profile(target):
        console.print(f"[green]Profile '{target}' removed.[/green]")
    else:
        console.print(f"[yellow]Profile '{target}' not found.[/yellow]")
