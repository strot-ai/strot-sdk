"""
STROT SDK — Configuration & Credentials

Reads credentials from (in priority order):
1. Constructor arguments
2. Environment variables (STROT_URL, STROT_API_KEY)
3. Credentials file (~/.strot/credentials)
"""
import os
import stat
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_CREDENTIALS_DIR = Path.home() / ".strot"
DEFAULT_CREDENTIALS_FILE = DEFAULT_CREDENTIALS_DIR / "credentials"


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML file, returns empty dict on failure."""
    try:
        import yaml
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _save_yaml(path: Path, data: Dict[str, Any]) -> None:
    """Save YAML file with restricted permissions."""
    import yaml
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    # Restrict permissions: owner read/write only
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


class StrotConfig:
    """Manages STROT configuration and credentials."""

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        profile: Optional[str] = None,
        credentials_file: Optional[Path] = None,
    ):
        self._credentials_file = credentials_file or DEFAULT_CREDENTIALS_FILE
        self._profile = profile

        # Resolve URL and API key with priority chain
        self.url = url or os.environ.get("STROT_URL") or self._from_credentials("url")
        self.api_key = api_key or os.environ.get("STROT_API_KEY") or self._from_credentials("api_key")

        if not self.url:
            logger.debug("No STROT URL configured. Use 'strot login' or set STROT_URL.")
        if not self.api_key:
            logger.debug("No STROT API key configured. Use 'strot login' or set STROT_API_KEY.")

    def _get_profile_name(self) -> str:
        """Get the active profile name."""
        if self._profile:
            return self._profile
        return os.environ.get("STROT_PROFILE", self._read_current_profile())

    def _read_current_profile(self) -> str:
        """Read current_profile from credentials file."""
        data = _load_yaml(self._credentials_file)
        return data.get("current_profile", "default")

    def _from_credentials(self, key: str) -> Optional[str]:
        """Read a value from the active profile in credentials file."""
        data = _load_yaml(self._credentials_file)
        profiles = data.get("profiles", {})
        profile_name = self._get_profile_name()
        profile = profiles.get(profile_name, {})
        return profile.get(key)

    @property
    def org(self) -> Optional[str]:
        """Get organization from credentials."""
        return self._from_credentials("org")

    @property
    def user_email(self) -> Optional[str]:
        """Get user email from credentials."""
        return self._from_credentials("user_email")

    @property
    def is_configured(self) -> bool:
        """Check if URL and API key are available."""
        return bool(self.url and self.api_key)

    def validate(self) -> None:
        """Raise if not configured."""
        if not self.url:
            raise RuntimeError(
                "STROT URL not configured. Run 'strot login' or set STROT_URL environment variable."
            )
        if not self.api_key:
            raise RuntimeError(
                "STROT API key not configured. Run 'strot login' or set STROT_API_KEY environment variable."
            )

    # --- Credential management (used by CLI) ---

    @staticmethod
    def save_profile(
        profile: str,
        url: str,
        api_key: str,
        org: Optional[str] = None,
        user_email: Optional[str] = None,
        set_current: bool = True,
    ) -> None:
        """Save credentials for a profile."""
        data = _load_yaml(DEFAULT_CREDENTIALS_FILE)
        if "version" not in data:
            data["version"] = 1
        if "profiles" not in data:
            data["profiles"] = {}
        data["profiles"][profile] = {
            "url": url,
            "api_key": api_key,
        }
        if org:
            data["profiles"][profile]["org"] = org
        if user_email:
            data["profiles"][profile]["user_email"] = user_email
        if set_current:
            data["current_profile"] = profile
        _save_yaml(DEFAULT_CREDENTIALS_FILE, data)

    @staticmethod
    def delete_profile(profile: str) -> bool:
        """Delete a profile. Returns True if deleted."""
        data = _load_yaml(DEFAULT_CREDENTIALS_FILE)
        profiles = data.get("profiles", {})
        if profile in profiles:
            del profiles[profile]
            if data.get("current_profile") == profile:
                # Switch to first remaining profile or "default"
                data["current_profile"] = next(iter(profiles), "default")
            _save_yaml(DEFAULT_CREDENTIALS_FILE, data)
            return True
        return False

    @staticmethod
    def list_profiles() -> Dict[str, Dict[str, Any]]:
        """List all saved profiles."""
        data = _load_yaml(DEFAULT_CREDENTIALS_FILE)
        return data.get("profiles", {})

    @staticmethod
    def get_current_profile_name() -> str:
        """Get the current profile name."""
        data = _load_yaml(DEFAULT_CREDENTIALS_FILE)
        return data.get("current_profile", "default")
