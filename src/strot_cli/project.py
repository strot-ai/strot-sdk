"""
STROT CLI — Project Detection

Reads strot.yaml to understand the project type and configuration.
"""
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def find_project_root(start: Optional[Path] = None) -> Optional[Path]:
    """Find the project root by looking for strot.yaml."""
    current = start or Path.cwd()
    while current != current.parent:
        if (current / "strot.yaml").exists():
            return current
        current = current.parent
    return None


def load_project_config(project_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load strot.yaml from the project directory.

    Returns:
        Project config dict with keys:
        - name: str
        - type: str (tool, agent, cortex, page)
        - language: str (python, typescript)
        - version: str
        - description: str
        - category: str
        - entry: str (main entry file)
        - files: list of additional files
    """
    import yaml

    root = project_dir or find_project_root()
    if not root:
        raise FileNotFoundError("No strot.yaml found. Run 'strot init' to create a project.")

    config_path = root / "strot.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    # Defaults
    config.setdefault("name", root.name)
    config.setdefault("type", "tool")
    config.setdefault("language", "python")
    config.setdefault("version", "1.0.0")
    config.setdefault("description", "")
    config.setdefault("category", "custom")
    config.setdefault("entry", "main.py")
    config.setdefault("files", [])

    return config


def read_project_files(project_dir: Optional[Path] = None) -> Dict[str, str]:
    """
    Read all project files (entry + additional files) and return contents.

    Returns:
        Dict mapping filename to file contents.
    """
    root = project_dir or find_project_root()
    if not root:
        raise FileNotFoundError("No strot.yaml found.")

    config = load_project_config(root)
    files = {}

    # Read entry file
    entry_path = root / config["entry"]
    if entry_path.exists():
        files[config["entry"]] = entry_path.read_text()

    # Read additional files
    for fname in config.get("files", []):
        fpath = root / fname
        if fpath.exists():
            files[fname] = fpath.read_text()

    return files
