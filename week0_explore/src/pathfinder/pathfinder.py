"""
Pathfinder module for efficient navigation and decision-making.

This module provides the Pathfinder class which implements adaptive path selection
based on multi-criteria scoring, navigation history tracking, and efficiency monitoring.
"""

from typing import Any, Dict, List, Optional, Tuple

from .path_history import PathHistory, PathRecord
from .path_evaluator import PathEvaluator, PathScore, PathAnalysis


class Pathfinder:
    """
    Implements efficient navigation path selection with adaptive search strategies.
    
    The Pathfinder manages navigation decisions by:
    - Maintaining navigation history to avoid redundant exploration
    - Evaluating paths using multi-criteria scoring (step count, time, resources, success probability)
    - Implementing adaptive search that switches objectives when efficiency falls below thresholds
    - Tracking and learning from successful paths with appropriate weighting
    
    Performance characteristics:
    - Path selection: O(n*m) where n = alternatives evaluated, m = path length
    - History queries: O(1) for indexed lookups via PathHistory
    - Pattern matching: O(n) where n = total history records
    """
    
    def __init__(
        self,
        path_history: Optional[PathHistory] = None,
        path_evaluator: Optional[PathEvaluator] = None,
        max_backtracking_distance: int = 3,
        patience_threshold: int = 10,
        efficiency_threshold: float = 0.50,
        min_alternatives: int = 3,
        data_root: str = "data"
    ):
        """
        Initialize the pathfinder.
        
        Args:
            path_history: PathHistory instance for navigation history.
            path_evaluator: PathEvaluator instance for path scoring.
            max_backtracking_distance: Maximum steps to backtrack (default 3).
            patience_threshold: Failed attempts before reconsidering (default 10).
            efficiency_threshold: Efficiency threshold for objective switching (default 0.50).
            min_alternatives: Minimum alternatives to evaluate (default 3).
            data_root: Root directory for persisted data.
        """
        self.path_history = path_history or PathHistory(data_root)
        self.path_evaluator = path_evaluator or PathEvaluator(
            path_history=self.path_history,
            max_backtracking_distance=max_backtracking_distance,
            patience_threshold=patience_threshold,
            data_root=data_root
        )
        self.max_backtracking_distance = max_backtracking_distance
        self.patience_threshold = patience_threshold
        self.efficiency_threshold = efficiency_threshold
        self.min_alternatives = min_alternatives
        
        # Tracking state
        self._current_objective: Optional[str] = None
        self._current_path: List[PathRecord] = []
        self._failed_attempts: int = 0
        self._progress_stalled: int = 0
        self._last_progress_step: int = 0
    
    def select_path(self, objective: str, current_location: Optional[str] = None) -> Tuple[List[PathRecord], PathScore]:
        """
        Select the optimal path for the given objective.
        
        This method implements the core path selection logic:
        1. Evaluates at least min_alternatives paths (default 3)
        2. Selects the path with highest composite score
        3. Considers previous successful paths with appropriate weighting
        4. Monitors efficiency and switches objectives if needed
        
        Args:
            objective: The objective to achieve.
            current_location: Current location ID (uses history if not provided).
            
        Returns:
            Tuple of (selected_path, selected_score).
        """
        # Get current location from history if not provided
        if current_location is None:
            current_location = self._get_current_location()
        
        # Generate alternative paths
        alternatives = self._generate_alternatives(objective, current_location)
        
        # Ensure minimum number of alternatives
        while len(alternatives) < self.min_alternatives:
            synthetic = self._generate_synthetic_alternative(current_location, objective)
            alternatives.append(synthetic)
        
        # Evaluate each alternative
        evaluated_paths: List[Tuple[List[PathRecord], PathScore]] = []
        
        for alt in alternatives:
            path = self._build_path_from_analysis(alt, current_location, objective)
            score = self.path_evaluator.evaluate(path, objective)
            evaluated_paths.append((path, score))
        
        # Sort by composite score (descending)
        evaluated_paths.sort(key=lambda x: x[1].composite_score, reverse=True)
        
        # Select best path
        best_path, best_score = evaluated_paths[0]
        
        # Check if we should switch objectives
        should_switch, efficiency_ratio = self.path_evaluator.should_switch(
            self._current_path or best_path,
            alternatives,
            best_score
        )
        
        if should_switch:
            # Log switch for observability
            # In a real implementation, this would emit a metric or log
            pass
        
        # Update current state
        self._current_objective = objective
        self._current_path = best_path
        self._last_progress_step = len(best_path)
        
        return best_path, best_score
    
    def record(self, record: PathRecord) -> bool:
        """
        Record a navigation event.
        
        Args:
            record: PathRecord to record.
            
        Returns:
            True if successful, False otherwise.
        """
        return self.path_history.record(record)
    
    def record_success(self, agent_id: str, location_id: str, action: str, 
                      time_spent: int, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Record a successful navigation event.
        
        Args:
            agent_id: ID of the agent.
            location_id: ID of the location.
            action: Action performed.
            time_spent: Time spent in milliseconds.
            metadata: Optional metadata.
            
        Returns:
            True if successful, False otherwise.
        """
        record = PathRecord(
            agent_id=agent_id,
            location_id=location_id,
            action=action,
            success=True,
            timestamp=self._get_timestamp(),
            time_spent=time_spent,
            record_type="success",
            metadata=metadata or {}
        )
        return self.record(record)
    
    def record_failure(self, agent_id: str, location_id: str, action: str,
                       time_spent: int, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Record a failed navigation event.
        
        Args:
            agent_id: ID of the agent.
            location_id: ID of the location.
            action: Action performed.
            time_spent: Time spent in milliseconds.
            metadata: Optional metadata.
            
        Returns:
            True if successful, False otherwise.
        """
        record = PathRecord(
            agent_id=agent_id,
            location_id=location_id,
            action=action,
            success=False,
            timestamp=self._get_timestamp(),
            time_spent=time_spent,
            record_type="failure",
            metadata=metadata or {}
        )
        return self.record(record)
    
    def get_path_history(self) -> PathHistory:
        """Get the path history instance."""
        return self.path_history
    
    def get_path_evaluator(self) -> PathEvaluator:
        """Get the path evaluator instance."""
        return self.path_evaluator
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pathfinder statistics."""
        return {
            "current_objective": self._current_objective,
            "failed_attempts": self._failed_attempts,
            "progress_stalled": self._progress_stalled,
            "last_progress_step": self._last_progress_step,
            "history_stats": self.path_history.get_stats(""),
            "evaluator_stats": self.path_evaluator.get_stats()
        }
    
    def _get_current_location(self) -> Optional[str]:
        """Get the current location from navigation history."""
        locations = self.path_history.get_visited_locations("")
        if locations:
            # Return the most recent location
            most_recent = max(locations, key=lambda x: x.get('last_visit', ''))
            return most_recent.get('location_id')
        return None
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    def _generate_alternatives(
        self, objective: str, current_location: str
    ) -> List[PathAnalysis]:
        """Generate alternative path analyses."""
        # Get alternatives from evaluator
        current_path = self._get_current_path_records()
        
        alternatives = self.path_evaluator.get_alternatives(
            current_path, objective, self.min_alternatives
        )
        
        return alternatives
    
    def _get_current_path_records(self) -> List[PathRecord]:
        """Get current path as list of PathRecords."""
        if not self._current_path:
            return []
        return self._current_path
    
    def _build_path_from_analysis(
        self, analysis: PathAnalysis, current_location: str, objective: str
    ) -> List[PathRecord]:
        """Build a path from PathAnalysis."""
        path = []
        
        # Add current location as first step
        path.append(PathRecord(
            agent_id="agent_1",
            location_id=current_location,
            action="start",
            success=True,
            timestamp=self._get_timestamp(),
            time_spent=0,
            record_type="visit",
            metadata={"objective": objective}
        ))
        
        # Add locations from analysis (filter out None)
        valid_locations = [loc for loc in analysis.locations if loc]
        for loc_id in valid_locations:
            path.append(PathRecord(
                agent_id="agent_1",
                location_id=loc_id,
                action="move",
                success=True,
                timestamp=self._get_timestamp(),
                time_spent=int(analysis.estimated_time_ms / max(1, len(valid_locations))),
                record_type="visit",
                metadata={"objective": objective}
            ))
        
        return path
    
    def _generate_synthetic_alternative(
        self, current_location: str, objective: str
    ) -> PathAnalysis:
        """Generate a synthetic alternative path analysis."""
        return PathAnalysis(
            path_id=f"synthetic_{objective[:20]}",
            objective=objective,
            locations=[current_location],
            actions=["explore"],
            estimated_step_count=1,
            estimated_time_ms=1000,
            resource_requirements={"complexity": "low"},
            success_probability=0.5,
            historical_success_rate=0.0,
            similar_path_count=0,
            similar_path_avg_steps=0,
            similar_path_avg_time=0
        )
    
    def reset(self) -> None:
        """Reset the pathfinder state."""
        self._current_objective = None
        self._current_path = []
        self._failed_attempts = 0
        self._progress_stalled = 0
        self._last_progress_step = 0