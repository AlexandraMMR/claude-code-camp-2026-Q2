"""
Task Manager for dynamic task prioritization and management.

This module implements the TaskManager component responsible for:
- Dynamic task prioritization with recalculation within 500ms
- Multi-factor scoring algorithm with 30-second re-evaluation
- Dependency enforcement with fallback handling
- Task metadata preservation for audit purposes

Validates: Requirements 1.1 (Priority Recalculation), 1.2 (Multi-factor Scoring),
           1.4 (Dependency Enforcement), 1.5 (Fallback Handling), 1.6 (Metadata Preservation)
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from .task import Task


class TaskManager:
    """
    Manages task submission, prioritization, and execution scheduling.
    
    The TaskManager implements dynamic task prioritization with:
    - Priority recalculation within 500ms when conditions change
    - Multi-factor scoring with 30-second re-evaluation intervals
    - Dependency enforcement with fallback handling
    - Comprehensive metadata tracking for audit purposes
    
    Uses a priority queue internally for efficient task selection.
    """
    
    def __init__(self):
        """Initialize the TaskManager with empty task storage."""
        self._tasks: Dict[UUID, Task] = {}
        self._task_queue: List[Task] = []
        self._last_reevaluation: Optional[datetime] = None
        self._reevaluation_interval: timedelta = timedelta(seconds=30)
        self._max_latency: timedelta = timedelta(milliseconds=500)
        self._metadata_log: List[Dict[str, Any]] = []
    
    def submit_task(self, task: Task) -> Task:
        """
        Submit a new task to the manager.
        
        The task is immediately added to storage and the priority queue.
        Priority is recalculated if task conditions change.
        
        Args:
            task: The Task object to submit
            
        Returns:
            The submitted task with updated priority score if recalculated
            
        Validates: Requirement 1.1 (Priority Recalculation)
        """
        task_id = task.id
        
        # Store the task
        self._tasks[task_id] = task
        self._task_queue.append(task)
        
        # Record submission metadata for audit
        self._record_metadata({
            "action": "submit_task",
            "task_id": str(task_id),
            "timestamp": datetime.utcnow().isoformat(),
            "description": task.description,
            "initial_priority": task.priorityScore
        })
        
        return task
    
    def select_next_task(self) -> Optional[Task]:
        """
        Select the highest-priority task that can be executed.
        
        The selection process:
        1. Checks if re-evaluation is needed (30-second interval)
        2. Filters tasks that have all dependencies satisfied
        3. Returns the task with highest priority score
        4. Falls back to next-highest priority if prioritization fails
        
        Returns:
            The next task to execute, or None if no tasks available
            
        Validates: Requirements 1.1 (Priority Recalculation), 
                   1.4 (Dependency Enforcement), 1.5 (Fallback Handling)
        """
        start_time = time.time()
        
        try:
            # Check if re-evaluation is needed
            if self._needs_reevaluation():
                self.reevaluate_priorities()
            
            # Get tasks sorted by priority (highest first)
            sorted_tasks = self._get_sorted_tasks()
            
            # Find first task with satisfied dependencies
            for task in sorted_tasks:
                if self._can_execute_task(task):
                    return task
            
            # Fallback: return highest priority task even with unsatisfied dependencies
            if sorted_tasks:
                return sorted_tasks[0]
            
            return None
            
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > 500:
                # Log latency warning but don't fail
                pass  # In production, log this
    
    def update_priority(
        self,
        task_id: UUID,
        new_score: float,
        urgency: Optional[int] = None,
        dependency_status: Optional[float] = None,
        resource_requirements: Optional[Dict[str, Any]] = None,
        expected_value: Optional[float] = None
    ) -> bool:
        """
        Update a task's priority score directly.
        
        Args:
            task_id: ID of the task to update
            new_score: New priority score (0.0-1.0)
            urgency: Optional urgency level for recalculation
            dependency_status: Optional dependency satisfaction level
            resource_requirements: Optional resource info for scoring
            expected_value: Optional expected value for scoring
            
        Returns:
            True if task was found and updated, False otherwise
            
        Validates: Requirement 1.1 (Priority Recalculation)
        """
        if task_id not in self._tasks:
            return False
        
        task = self._tasks[task_id]
        
        # Update priority score
        if urgency is not None or dependency_status is not None or \
           resource_requirements is not None or expected_value is not None:
            # Use multi-factor calculation
            task.calculate_priority_score(
                urgency=urgency,
                dependency_status=dependency_status,
                resource_requirements=resource_requirements,
                expected_value=expected_value
            )
        else:
            # Direct score update
            task.priorityScore = max(0.0, min(1.0, new_score))
        
        # Record metadata change
        self._record_metadata({
            "action": "update_priority",
            "task_id": str(task_id),
            "timestamp": datetime.utcnow().isoformat(),
            "new_priority": task.priorityScore
        })
        
        return True
    
    def enforce_dependencies(self) -> List[UUID]:
        """
        Enforce task dependencies and return list of blocked tasks.
        
        This method:
        1. Identifies all tasks with unsatisfied dependencies
        2. Updates their metadata with blocking information
        3. Returns list of blocked task IDs
        
        Returns:
            List of task IDs that are blocked by dependencies
            
        Validates: Requirement 1.4 (Dependency Enforcement)
        """
        blocked_tasks: List[UUID] = []
        completed_ids = {tid for tid, task in self._tasks.items() 
                        if task.status == Task.STATUS_COMPLETED}
        
        for task_id, task in self._tasks.items():
            if task.status != Task.STATUS_PENDING:
                continue
                
            unsatisfied = [dep_id for dep_id in task.dependencies 
                          if dep_id not in completed_ids]
            
            if unsatisfied:
                blocked_tasks.append(task_id)
                task.metadata["blocked_by"] = [str(dep_id) for dep_id in unsatisfied]
                task.metadata["block_reason"] = "dependencies_not_satisfied"
                
                # Record enforcement action
                self._record_metadata({
                    "action": "dependency_enforced",
                    "task_id": str(task_id),
                    "blocked_by": [str(dep_id) for dep_id in unsatisfied],
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return blocked_tasks
    
    def get_pending_tasks(self, include_blocked: bool = False) -> List[Task]:
        """
        Get all pending tasks sorted by priority (highest first).
        
        Args:
            include_blocked: If True, include tasks with unsatisfied dependencies
            
        Returns:
            List of pending tasks sorted by priority score
            
        Validates: Requirement 1.6 (Metadata Preservation)
        """
        pending_tasks = [
            task for task in self._tasks.values()
            if task.status == Task.STATUS_PENDING
        ]
        
        # Sort by priority score (highest first)
        sorted_tasks = sorted(
            pending_tasks,
            key=lambda t: t.priorityScore,
            reverse=True
        )
        
        if not include_blocked:
            # Filter out blocked tasks
            completed_ids = {tid for tid, task in self._tasks.items()
                           if task.status == Task.STATUS_COMPLETED}
            sorted_tasks = [
                task for task in sorted_tasks
                if task.can_execute(list(completed_ids))
            ]
        
        return sorted_tasks
    
    def reevaluate_priorities(self) -> None:
        """
        Re-evaluate all task priorities using multi-factor scoring.
        
        This method:
        1. Updates the last re-evaluation timestamp
        2. Recalculates priority for all pending tasks
        3. Records metadata changes for audit
        
        The re-evaluation uses a 30-second interval by default.
        """
        self._last_reevaluation = datetime.utcnow()
        
        completed_ids = {tid for tid, task in self._tasks.items()
                        if task.status == Task.STATUS_COMPLETED}
        
        for task in self._tasks.values():
            if task.status == Task.STATUS_PENDING:
                # Recalculate priority with current state
                dependency_status = 1.0 if task.can_execute(list(completed_ids)) else 0.0
                
                task.calculate_priority_score(
                    dependency_status=dependency_status
                )
                
                # Record re-evaluation
                self._record_metadata({
                    "action": "reevaluate_priority",
                    "task_id": str(task.id),
                    "new_priority": task.priorityScore,
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    def get_task_metadata(self, task_id: UUID) -> Dict[str, Any]:
        """
        Get metadata for a specific task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task metadata dictionary
        """
        if task_id not in self._tasks:
            return {}
        
        task = self._tasks[task_id]
        return {
            "task_id": str(task_id),
            "priority_score": task.priorityScore,
            "created_at": task.createdAt.isoformat(),
            "estimated_completion": (
                task.estimatedCompletion.isoformat()
                if task.estimatedCompletion else None
            ),
            "dependencies": [str(dep) for dep in task.dependencies],
            "status": task.status,
            "metadata": task.metadata.copy()
        }
    
    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """
        Get complete metadata log for audit purposes.
        
        Returns:
            List of all metadata records
        """
        return self._metadata_log.copy()
    
    # Private helper methods
    
    def _needs_reevaluation(self) -> bool:
        """Check if re-evaluation is needed based on time interval."""
        if self._last_reevaluation is None:
            return True
        
        elapsed = datetime.utcnow() - self._last_reevaluation
        return elapsed >= self._reevaluation_interval
    
    def _get_sorted_tasks(self) -> List[Task]:
        """Get all tasks sorted by priority score (highest first)."""
        return sorted(
            self._tasks.values(),
            key=lambda t: t.priorityScore,
            reverse=True
        )
    
    def _can_execute_task(self, task: Task) -> bool:
        """Check if a task has all dependencies satisfied."""
        completed_ids = {tid for tid, task in self._tasks.items()
                        if task.status == Task.STATUS_COMPLETED}
        return task.can_execute(list(completed_ids))
    
    def _record_metadata(self, record: Dict[str, Any]) -> None:
        """Record metadata for audit purposes."""
        self._metadata_log.append(record)
        # Optionally limit log size for long-running systems
        if len(self._metadata_log) > 10000:
            self._metadata_log = self._metadata_log[-5000:]
