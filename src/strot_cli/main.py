"""
STROT CLI — Main entry point.

Usage:
    strot login                     # Authenticate with a STROT instance
    strot whoami                    # Show current user/instance
    strot logout                    # Clear credentials

    strot init tool my-tool         # Scaffold a new tool project
    strot init agent my-agent       # Scaffold a new agent project

    strot resources                 # List all available resources
    strot resources queries         # List saved queries

    strot test                      # Run project locally
    strot test --mock               # Run with mocked data

    strot deploy                    # Deploy to STROT instance
    strot deploy --dry-run          # Validate without deploying
"""
import click


@click.group()
@click.version_option(version="0.1.0", prog_name="strot")
def cli():
    """STROT CLI — Build and deploy tools, agents, and pipelines."""
    pass


# Import and register commands
from .commands.login import login
from .commands.whoami import whoami
from .commands.logout import logout
from .commands.init import init
from .commands.resources import resources
from .commands.test import test
from .commands.deploy import deploy

cli.add_command(login)
cli.add_command(whoami)
cli.add_command(logout)
cli.add_command(init)
cli.add_command(resources)
cli.add_command(test)
cli.add_command(deploy)


if __name__ == "__main__":
    cli()
