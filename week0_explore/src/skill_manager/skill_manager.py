"""
Skill Manager - Unified interface for skill management with metrics tracking.

This module provides the SkillManager class that:
- Integrates SkillRegistry and SkillExecutor for unified skill operations
- Tracks comprehensive skill usage and performance metrics
- Aggregates metrics hourly with 30-day retention
- Manages dependency resolution for skill invocation

Validates: Requirements 11.2, 11.3, 11.4 (Skill Invocation, Metrics Tracking, Dependency Management)
"""

import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Import models from data folder
from ..data.models import SkillMetadata, ParameterSchema

# Import registry and executor
from .registry import SkillRegistry
from .executor import SkillExecutor, SkillResult, ValidationError, TimeoutError, ExecutionError, DependencyError


# =============================================================================
# Metrics Data Structures
# =============================================================================

@dataclass
class SkillMetrics:
    """
    Metrics for a single skill.
    
    Validates: Requirements 11.3 (Metrics Tracking)
    """
    skill_name: str
    invocation_count: int = 0
    total_execution_time_ms: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    error_types: Dict[str, int] = field(default_factory=dict)
    resource_consumption: Dict[str, float] = field(default_factory=dict)
    last_invocation: Optional[datetime] = None
    
    @property
    def average_execution_time_ms(self) -> float:
        """Calculate average execution time in milliseconds."""
        if self.invocation_count == 0:
            return 0.0
        return self.total_execution_time_ms / self.invocation_count
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage."""
        if self.invocation_count == 0:
            return 0.0
        return (self.success_count / self.invocation_count) * 100
    
    def add_invocation(
        self,
        duration_ms: float,
        status: str,
        error_type: Optional[str] = None,
        resource_consumption: Optional[Dict[str, float]] = None
    ) -> None:
        """Add a skill invocation to the metrics."""
        self.invocation_count += 1
        self.total_execution_time_ms += duration_ms
        self.last_invocation = datetime.utcnow()
        
        if status == "success":
            self.success_count += 1
        else:
            self.failure_count += 1
            if error_type:
                self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
        
        if resource_consumption:
            for key, value in resource_consumption.items():
                self.resource_consumption[key] = self.resource_consumption.get(key, 0.0) + value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "skill_name": self.skill_name,
            "invocation_count": self.invocation_count,
            "average_execution_time_ms": self.average_execution_time_ms,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "error_types": self.error_types,
            "resource_consumption": self.resource_consumption,
            "last_invocation": self.last_invocation.isoformat() if self.last_invocation else None
        }


@dataclass
class AggregatedMetrics:
    """
    Hourly aggregated metrics for all skills.
    
    Validates: Requirements 11.3 (Metrics Aggregation)
    """
    hour_start: datetime
    skills: Dict[str, SkillMetrics] = field(default_factory=dict)
    total_invocations: int = 0
    total_success_count: int = 0
    total_failure_count: int = 0
    
    def add_skill_metrics(self, skill_metrics: SkillMetrics) -> None:
        """Add skill metrics to the hourly aggregate."""
        self.skills[skill_metrics.skill_name] = skill_metrics
        self.total_invocations += skill_metrics.invocation_count
        self.total_success_count += skill_metrics.success_count
        self.total_failure_count += skill_metrics.failure_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert aggregated metrics to dictionary."""
        return {
            "hour_start": self.hour_start.isoformat(),
            "total_invocations": self.total_invocations,
            "total_success_count": self.total_success_count,
            "total_failure_count": self.total_failure_count,
            "skills": {name: metrics.to_dict() for name, metrics in self.skills.items()}
        }


# =============================================================================
# Skill Manager
# =============================================================================

