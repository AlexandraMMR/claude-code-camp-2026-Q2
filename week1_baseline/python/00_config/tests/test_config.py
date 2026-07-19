"""
Tests for Boukensha Config class.
"""

import os
from pathlib import Path

import pytest

# Set up test environment before importing boukensha
test_boukensha_dir = Path(__file__).parent.parent.parent.parent / ".boukensha"
os.environ["BOUKENSHA_DIR"] = str(test_boukensha_dir)

from boukensha import Config
from boukensha.tasks.base import Base
from boukensha.tasks.player import Player


class TestConfig:
    """Tests for Config class."""

    def test_config_dir_resolved(self):
        """Config directory should be resolved correctly."""
        config = Config()
        assert config.dir is not None
        assert Path(config.dir).exists()

    def test_tasks_method_returns_all_tasks(self):
        """tasks() with no args should return all tasks."""
        config = Config()
        all_tasks = config.tasks()
        assert isinstance(all_tasks, dict)
        assert "player" in all_tasks

    def test_tasks_method_returns_single_task(self):
        """tasks(name) should return a specific task's settings."""
        config = Config()
        player = config.tasks("player")
        assert isinstance(player, dict)
        assert "provider" in player
        assert "model" in player

    def test_tasks_method_returns_empty_for_unknown_task(self):
        """tasks(name) for unknown task should return empty dict."""
        config = Config()
        unknown = config.tasks("nonexistent")
        assert unknown == {}

    def test_user_prompts_dir(self):
        """user_prompts_dir should return the prompts subdirectory."""
        config = Config()
        assert config.user_prompts_dir() == Path(config.dir) / "prompts"

    def test_mud_host_default(self):
        """mud_host should return default when not set."""
        # This test uses the actual settings.yml
        config = Config()
        host = config.mud_host()
        assert host is not None

    def test_mud_port_default(self):
        """mud_port should return default when not set."""
        config = Config()
        port = config.mud_port()
        assert port == 4000

    def test_mud_credentials(self):
        """MUD credentials should be loaded."""
        config = Config()
        # These should be loaded from .env
        assert config.mud_username() is not None
        assert config.mud_password() is not None


class TestPlayerTask:
    """Tests for Player task."""

    def test_task_name(self):
        """Player should have task_name of 'player'."""
        assert Player.task_name() == "player"

    def test_provider_required(self):
        """Provider should raise ValueError when missing."""
        with pytest.raises(ValueError):
            Player.provider({})

    def test_model_required(self):
        """Model should raise ValueError when missing."""
        with pytest.raises(ValueError):
            Player.model({})

    def test_prompt_override_not_set(self):
        """prompt_override? should return False when not set."""
        settings = {"provider": "anthropic", "model": "claude"}
        assert Player.prompt_override?(settings, "system") is False

    def test_prompt_override_set(self):
        """prompt_override? should return True when set."""
        settings = {
            "provider": "anthropic",
            "model": "claude",
            "prompt_override": {"system": True}
        }
        assert Player.prompt_override?(settings, "system") is True

    def test_system_prompt_resolution(self):
        """system_prompt should resolve from user or default."""
        settings = {"provider": "anthropic", "model": "claude"}
        
        # Without override, should return default prompt
        prompt = Player.system_prompt(
            settings,
            user_prompts_dir=None,
            default_prompts_dir=str(Config.PROMPTS_DIR)
        )
        assert prompt is not None
        assert "MUD player assistant" in prompt


class TestBaseTask:
    """Tests for Base task."""

    def test_task_name_not_implemented(self):
        """Base.task_name should raise NotImplementedError."""
        with pytest.raises(NotImplementedError):
            Base.task_name()
