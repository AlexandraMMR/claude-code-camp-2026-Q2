"""
Abstract base class for Boukensha tasks.
All task implementations must subclass Base and define task_name.
"""

from pathlib import Path
from typing import Optional


class Base:
    """Abstract base class for tasks. All behavior is expressed as class methods."""

    @classmethod
    def task_name(cls) -> str:
        """Must be overridden by subclasses to return the task name."""
        raise NotImplementedError(f"{cls.__name__} must define task_name")

    @classmethod
    def provider(cls, settings: dict) -> str:
        """Returns the provider name from settings."""
        value = settings.get("provider")
        if value is None:
            raise ValueError(f"tasks.{cls.task_name()}.provider is required in settings.yml")
        return value

    @classmethod
    def model(cls, settings: dict) -> str:
        """Returns the model name from settings."""
        value = settings.get("model")
        if value is None:
            raise ValueError(f"tasks.{cls.task_name()}.model is required in settings.yml")
        return value

    @classmethod
    def prompt_override(cls, settings: dict, prompt: str = "system") -> bool:
        """Returns True if prompt override is enabled for the given prompt type."""
        node = settings.get("prompt_override") or settings.get("prompt_override")
        if not isinstance(node, dict):
            return False
        return (node.get(prompt) or node.get(prompt)) is True

    @classmethod
    def prompt(cls, settings: dict, name: str = "system", user_prompts_dir: Optional[str] = None, default_prompts_dir: Optional[str] = None) -> Optional[str]:
        """Resolves the prompt text based on override settings."""
        if cls.prompt_override(settings, name):
            text = cls._read_user_prompt(name, user_prompts_dir=user_prompts_dir)
            if text is not None:
                return text

        return cls._read_default_prompt(name, default_prompts_dir=default_prompts_dir)

    @classmethod
    def system_prompt(cls, settings: dict, user_prompts_dir: Optional[str] = None, default_prompts_dir: Optional[str] = None) -> Optional[str]:
        """Resolves the system prompt."""
        return cls.prompt(settings, "system", user_prompts_dir=user_prompts_dir, default_prompts_dir=default_prompts_dir)

    @classmethod
    def _read_user_prompt(cls, prompt_name: str, user_prompts_dir: Optional[str]) -> Optional[str]:
        """Reads a user-defined prompt override."""
        if user_prompts_dir is None:
            return None
        path = Path(user_prompts_dir) / cls.task_name() / f"{prompt_name}.md"
        return cls._read_file(path)

    @classmethod
    def _read_default_prompt(cls, prompt_name: str, default_prompts_dir: Optional[str]) -> Optional[str]:
        """Reads the default shipped prompt."""
        if default_prompts_dir is None:
            return None
        path = Path(default_prompts_dir) / f"{prompt_name}.md"
        return cls._read_file(path)

    @classmethod
    def _read_file(cls, path: Path) -> Optional[str]:
        """Reads file content if it exists, returns None otherwise."""
        if path.exists():
            return path.read_text().strip()
        return None
