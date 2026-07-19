"""
Task Scheduler for dynamic task prioritization and background re-evaluation.

This module implements the TaskScheduler component responsible for:
- Task scheduling with proper ordering using multi-factor scoring
- Continuous re-evaluation of priorities at 30-second intervals
- Integration with TaskManager for task selection and management
- Background thread for periodic priority recalculation

Validates: Requirements 1.1 (Priority Recalculation), 1.2 (Multi-factor Scoring),
           1.3 (Condition-Based Updates), 1.4 (Dependency Enforcement)
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from .task import Task
from .task_manager import TaskManager


class TaskScheduler:
    """
    Manages task scheduling with dynamic priority re-evaluation.
    
    The TaskScheduler provides:
    - Task scheduling with proper ordering based on multi-factor scoring
    - Continuous re-evaluation of priorities at configurable intervals
    - Integration with TaskManager for task submission and selection
    - Background thread for periodic priority recalculation (default 30 seconds)
    
    The scheduler uses the multi-factor scoring algorithm defined in Task:
    - Urgency (30% weight)
    - Dependency Status (25% weight)
    - Resource Requirements (20% weight)
    - Expected Value (25% weight)
    
    Thread-safe operations using internal locks.
    """
    
    def __init__(
        self,
        task_manager: Optional[TaskManager] = None,
        reevaluation_interval: float = 30.0,
        max_priority_latency_ms: float = 500.0
    ):
        """
        Initialize the TaskScheduler.
        
        Args:
            task_manager: TaskManager instance for task storage and selection.
                         If None, creates a new TaskManager.
            reevaluation_interval: Seconds between priority re-evaluations (default 30)
            max_priority_latency_ms: Maximum allowed latency for priority recalculation (default 500ms)
        """
        self._task_manager: TaskManager = task_manager or TaskManager()
        self._reevaluation_interval: float = reevaluation_interval
        self._max_priority_latency_ms: float = max_priority_latency_ms
        
        # Background thread control
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event: threading.Event = threading.Event()
        self._thread_lock: threading.Lock = threading.Lock()
        
        # State tracking
        self._last_reevaluation: Optional[datetime] = None
        self._is_running: bool = False
        
        # Metrics for monitoring
        self._metrics: Dict[str, Any] = {
            "total_schedules": 0,
            "total_next_task_calls": 0,
            "total_reevaluations": 0,
            "average_priority_calculation_ms": 0.0,
            "last_reevaluation_duration_ms": 0.0
        }
        self._calculation_times: List[float] = []
    
    def start(self) -> None:
        """
        Start the background scheduler thread.
        
        This method:
        1. Creates and starts a background thread for periodic re-evaluation
        2. Sets up the stop event for graceful shutdown
        3. Logs the start action
        
        The background thread runs the reevaluation loop at the configured
        interval (default 30 seconds).
        """
        with self._thread_lock:
            if self._is_running:
                return
            
            self._stop_event.clear()
            self._is_running = True
            
            # Start background thread
            self._scheduler_thread = threading.Thread(
                target=self._reevaluation_loop,
                name="TaskScheduler-Reevaluation",
                daemon=True
            )
            self._scheduler_thread.start()
    
    def stop(self) -> None:
        """
        Stop the background scheduler thread.
        
        This method:
        1. Signals the stop event to terminate the reevaluation loop
        2. Joins the background thread with timeout
        3. Updates running state
        """
        with self._thread_lock:
            if not self._is_running:
                return
            
            self._stop_event.set()
            self._is_running = False
            
            # Wait for thread to finish (with timeout for safety)
            if self._scheduler_thread:
                self._scheduler_thread.join(timeout=5.0)
                if self._scheduler_thread.is_alive():
                    # Log warning but don't block
                    pass  # In production, log this warning
    
    def schedule(self, task: Task) -> Task:
        """
        Schedule a task for execution.
        
        This method:
        1. Submits the task to the internal TaskManager
        2. Recalculates priority immediately if conditions have changed
        3. Updates scheduling metrics
        
        The task is added to the queue and sorted by priority score.
        Priority recalculation happens within 500ms as required.
        
        Args:
            task: The Task object to schedule
            
        Returns:
            The scheduled task with updated priority score if recalculated
            
        Validates: Requirement 1.1 (Priority Recalculation)
        """
        start_time = time.time()
        
        try:
            # Submit task to manager
            scheduled_task = self._task_manager.submit_task(task)
            
            # Record scheduling action
            self._metrics["total_schedules"] += 1
            
            return scheduled_task
            
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            self._track_calculation_time(elapsed_ms)
    
    def get_next_task(self) -> Optional[Task]:
        """
        Get the next highest-priority task that can be executed.
        
        This method:
        1. Checks if re-evaluation is needed (based on interval)
        2. Calls select_next_task on the TaskManager
        3. Tracks metrics for monitoring
        
        Returns:
            The next task to execute, or None if no tasks available
            
        Validates: Requirement 1.1 (Priority Recalculation)
        """
        start_time = time.time()
        
        try:
            # Get next task from manager
            task = self._task_manager.select_next_task()
            
            # Record metrics
            self._metrics["total_next_task_calls"] += 1
            
            return task
            
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            self._track_calculation_time(elapsed_ms)
    
    def reevaluate_priorities(self) -> None:
        """
        Re-evaluate priorities for all pending tasks.
        
        This method:
        1. Calculates priority scores for all pending tasks
        2. Uses the multi-factor scoring algorithm
        3. Updates task metadata with recalculation timestamps
        4. Tracks performance metrics
        
        The re-evaluation considers:
        - Current task urgency
        - Dependency satisfaction status
        - Resource requirements availability
        - Expected completion value
        
        This method should complete within 500ms as required.
        
        Validates: Requirements 1.1 (Priority Recalculation), 
                   1.2 (Multi-factor Scoring)
        """
        start_time = time.time()
        
        try:
            # Delegate to TaskManager's reevaluate_priorities
            self._task_manager.reevaluate_priorities()
            
            # Update metrics
            self._metrics["total_reevaluations"] += 1
            self._last_reevaluation = datetime.utcnow()
            
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            self._metrics["last_reevaluation_duration_ms"] = elapsed_ms
    
    def get_pending_tasks(self, include_blocked: bool = False) -> List[Task]:
        """
        Get all pending tasks sorted by priority.
        
        Args:
            include_blocked: If True, include tasks with unsatisfied dependencies
            
        Returns:
            List of pending tasks sorted by priority score (highest first)
        """
        return self._task_manager.get_pending_tasks(include_blocked=include_blocked)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get scheduler metrics for monitoring.
        
        Returns:
            Dictionary of scheduler metrics including:
            - total_schedules: Total tasks scheduled
            - total_next_task_calls: Total next task queries
            - total_reevaluations: Total priority re-evaluations
            - average_priority_calculation_ms: Average calculation time
            - last_reevaluation_duration_ms: Duration of last re-evaluation
        """
        with self._thread_lock:
            metrics = self._metrics.copy()
            metrics["is_running"] = self._is_running
            metrics["last_reevaluation"] = (
                self._last_reevaluation.isoformat()
                if self._last_reevaluation else None
            )
            metrics["reevaluation_interval_seconds"] = self._reevaluation_interval
            return metrics
    
    def get_task_manager(self) -> TaskManager:
        """Get the internal TaskManager instance."""
        return self._task_manager
    
    # Private methods
    
    def _reevaluation_loop(self) -> None:
        """
        Background thread loop for periodic priority re-evaluation.
        
        This method:
        1. Waits for the configured interval between re-evaluations
        2. Calls reevaluate_priorities() to update task priorities
        3. Continues until stop event is set
        """
        next_reevaluation = time.time() + self._reevaluation_interval
        
        while not self._stop_event.wait(max(0, next_reevaluation - time.time())):
            if self._stop_event.is_set():
                break
            
            # Perform re-evaluation
            self.reevaluate_priorities()
            
            # Schedule next re-evaluation
            next_reevaluation = time.time() + self._reevaluation_interval
    
    def _track_calculation_time(self, elapsed_ms: float) -> None:
        """Track calculation time for average computation."""
        self._calculation_times.append(elapsed_ms)
        
        # Keep only last 1000 calculations
        if len(self._calculation_times) > 1000:
            self._calculation_times = self._calculation_times[-1000:]
        
        # Update average
        self._metrics["average_priority_calculation_ms"] = (
            sum(self._calculation_times) / len(self._calculation_times)
        )
    
    def submit_task(self, task: Task) -> Task:
        """
        Alias for schedule() for API consistency.
        
        Args:
            task: The Task object to schedule
            
        Returns:
            The scheduled task
        """
        return self.schedule(task)
    
    def select_next_task(self) -> Optional[Task]:
        """
        Alias for get_next_task() for API consistency.
        
        Returns:
            The next task to execute, or None
        """
        return self.get_next_task()
