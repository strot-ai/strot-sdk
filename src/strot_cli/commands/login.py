"""strot login — Authenticate with a STROT instance (org-scoped)."""
import click
from rich.console import Console

console = Console()


@click.command()
@click.option("--instance", "-i", help="STROT instance URL (e.g., https://app.strot.ai)")
@click.option("--org", "-o", help="Organization ID (UUID from your STROT URL)")
@click.option("--token", "-t", help="API key (skip browser auth)")
@click.option("--profile", "-p", default="default", help="Profile name to save as")
def login(instance, org, token, profile):
    """Authenticate with a STROT instance.

    Opens a browser where you authorize the CLI and get an API key to paste back.

    Your org ID is the UUID in your STROT URL:
    https://app.strot.ai/<org-id>/

    Examples:

      strot login                                    # Interactive

      strot login -i https://app.strot.ai -o 98bf9a0a-...

      strot login --token sk_live_abc123              # Direct API key
    """
    from strot_sdk.config import StrotConfig

    # Collect instance + org
    if not instance:
        instance = click.prompt("STROT instance URL", default="https://app.strot.ai")
    if not org:
        org = click.prompt("Organization ID (UUID from your STROT URL)")

    if token:
        # Direct API key — validate and save
        _validate_and_save(instance, org, token, profile)
        return

    # Browser-based flow: open browser → user authorizes → copies key → pastes here
    from strot_cli.auth import generate_auth_code, open_browser_auth

    code = generate_auth_code()
    url = open_browser_auth(instance, org, code)

    console.print()
    console.print(f"[bold]Authenticating with organization:[/bold] {org}")
    console.print()
    console.print("Opening browser for authentication...")
    console.print(f"If the browser doesn't open, visit this URL:")
    console.print(f"  {url}")
    console.print()
    console.print("After authorizing, copy the API key from the browser and paste it below.")
    console.print()

    api_key = click.prompt("Paste API key")

    if not api_key or not api_key.strip():
        console.print("[red]No API key provided.[/red]")
        raise SystemExit(1)

    api_key = api_key.strip()
    _validate_and_save(instance, org, api_key, profile)


def _validate_and_save(instance: str, org: str, api_key: str, profile: str):
    """Validate API key against the instance and save credentials."""
    from strot_sdk.config import StrotConfig

    console.print(f"[dim]Validating...[/dim]")
    try:
        from strot_sdk.client import StrotClient
        client = StrotClient(url=instance, api_key=api_key, org=org)
        user_info = client.whoami()
        user_email = user_info.get("email", "")
    except Exception as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        raise SystemExit(1)

    StrotConfig.save_profile(
        profile=profile,
        url=instance,
        api_key=api_key,
        org=org,
        user_email=user_email,
    )

    console.print()
    console.print(f"[green]Authenticated as {user_email}[/green]")
    console.print(f"[dim]Organization: {org}[/dim]")
    console.print(f"[dim]Credentials saved to profile '{profile}'[/dim]")
