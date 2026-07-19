"""
Configuration class for Boukensha.
Loads settings from .boukensha/settings.yml and environment from .boukensha/.env
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from dotenv import load_dotenv


class Config:
    """
    Configuration manager for Boukensha.
    
    The .boukensha config directory is resolved in this order:
      1. BOUKENSHA_DIR environment variable (set before loading .env)
      2. ~/.boukensha (default)
    """

    # Default prompts shipped alongside the library code
    PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

    def __init__(self):
        self.dir = self._resolve_dir()
        self._load_env()
        self._settings = self._load_settings()

    # ---------- tasks -----------------------------------------------------

    def tasks(self, name: Optional[str] = None) -> Union[Dict[str, Any], Dict[str, Any]]:
        """
        Returns the full tasks hash from settings.yaml, or a specific task's settings.
        
        Args:
            name: Optional task name. If provided, returns that task's settings dict.
                  If None, returns the entire tasks hash.
        
        Returns:
            If name provided: that task's settings dict (or empty dict if not found)
            If name is None: the full tasks dict
        """
        all_tasks = self._dig("tasks") or {}
        if name is None:
            return all_tasks
        
        # Try both string and None (ruby uses symbol or string)
        task_name_str = str(name)
        return all_tasks.get(task_name_str, all_tasks.get(name)) or {}

    def user_prompts_dir(self) -> Path:
        """The user's prompts directory for task prompt overrides."""
        return Path(self.dir) / "prompts"

    # ---------- MUD connection --------------------------------------------

    def mud_host(self) -> str:
        """MUD host from settings, defaults to 'localhost'."""
        return self._dig("mud", "host") or "localhost"

    def mud_port(self) -> int:
        """MUD port from settings, defaults to 4000."""
        return self._dig("mud", "port") or 4000

    def mud_username(self) -> Optional[str]:
        """MUD username from settings."""
        return self._dig("mud", "username")

    def mud_password(self) -> Optional[str]:
        """MUD password from settings."""
        return self._dig("mud", "password")

    # ---------- low-level helpers -----------------------------------------

    def _dig(self, *keys) -> Optional[Any]:
        """
        Fetches a nested key path from settings.
        
        Args:
            *keys: Key path to traverse, e.g., _dig("mud", "host")
        
        Returns:
            The value at the key path, or None if not found.
        """
        node = self._settings
        for key in keys:
            if isinstance(node, dict):
                node = node.get(str(key)) or node.get(key)
            else:
                return None
        return node

    def __str__(self) -> str:
        tasks_list = ",".join(self.tasks().keys())
        return f"#<Boukensha::Config dir={self.dir} tasks={tasks_list}>"

    def __repr__(self) -> str:
        return self.__str__()

    # ---------- private methods -----------------------------------------

    def _resolve_dir(self) -> str:
        """Resolves the .boukensha config directory."""
        raw = os.environ.get("BOUKENSHA_DIR")
        if raw is None:
            raw = str(Path.home() / ".boukensha")
        return str(Path(raw).resolve())

    def _load_env(self) -> None:
        """Loads environment variables from .env file."""
        env_file = Path(self.dir) / ".env"
        if env_file.exists():
            load_dotenv(env_file)

    def _load_settings(self) -> Dict[str, Any]:
        """Loads settings from settings.yaml."""
        settings_file = Path(self.dir) / "settings.yml"
        if settings_file.exists():
            content = settings_file.read_text()
            return yaml.safe_load(content) or {}
        return {}
