"""
Task class for dynamic task management.

This module implements the Task data model with priority scoring,
dependency tracking, and status transitions as specified in the
design document.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class Task:
    """
    Represents a task in the task manager.
    
    The Task class implements:
    - Priority score calculation using multi-factor scoring
    - Dependency tracking and enforcement
    - Task status transitions (pending → running → completed/failed)
    
    Validates: Requirements 1.1 (Priority Recalcation), 1.2 (Multi-factor Scoring),
               1.4 (Dependency Tracking), 1.6 (Metadata Preservation)
    """
    
    # Status constants
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    
    # Status transition map: allowed transitions from each state
    VALID_TRANSITIONS = {
        STATUS_PENDING: [STATUS_RUNNING, STATUS_FAILED],
        STATUS_RUNNING: [STATUS_COMPLETED, STATUS_FAILED],
        STATUS_COMPLETED: [],
        STATUS_FAILED: []
    }
    
    def __init__(
        self,
        description: str,
        priorityScore: float = 0.5,
        createdAt: Optional[datetime] = None,
        estimatedCompletion: Optional[datetime] = None,
        dependencies: Optional[List[UUID]] = None,
        status: str = STATUS_PENDING,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a Task.
        
        Args:
            description: Task description
            priorityScore: Initial priority score (0.0-1.0)
            createdAt: Creation timestamp (defaults to now)
            estimatedCompletion: Estimated completion time
            dependencies: List of dependency task IDs
            status: Initial task status
            metadata: Additional metadata dictionary
        """
        self.id: UUID = uuid4()
        self.description: str = description
        self.priorityScore: float = max(0.0, min(1.0, priorityScore))
        self.createdAt: datetime = createdAt or datetime.utcnow()
        self.estimatedCompletion: Optional[datetime] = estimatedCompletion
        self.dependencies: List[UUID] = dependencies or []
        self.status: str = status
        self.metadata: Dict[str, Any] = metadata or {}
        self.metadata["lastReevaluated"] = self.createdAt
    
    def calculate_priority_score(
        self,
        urgency: Optional[int] = None,
        dependency_status: Optional[float] = None,
        resource_requirements: Optional[Dict[str, Any]] = None,
        expected_value: Optional[float] = None
    ) -> float:
        """
        Calculate priority score using multi-factor algorithm.
        
        The scoring algorithm combines four factors with the following weights:
        - Urgency (30%): How time-sensitive the task is
        - Dependency Status (25%): Whether dependencies are satisfied
        - Resource Requirements (20%): How resource-intensive the task is
        - Expected Value (25%): The expected benefit of completing this task
        
        All factors are normalized to 0.0-1.0 scale before weighting.
        
        Args:
            urgency: Task urgency level (1-10 scale)
            dependency_status: Fraction of dependencies completed (0.0-1.0)
            resource_requirements: Dictionary with resource requirements info
            expected_value: Expected completion value (0.0-1.0)
            
        Returns:
            Calculated priority score between 0.0 and 1.0
        """
        # Extract or calculate factor values
        urgency_score = self._calculate_urgency_score(urgency)
        dependency_score = self._calculate_dependency_score(dependency_status)
        resource_score = self._calculate_resource_score(resource_requirements)
        value_score = self._calculate_value_score(expected_value)
        
        # Apply weights to calculate final score
        weights = {
            "urgency": 0.30,
            "dependencyStatus": 0.25,
            "resourceRequirements": 0.20,
            "expectedValue": 0.25
        }
        
        priority_score = (
            urgency_score * weights["urgency"] +
            dependency_score * weights["dependencyStatus"] +
            resource_score * weights["resourceRequirements"] +
            value_score * weights["expectedValue"]
        )
        
        # Update metadata with recalculation timestamp
        self.metadata["lastReevaluated"] = datetime.utcnow()
        self.metadata["priorityFactors"] = {
            "urgency": urgency_score,
            "dependencyStatus": dependency_score,
            "resourceRequirements": resource_score,
            "expectedValue": value_score
        }
        
        # Update the task's priority score
        self.priorityScore = round(priority_score, 4)
        
        return self.priorityScore
    
    def _calculate_urgency_score(self, urgency: Optional[int]) -> float:
        """Convert urgency (1-10) to normalized score (0.0-1.0)."""
        if urgency is None:
            # Default urgency based on task age (older = more urgent)
            age_hours = (datetime.utcnow() - self.createdAt).total_seconds() / 3600
            urgency = max(1, min(10, int(5 + age_hours / 2)))
        
        # Normalize 1-10 scale to 0.0-1.0
        return (urgency - 1) / 9.0
    
    def _calculate_dependency_score(self, dependency_status: Optional[float]) -> float:
        """Calculate dependency satisfaction score."""
        if dependency_status is not None:
            return dependency_status
        
        # If no external dependency status provided, calculate from actual dependencies
        if not self.dependencies:
            return 1.0  # No dependencies = fully satisfied
        
        # Assume dependencies are tracked elsewhere; return partial score
        # In a real implementation, this would check actual task states
        return 0.5  # Default to partially satisfied
    
    def _calculate_resource_score(self, resource_requirements: Optional[Dict[str, Any]]) -> float:
        """Calculate resource efficiency score."""
        if resource_requirements is None:
            return 1.0  # Default to no resource concerns
        
        # Normalize resource requirements to score
        # Lower resource requirements = higher score
        total_resources = resource_requirements.get("totalResources", 10)
        available_resources = resource_requirements.get("availableResources", 10)
        
        if total_resources <= 0:
            return 1.0
        
        availability_ratio = available_resources / total_resources
        return availability_ratio
    
    def _calculate_value_score(self, expected_value: Optional[float]) -> float:
        """Calculate expected value score."""
        if expected_value is not None:
            return expected_value
        
        # Default value based on task description analysis
        # In a real implementation, this would analyze task content
        return 0.5  # Neutral default
    
    def add_dependency(self, dependency_id: UUID) -> None:
        """Add a dependency to this task."""
        if dependency_id not in self.dependencies:
            self.dependencies.append(dependency_id)
    
    def remove_dependency(self, dependency_id: UUID) -> bool:
        """Remove a dependency from this task. Returns True if dependency was found."""
        if dependency_id in self.dependencies:
            self.dependencies.remove(dependency_id)
            return True
        return False
    
    def has_dependencies(self) -> bool:
        """Check if this task has any dependencies."""
        return len(self.dependencies) > 0
    
    def can_execute(self, completed_task_ids: List[UUID]) -> bool:
        """
        Check if this task can be executed given completed tasks.
        
        Args:
            completed_task_ids: List of task IDs that have been completed
            
        Returns:
            True if all dependencies are satisfied, False otherwise
        """
        return all(dep_id in completed_task_ids for dep_id in self.dependencies)
    
    def get_status_transitions(self) -> List[str]:
        """Get list of valid status transitions from current state."""
        return self.VALID_TRANSITIONS.get(self.status, [])
    
    def can_transition_to(self, new_status: str) -> bool:
        """Check if transition to new status is valid from current status."""
        return new_status in self.get_status_transitions()
    
    def update_status(self, new_status: str) -> bool:
        """
        Attempt to update task status.
        
        Args:
            new_status: The desired new status
            
        Returns:
            True if status was updated, False if transition is invalid
        """
        if self.can_transition_to(new_status):
            old_status = self.status
            self.status = new_status
            self.metadata["statusTransitions"] = self.metadata.get("statusTransitions", [])
            self.metadata["statusTransitions"].append({
                "from": old_status,
                "to": new_status,
                "timestamp": datetime.utcnow().isoformat()
            })
            return True
        return False
    
    def get_priority_score(self) -> float:
        """Get current priority score."""
        return self.priorityScore
    
    def get_estimated_completion_time(
        self,
        base_duration_hours: float = 1.0
    ) -> datetime:
        """Calculate estimated completion time based on priority and dependencies."""
        if self.estimatedCompletion:
            return self.estimatedCompletion
        
        # Calculate estimated completion based on priority
        # Higher priority = shorter estimated duration
        priority_factor = max(0.1, self.priorityScore)
        adjusted_duration = base_duration_hours * (1 - priority_factor * 0.5)
        
        # Add estimated time from dependencies
        dependency_count = len(self.dependencies)
        dependency_adjustment = dependency_count * 0.5  # Assume 30 min per dependency
        
        estimated_time = datetime.utcnow() + timedelta(
            hours=adjusted_duration + dependency_adjustment
        )
        
        self.estimatedCompletion = estimated_time
        return estimated_time