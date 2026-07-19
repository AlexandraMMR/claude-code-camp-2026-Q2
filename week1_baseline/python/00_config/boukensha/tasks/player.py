"""
Concrete Player task implementation.
"""

from .base import Base


class Player(Base):
    """Concrete Player task - the main agentic loop."""

    @classmethod
    def task_name(cls) -> str:
        return "player"
