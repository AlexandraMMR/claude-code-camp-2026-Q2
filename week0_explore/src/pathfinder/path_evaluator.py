"""
Path Evaluator module for efficient navigation and decision-making.

This module provides the PathEvaluator class which implements multi-criteria
scoring for path evaluation, alternative path generation, and adaptive search
strategies based on efficiency metrics.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .path_history import PathHistory, PathRecord


@dataclass
class PathScore:
    """Represents the multi-criteria score for a path."""
    path_id: str
    composite_score: float
    step_count: float
    time_estimate: float
    resource_requirement: float
    success_probability: float
    weight_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class PathAnalysis:
    """Analysis of a path with evaluation metrics."""
    path_id: str
    objective: str
    locations: List[str]
    actions: List[str]
    estimated_step_count: int
    estimated_time_ms: int
    resource_requirements: Dict[str, Any]
    success_probability: float
    historical_success_rate: float = 0.0
    similar_path_count: int = 0
    similar_path_avg_steps: float = 0.0
    similar_path_avg_time: float = 0.0


class PathEvaluator:
    """
    Evaluates navigation paths using multi-criteria scoring and adaptive search strategies.
    
    The evaluator considers multiple factors when scoring paths:
    - Step count (40% weight): Fewer steps are preferred
    - Time estimate (30% weight): Faster paths are preferred
    - Resource requirements (20% weight): Lower resource usage is preferred
    - Success probability (10% weight): Higher success probability is preferred
    
    The evaluator also implements adaptive search strategies:
    - Tracks previous successful paths with weighted consideration
    - Switches objectives if current approach efficiency falls below 50% of alternatives
    - Configurable backtracking distance and patience threshold
    """
    
    def __init__(
        self,
        path_history: Optional[PathHistory] = None,
        max_backtracking_distance: int = 3,
        patience_threshold: int = 10,
        data_root: str = "data"
    ):
        """
        Initialize the path evaluator.
        
        Args:
            path_history: PathHistory instance for navigation history.
            max_backtracking_distance: Maximum steps to backtrack (default 3).
            patience_threshold: Failed attempts before reconsidering goal (default 10).
            data_root: Root directory for persisted data.
        """
        self.path_history = path_history or PathHistory(data_root)
        self.max_backtracking_distance = max_backtracking_distance
        self.patience_threshold = patience_threshold
        
        # Scoring weights as specified in requirements
        self.step_count_weight = 0.40
        self.time_estimate_weight = 0.30
        self.resource_requirement_weight = 0.20
        self.success_probability_weight = 0.10
        
        # Cache for recent evaluations
        self._evaluation_cache: Dict[str, PathScore] = {}
        self._cache_ttl_ms = 60000  # 1 minute TTL
    
    def evaluate(self, path: List[PathRecord], objective: str) -> PathScore:
        """
        Evaluate a path using multi-criteria scoring.
        
        Args:
            path: List of PathRecords representing the path to evaluate.
            objective: The objective the path is trying to achieve.
            
        Returns:
            PathScore with composite score and breakdown.
        """
        path_id = self._generate_path_id(path, objective)
        
        # Check cache first
        cache_key = f"{path_id}:{objective}"
        if cache_key in self._evaluation_cache:
            cache_entry = self._evaluation_cache[cache_key]
            # Check if cache is still valid (within TTL)
            if self._is_cache_valid(cache_entry):
                return cache_entry
        
        # Calculate individual criteria scores
        path_analysis = self._analyze_path(path, objective)
        
        # Normalize scores (0.0 to 1.0, where 1.0 is best)
        step_score = self._normalize_step_count(
            path_analysis.estimated_step_count,
            path_analysis.objective
        )
        
        time_score = self._normalize_time_estimate(
            path_analysis.estimated_time_ms,
            path_analysis.objective
        )
        
        resource_score = self._normalize_resource_requirement(
            path_analysis.resource_requirements,
            path_analysis.objective
        )
        
        success_score = self._normalize_success_probability(
            path_analysis.success_probability,
            path_analysis.historical_success_rate,
            path_analysis.objective
        )
        
        # Calculate composite score
        composite_score = (
            step_score * self.step_count_weight +
            time_score * self.time_estimate_weight +
            resource_score * self.resource_requirement_weight +
            success_score * self.success_probability_weight
        )
        
        score = PathScore(
            path_id=path_id,
            composite_score=composite_score,
            step_count=step_score,
            time_estimate=time_score,
            resource_requirement=resource_score,
            success_probability=success_score,
            weight_breakdown={
                "step_count": step_score,
                "time_estimate": time_score,
                "resource_requirement": resource_score,
                "success_probability": success_score
            }
        )
        
        # Cache the result
        self._evaluation_cache[cache_key] = score
        return score
    
    def get_alternatives(
        self,
        current_path: List[PathRecord],
        objective: str,
        count: int = 3
    ) -> List[PathAnalysis]:
        """
        Get alternative paths for evaluation.
        
        Args:
            current_path: The current path being evaluated.
            objective: The objective to achieve.
            count: Number of alternatives to return (default 3).
            
        Returns:
            List of alternative path analyses.
        """
        # Get similar successful paths from history
        similar_paths = self._find_similar_successful_paths(objective, count + 1)
        
        alternatives: List[PathAnalysis] = []
        
        # Generate alternatives based on historical patterns
        for path_data in similar_paths[:count]:
            analysis = self._create_path_analysis_from_history(
                path_data, objective
            )
            alternatives.append(analysis)
        
        # If not enough alternatives, generate synthetic ones
        while len(alternatives) < count:
            synthetic = self._generate_synthetic_alternative(current_path, objective)
            alternatives.append(synthetic)
        
        # Sort by success probability
        alternatives.sort(
            key=lambda a: a.success_probability + (a.historical_success_rate * 0.5),
            reverse=True
        )
        
        return alternatives[:count]
    
    def should_switch(
        self,
        current_path: List[PathRecord],
        alternatives: List[PathAnalysis],
        current_score: PathScore
    ) -> Tuple[bool, float]:
        """
        Determine if the agent should switch objectives based on efficiency.
        
        Args:
            current_path: The current path being evaluated.
            alternatives: List of alternative path analyses.
            current_score: Current path evaluation score.
            
        Returns:
            Tuple of (should_switch, efficiency_ratio).
            efficiency_ratio is current_score / avg_alternative_score.
        """
        if not alternatives:
            return False, 0.0
        
        # Calculate average alternative score
        alt_scores = [
            a.success_probability + (a.historical_success_rate * 0.5)
            for a in alternatives
        ]
        avg_alt_score = sum(alt_scores) / len(alt_scores)
        
        # Calculate efficiency ratio
        current_efficiency = current_score.composite_score
        efficiency_ratio = current_efficiency / avg_alt_score if avg_alt_score > 0 else 0.0
        
        # Switch if efficiency falls below 50% of alternatives
        should_switch = efficiency_ratio < 0.50
        
        return should_switch, efficiency_ratio
    
    def _generate_path_id(self, path: List[PathRecord], objective: str) -> str:
        """Generate a unique identifier for a path."""
        location_ids = [r.location_id for r in path if r.location_id]
        return f"path_{'_'.join(location_ids)}_{objective[:20]}"
    
    def _is_cache_valid(self, score: PathScore) -> bool:
        """Check if cached score is still valid (within TTL)."""
        # For now, always return True - cache is simple
        # In a more complex implementation, this would check timestamps
        return True
    
    def _analyze_path(self, path: List[PathRecord], objective: str) -> PathAnalysis:
        """Analyze a path and extract metrics."""
        if not path:
            return PathAnalysis(
                path_id="empty",
                objective=objective,
                locations=[],
                actions=[],
                estimated_step_count=1,
                estimated_time_ms=0,
                resource_requirements={},
                success_probability=0.5
            )
        
        locations = [r.location_id for r in path]
        actions = [r.action for r in path]
        
        # Calculate metrics
        step_count = len(path)
        total_time = sum(r.time_spent for r in path)
        
        # Calculate historical success rate for similar patterns
        historical_success = self._calculate_historical_success_rate(
            objective, locations, actions
        )
        
        # Estimate resource requirements based on path complexity
        resource_requirements = self._estimate_resource_requirements(
            path, objective
        )
        
        # Base success probability on historical data with confidence weighting
        if historical_success and historical_success.get('rate', 0) > 0:
            # Higher confidence in paths with more examples
            confidence = min(1.0, historical_success.get('count', 0) / 5.0)
            base_prob = historical_success['rate']
            success_prob = base_prob * confidence + 0.3 * (1 - confidence)
        else:
            success_prob = 0.5  # Default when no history
        
        return PathAnalysis(
            path_id=self._generate_path_id(path, objective),
            objective=objective,
            locations=locations,
            actions=actions,
            estimated_step_count=step_count,
            estimated_time_ms=total_time,
            resource_requirements=resource_requirements,
            success_probability=success_prob,
            historical_success_rate=historical_success['rate'] if historical_success else 0.0,
            similar_path_count=historical_success['count'] if historical_success else 0,
            similar_path_avg_steps=historical_success.get('avg_steps', 0),
            similar_path_avg_time=historical_success.get('avg_time_ms', 0)
        )
    
    def _find_similar_successful_paths(
        self, objective: str, count: int
    ) -> List[Dict[str, Any]]:
        """Find successful paths from history that match the objective."""
        # Get all history records
        history_data = self.path_history.get_visited_locations("")
        
        # Filter successful entries and group by location patterns
        success_patterns: Dict[str, List[Dict[str, Any]]] = {}
        
        for loc_data in history_data:
            if loc_data.get('successes', 0) > 0:
                loc_id = loc_data['location_id']
                success_count = loc_data['successes']
                total_count = loc_data['successes'] + loc_data.get('failures', 0)
                
                if total_count > 0:
                    pattern_key = f"success_{loc_id}"
                    if pattern_key not in success_patterns:
                        success_patterns[pattern_key] = []
                    
                    success_patterns[pattern_key].append({
                        'location_id': loc_id,
                        'success_count': success_count,
                        'total_count': total_count,
                        'success_rate': success_count / total_count
                    })
        
        # Sort by success rate and return top patterns
        all_patterns = []
        for pattern_list in success_patterns.values():
            all_patterns.extend(pattern_list)
        
        all_patterns.sort(key=lambda x: x['success_rate'], reverse=True)
        
        # Add historical stats to each pattern
        for pattern in all_patterns:
            pattern['historical_stats'] = self.path_history.get_patterns(
                "success_rate_by_location"
            )
        
        return all_patterns[:count]
    
    def _create_path_analysis_from_history(
        self, path_data: Dict[str, Any], objective: str
    ) -> PathAnalysis:
        """Create a PathAnalysis from historical data."""
        return PathAnalysis(
            path_id=f"historical_{path_data['location_id']}",
            objective=objective,
            locations=[path_data['location_id']],
            actions=[],
            estimated_step_count=1,
            estimated_time_ms=0,
            resource_requirements={},
            success_probability=path_data.get('success_rate', 0.5),
            historical_success_rate=path_data.get('success_rate', 0.0),
            similar_path_count=path_data.get('success_count', 0),
            similar_path_avg_steps=0,
            similar_path_avg_time=0
        )
    
    def _generate_synthetic_alternative(
        self, current_path: List[PathRecord], objective: str
    ) -> PathAnalysis:
        """Generate a synthetic alternative path."""
        if not current_path:
            return PathAnalysis(
                path_id="synthetic_empty",
                objective=objective,
                locations=[],
                actions=[],
                estimated_step_count=1,
                estimated_time_ms=0,
                resource_requirements={},
                success_probability=0.5
            )
        
        # Create a simpler alternative with fewer steps
        num_steps = max(1, len(current_path) // 2)
        new_locations = [
            r.location_id for r in current_path[:num_steps]
        ]
        
        # Estimate higher time and resources (simpler path might be less efficient)
        estimated_time = sum(r.time_spent for r in current_path[:num_steps])
        
        return PathAnalysis(
            path_id=f"synthetic_{num_steps}_steps",
            objective=objective,
            locations=new_locations,
            actions=[r.action for r in current_path[:num_steps]],
            estimated_step_count=num_steps,
            estimated_time_ms=estimated_time,
            resource_requirements={
                "complexity": "low",
                "estimated_steps": num_steps
            },
            success_probability=0.6,  # Slightly higher than average
            historical_success_rate=0.0,
            similar_path_count=0,
            similar_path_avg_steps=0,
            similar_path_avg_time=0
        )
    
    def _normalize_step_count(
        self, step_count: int, objective: str
    ) -> float:
        """Normalize step count to 0.0-1.0 scale (fewer is better)."""
        # Base expectation: 5 steps for simple objectives, 20 for complex
        base_expectation = 5 if len(objective) < 20 else 20
        
        # Calculate normalized score (fewer steps = higher score)
        # Score decreases as step count increases beyond expectation
        if step_count <= base_expectation:
            return 1.0 - (step_count / base_expectation) * 0.3
        else:
            # Penalize longer paths more heavily
            excess = step_count / base_expectation
            return max(0.1, 0.7 - (math.log(excess) * 0.2))
    
    def _normalize_time_estimate(
        self, time_ms: int, objective: str
    ) -> float:
        """Normalize time estimate to 0.0-1.0 scale (faster is better)."""
        # Base expectation: 1000ms per step
        base_expectation = 1000
        
        # Calculate normalized score
        if time_ms <= base_expectation:
            return 1.0 - (time_ms / base_expectation) * 0.3
        else:
            excess = time_ms / base_expectation
            return max(0.1, 0.7 - (math.log(excess) * 0.2))
    
    def _normalize_resource_requirement(
        self, resources: Dict[str, Any], objective: str
    ) -> float:
        """Normalize resource requirements to 0.0-1.0 scale (less is better)."""
        if not resources:
            return 1.0
        
        # Calculate resource score based on complexity indicators
        complexity = resources.get('complexity', 'medium')
        complexity_scores = {
            'low': 1.0,
            'medium': 0.7,
            'high': 0.4,
            'very_high': 0.2
        }
        
        return complexity_scores.get(complexity, 0.5)
    
    def _normalize_success_probability(
        self, success_prob: float, historical_rate: float, objective: str
    ) -> float:
        """Normalize success probability to 0.0-1.0 scale (higher is better)."""
        # Weight historical data if available
        if historical_rate > 0:
            # Blend historical rate with current estimate
            blended = (success_prob + historical_rate) / 2
            return blended
        
        return success_prob
    
    def _calculate_historical_success_rate(
        self, objective: str, locations: List[str], actions: List[str]
    ) -> Dict[str, float]:
        """Calculate historical success rate for similar patterns."""
        if not locations:
            return {'rate': 0.5, 'count': 0}
        
        # Get patterns from history
        patterns = self.path_history.get_patterns("success_rate_by_location")
        
        # Find matching locations
        matching_locations = patterns.get('location_rates', [])
        
        # Filter for our locations
        matching = [l for l in matching_locations if l['location_id'] in locations]
        
        if matching:
            total_successes = sum(l['successes'] for l in matching)
            total_attempts = sum(
                l['successes'] + l['failures'] for l in matching
            )
            
            if total_attempts > 0:
                return {
                    'rate': total_successes / total_attempts,
                    'count': len(matching),
                    'avg_steps': 0,
                    'avg_time_ms': 0
                }
        
        return {'rate': 0.5, 'count': 0}
    
    def _estimate_resource_requirements(
        self, path: List[PathRecord], objective: str
    ) -> Dict[str, Any]:
        """Estimate resource requirements for a path."""
        if not path:
            return {'complexity': 'low'}
        
        # Calculate path complexity based on length and variety
        step_count = len(path)
        unique_locations = len(set(r.location_id for r in path))
        unique_actions = len(set(r.action for r in path))
        
        # Determine complexity level
        if step_count <= 3 and unique_locations <= 2:
            complexity = 'low'
        elif step_count <= 8 and unique_locations <= 4:
            complexity = 'medium'
        elif step_count <= 15:
            complexity = 'high'
        else:
            complexity = 'very_high'
        
        return {
            'complexity': complexity,
            'step_count': step_count,
            'unique_locations': unique_locations,
            'unique_actions': unique_actions,
            'estimated_memory_mb': step_count * 0.1
        }
    
    def clear_cache(self) -> None:
        """Clear the evaluation cache."""
        self._evaluation_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get evaluator statistics."""
        return {
            "max_backtracking_distance": self.max_backtracking_distance,
            "patience_threshold": self.patience_threshold,
            "cache_size": len(self._evaluation_cache),
            "weights": {
                "step_count": self.step_count_weight,
                "time_estimate": self.time_estimate_weight,
                "resource_requirement": self.resource_requirement_weight,
                "success_probability": self.success_probability_weight
            }
        }