class SkillManager:
    """
    Unified interface for skill management with comprehensive metrics tracking.
    
    Provides:
    - Integration of SkillRegistry and SkillExecutor
    - Metrics tracking: invocation count, average execution time, success rate,
      error types and frequencies, resource consumption
    - Hourly aggregation with 30-day retention
    - Dependency resolution support
    
    Performance:
    - Registry queries: <100ms
    - Dependency graph generation: <200ms for graphs up to 100 nodes
    - Metrics retrieval: O(1) for single skill, O(n) for all skills
    """
    
    def __init__(
        self,
        registry: Optional[SkillRegistry] = None,
        executor: Optional[SkillExecutor] = None,
        retention_days: int = 30,
        enable_metrics: bool = True
    ):
        """
        Initialize the skill manager.
        
        Args:
            registry: SkillRegistry instance (creates new if None)
            executor: SkillExecutor instance (creates new if None)
            retention_days: Number of days to retain metrics (default 30)
            enable_metrics: Whether to collect metrics (default True)
            
        Performance: O(1) initialization
        """
        self._registry = registry or SkillRegistry()
        self._executor = executor or SkillExecutor(self._registry)
        self._retention_days = retention_days
        self._enable_metrics = enable_metrics
        
        # Current hourly aggregate (Mutable - will be flushed at hour boundary)
        self._current_hour_start = self._get_hour_start(datetime.utcnow())
        self._current_hour_metrics = AggregatedMetrics(hour_start=self._current_hour_start)
        
        # Historical aggregates stored by hour start
        self._historical_metrics: Dict[datetime, AggregatedMetrics] = {}
        
        # In-memory metrics per skill (cumulative)
        self._skill_metrics: Dict[str, SkillMetrics] = {}
        
        # Metrics for overall system performance
        self._system_metrics: Dict[str, Any] = {
            "total_skill_executions": 0,
            "total_successes": 0,
            "total_failures": 0,
            "total_execution_time_ms": 0.0
        }
    
    def register_skill(self, metadata: SkillMetadata) -> bool:
        """
        Register a new skill with the manager.
        
        Args:
            metadata: SkillMetadata containing skill information
            
        Returns:
            True if registration successful, False otherwise
            
        Raises:
            ValueError: If circular dependency would be created
            
        Performance: <100ms for registration
        """
        try:
            success = self._registry.register(metadata)
            return success
        except ValueError as e:
            # Re-raise circular dependency error
            raise e
    
    def discover_skill(self, skill_name: str) -> Optional[SkillMetadata]:
        """
        Discover a skill by name.
        
        Args:
            skill_name: Name of the skill to discover
            
        Returns:
            SkillMetadata if found, None otherwise
            
        Performance: Returns within 100ms for single skill lookup
        """
        return self._registry.discover(skill_name)
    
    def list_skills(self, filter_by_version: Optional[str] = None) -> List[SkillMetadata]:
        """
        List all registered skills.
        
        Args:
            filter_by_version: Optional version string to filter skills
            
        Returns:
            List of SkillMetadata objects
            
        Performance: Returns within 100ms for up to 100 skills
        """
        return self._registry.list_skills(filter_by_version)
    
    def execute_skill(
        self,
        skill_name: str,
        parameters: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> SkillResult:
        """
        Execute a registered skill with the given parameters.
        
        Args:
            skill_name: Name of the skill to execute
            parameters: Dictionary of parameters to pass to the skill
            timeout: Optional timeout in seconds (overrides default)
            
        Returns:
            SkillResult with execution status, duration, output, and any errors
            
        Raises:
            ValueError: If skill not found or parameters invalid
            TimeoutError: If execution exceeds timeout
            ExecutionError: If skill execution fails
            
        Performance: Executes within timeout + buffer seconds
        """
        start_time = time.perf_counter()
        
        try:
            # Check dependencies before execution
            self._validate_dependencies(skill_name)
            
            # Execute the skill
            result = self._executor.execute(skill_name, parameters, timeout)
            
            # Update metrics if enabled
            if self._enable_metrics:
                duration_ms = (time.perf_counter() - start_time) * 1000
                self._update_metrics(skill_name, result, duration_ms)
            
            return result
            
        except ValueError as e:
            # Parameter validation failed
            result = self._create_failure_result(
                skill_name=skill_name,
                duration_ms=0,
                error_type="ValidationError",
                message=str(e),
                suggested_actions=["Check skill parameters"]
            )
            if self._enable_metrics:
                self._update_metrics(skill_name, result, 0)
            raise e
    
    def _validate_dependencies(self, skill_name: str) -> None:
        """
        Validate that all skill dependencies are satisfied.
        
        Args:
            skill_name: Name of the skill to validate dependencies for
            
        Raises:
            DependencyError: If dependencies are not satisfied
        """
        skill = self._registry.discover(skill_name)
        if skill is None:
            return  # Will be caught by executor
        
        # Check if any dependencies are missing
        missing_deps = []
        for dep in skill.dependencies:
            if self._registry.discover(dep) is None:
                missing_deps.append(dep)
        
        if missing_deps:
            raise DependencyError(
                f"Skill '{skill_name}' has unsatisfied dependencies: {', '.join(missing_deps)}",
                missing_dependencies=missing_deps,
                suggested_action=f"Register missing dependencies: {', '.join(missing_deps)}"
            )
    
    def get_skill_metrics(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metrics for a specific skill.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            Dictionary with skill metrics or None if skill not found
            
        Performance: O(1) lookup
        """
        if skill_name not in self._skill_metrics:
            return None
        
        metrics = self._skill_metrics[skill_name]
        return metrics.to_dict()
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for all skills.
        
        Returns:
            Dictionary with metrics for all registered skills
            
        Performance: O(n) where n is number of registered skills
        """
        return {
            skill_name: metrics.to_dict()
            for skill_name, metrics in self._skill_metrics.items()
        }
    
    def get_hourly_aggregates(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get hourly aggregated metrics within a time range.
        
        Args:
            start_time: Start of time range (default: 30 days ago)
            end_time: End of time range (default: now)
            
        Returns:
            List of hourly aggregate dictionaries
            
        Performance: O(n) where n is number of hours in range
        """
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(days=self._retention_days)
        if end_time is None:
            end_time = datetime.utcnow()
        
        aggregates = []
        
        # Include current hour metrics if within range
        if start_time <= self._current_hour_start <= end_time:
            aggregates.append(self._current_hour_metrics.to_dict())
        
        # Include historical metrics within range
        for hour_start, aggregate in self._historical_metrics.items():
            if start_time <= hour_start <= end_time:
                aggregates.append(aggregate.to_dict())
        
        # Sort by hour start
        aggregates.sort(key=lambda x: x["hour_start"])
        
        return aggregates
    
    def get_dependency_graph(self, skill_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get dependency graph for skills.
        
        Args:
            skill_name: Optional specific skill to get graph for.
                       If None, returns graph for all skills.
            
        Returns:
            Dictionary mapping skill names to their dependencies
            
        Performance: <200ms for graphs up to 100 nodes
        """
        return self._registry.get_dependency_graph(skill_name)
    
    def get_skill_registry(self) -> SkillRegistry:
        """
        Get the underlying skill registry.
        
        Returns:
            SkillRegistry instance
        """
        return self._registry
    
    def get_skill_executor(self) -> SkillExecutor:
        """
        Get the underlying skill executor.
        
        Returns:
            SkillExecutor instance
        """
        return self._executor
    
    def flush_metrics(self, current_time: Optional[datetime] = None) -> None:
        """
        Flush current hour metrics to historical storage.
        
        Call this at the start of each hour to maintain hourly aggregation.
        
        Args:
            current_time: Current time for determining hour boundary
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        current_hour_start = self._get_hour_start(current_time)
        
        # Check if we need to flush
        if current_hour_start != self._current_hour_start:
            # Store current hour metrics
            if self._current_hour_metrics.skills:
                self._historical_metrics[self._current_hour_start] = self._current_hour_metrics
            
            # Create new current hour metrics
            self._current_hour_start = current_hour_start
            self._current_hour_metrics = AggregatedMetrics(hour_start=current_hour_start)
            
            # Clean up old metrics beyond retention period
            cutoff_time = current_time - timedelta(days=self._retention_days)
            old_hours = [
                hour for hour in self._historical_metrics.keys()
                if hour < cutoff_time
            ]
            for hour in old_hours:
                del self._historical_metrics[hour]
    
    def _update_metrics(
        self,
        skill_name: str,
        result: SkillResult,
        duration_ms: float
    ) -> None:
        """
        Update metrics for a skill invocation.
        
        Args:
            skill_name: Name of the skill executed
            result: SkillResult from execution
            duration_ms: Execution duration in milliseconds
        """
        # Initialize skill metrics if not exists
        if skill_name not in self._skill_metrics:
            self._skill_metrics[skill_name] = SkillMetrics(skill_name=skill_name)
        
        # Update skill-level metrics
        self._skill_metrics[skill_name].add_invocation(
            duration_ms=duration_ms,
            status=result.status,
            error_type=result.error_type,
            resource_consumption=None  # Can be enhanced with actual resource data
        )
        
        # Update hourly aggregate
        self._current_hour_metrics.add_skill_metrics(self._skill_metrics[skill_name])
        
        # Update system-wide metrics
        self._system_metrics["total_skill_executions"] += 1
        self._system_metrics["total_execution_time_ms"] += duration_ms
        if result.status == "success":
            self._system_metrics["total_successes"] += 1
        else:
            self._system_metrics["total_failures"] += 1
    
    def _create_failure_result(
        self,
        skill_name: str,
        duration_ms: float,
        error_type: str,
        message: str,
        suggested_actions: List[str]
    ) -> SkillResult:
        """
        Create a failure result with diagnostic information.
        
        Args:
            skill_name: Name of the skill that failed
            duration_ms: Execution duration in milliseconds
            error_type: Type of error that occurred
            message: Error message
            suggested_actions: List of suggested actions
            
        Returns:
            SkillResult with failure status and diagnostics
        """
        return SkillResult(
            status="failure",
            skill_name=skill_name,
            duration_ms=duration_ms,
            errors=[message],
            error_type=error_type,
            suggested_actions=suggested_actions
        )
    
    def _get_hour_start(self, dt: datetime) -> datetime:
        """
        Get the start of the hour for a given datetime.
        
        Args:
            dt: Datetime to get hour start for
            
        Returns:
            Datetime at the start of the hour (e.g., 10:35 -> 10:00)
        """
        return dt.replace(minute=0, second=0, microsecond=0)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system-wide metrics.
        
        Returns:
            Dictionary with system-wide statistics
        """
        return {
            **self._system_metrics,
            "retention_days": self._retention_days,
            "current_hour_start": self._current_hour_start.isoformat(),
            "active_hours_stored": len(self._historical_metrics)
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        self._skill_metrics.clear()
        self._historical_metrics.clear()
        self._current_hour_metrics = AggregatedMetrics(hour_start=self._current_hour_start)
        self._system_metrics = {
            "total_skill_executions": 0,
            "total_successes": 0,
            "total_failures": 0,
            "total_execution_time_ms": 0.0
        }
