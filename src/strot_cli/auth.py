"""
STROT CLI — Browser-Based Authentication (Org-Scoped)

Flow:
1. CLI opens browser to /<org_id>/cli/auth
2. User logs in if needed, clicks "Authorize CLI"
3. Browser shows the generated API key
4. User copies and pastes into the CLI prompt
5. CLI validates and saves to ~/.strot/credentials
"""
import secrets
import webbrowser
import logging

logger = logging.getLogger(__name__)


def generate_auth_code() -> str:
    """Generate a random code (used as a nonce in the auth URL)."""
    return secrets.token_urlsafe(16)


def get_auth_url(instance_url: str, org_id: str, code: str) -> str:
    """Build the org-scoped browser auth URL."""
    base = instance_url.rstrip("/")
    return f"{base}/{org_id}/cli/auth?code={code}"


def open_browser_auth(instance_url: str, org_id: str, code: str) -> str:
    """Open the browser to the auth URL. Returns the URL."""
    url = get_auth_url(instance_url, org_id, code)
    try:
        webbrowser.open(url)
    except Exception:
        pass  # Browser open may fail in headless environments
    return url
