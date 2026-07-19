"""Skill manager module.

This module provides the SkillManager class for unified skill management
with comprehensive metrics tracking and dependency management.

Exports:
    - SkillManager: Main class for skill management with registry and executor integration
    - SkillMetrics: Dataclass for skill-specific metrics
    - AggregatedMetrics: Dataclass for hourly aggregated metrics
"""

from .skill_manager import SkillManager, SkillMetrics, AggregatedMetrics
from .registry import SkillRegistry
from .executor import SkillExecutor, SkillResult

__all__ = [
    "SkillManager",
    "SkillMetrics",
    "AggregatedMetrics",
    "SkillRegistry",
    "SkillExecutor",
    "SkillResult",
]
