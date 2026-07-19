"""Path history tracking for the Pathfinder component.

This module implements the PathHistory class which maintains navigation history
for the AI agent. It records visited locations, attempted actions, successful
outcomes, and time spent per location to enable pattern analysis and avoid
redundant exploration.

The history is persisted to JSON files in the data/history/ directory using
the index_manager for atomic writes and efficient lookups.

Performance characteristics:
- Single-key lookup: O(1) for visited locations and attempts
- Pattern queries: O(n) where n = total records
- Persistence: Atomic with file locking via index_manager
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

from ..data.index_manager import IndexManager, IndexType


class RecordType(Enum):
    """Types of path records."""
    VISIT = "visit"
    ATTEMPT = "attempt"
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class PathRecord:
    """Represents a single path record in the navigation history."""
    agent_id: str
    location_id: str
    action: str
    success: bool
    timestamp: str
    time_spent: int  # milliseconds
    record_type: str = "visit"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PathRecord':
        """Create instance from dictionary."""
        return cls(
            agent_id=data['agent_id'],
            location_id=data['location_id'],
            action=data['action'],
            success=data['success'],
            timestamp=data['timestamp'],
            time_spent=data['time_spent'],
            record_type=data.get('record_type', 'visit'),
            metadata=data.get('metadata', {})
        )
    
    def to_index_record(self) -> Dict[str, Any]:
        """Convert to index record format for storage."""
        return {
            'agent_id': self.agent_id,
            'location_id': self.location_id,
            'action': self.action,
            'success': self.success,
            'timestamp': self.timestamp,
            'time_spent': self.time_spent,
            'record_type': self.record_type,
            'metadata': self.metadata
        }


class PathHistory:
    """Manages navigation history for the Pathfinder component.
    
    This class provides methods to record and query navigation history,
    including visited locations, attempted actions, and successful outcomes.
    It uses the index_manager for persistent storage and efficient lookups.
    
    The history is stored in JSON files under data/history/ with agent-specific
    naming ({agent_id}_path_history.json).
    
    Usage:
        history = PathHistory()
        history.record(PathRecord(...))
        locations = history.get_visited_locations("agent_1")
        attempts = history.get_attempts("room_123")
        patterns = history.get_patterns("locations_visited_more_than_3")
    """
    
    def __init__(self, data_root: str = "data"):
        """Initialize the path history manager.
        
        Args:
            data_root: Root directory for persisted data files.
        """
        self.data_root = Path(data_root)
        self.history_dir = self.data_root / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.index_manager = IndexManager(str(self.data_root))
        
        # Track agent-specific history files
        self._agent_history_files: Dict[str, Path] = {}
        
        # Ensure history directory exists
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_history_file(self, agent_id: str) -> Path:
        """Get the history file path for an agent.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            Path to the agent's history file.
        """
        if agent_id not in self._agent_history_files:
            self._agent_history_files[agent_id] = (
                self.history_dir / f"{agent_id}_path_history.json"
            )
        return self._agent_history_files[agent_id]
    
    def _load_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """Load history records for an agent from disk.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            List of history records.
        """
        history_file = self._get_history_file(agent_id)
        
        if not history_file.exists():
            return []
        
        try:
            with open(history_file, 'r') as f:
                data = json.load(f)
                return data.get('records', [])
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_history(self, agent_id: str, records: List[Dict[str, Any]]) -> bool:
        """Save history records for an agent to disk.
        
        Args:
            agent_id: ID of the agent.
            records: List of history records to save.
            
        Returns:
            True if successful, False otherwise.
        """
        history_file = self._get_history_file(agent_id)
        
        try:
            # Use atomic write pattern
            temp_file = history_file.with_suffix('.json.tmp')
            
            data = {
                'records': records,
                'last_updated': datetime.utcnow().isoformat(),
                'record_count': len(records)
            }
            
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic move: temp file to final file
            temp_file.replace(history_file)
            return True
        except (IOError, OSError):
            return False
    
    def get_visited_locations(self, agent_id: str, min_visits: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of locations visited by an agent.
        
        Args:
            agent_id: ID of the agent.
            min_visits: Optional minimum visit count filter.
            
        Returns:
            List of visited locations with metadata including visit count.
        """
        history = self._load_history(agent_id)
        
        # Aggregate by location
        location_counts: Dict[str, Dict[str, Any]] = {}
        
        for record in history:
            if record.get('record_type') in ['visit', 'success']:
                loc_id = record['location_id']
                if loc_id not in location_counts:
                    location_counts[loc_id] = {
                        'location_id': loc_id,
                        'visit_count': 0,
                        'first_visit': record['timestamp'],
                        'last_visit': record['timestamp'],
                        'total_time_spent': 0,
                        'actions': set(),
                        'successes': 0,
                        'failures': 0
                    }
                
                loc = location_counts[loc_id]
                loc['visit_count'] += 1
                loc['total_time_spent'] += record.get('time_spent', 0)
                loc['actions'].add(record['action'])
                
                if record['timestamp'] < loc['first_visit']:
                    loc['first_visit'] = record['timestamp']
                if record['timestamp'] > loc['last_visit']:
                    loc['last_visit'] = record['timestamp']
                
                if record['success']:
                    loc['successes'] += 1
                else:
                    loc['failures'] += 1
        
        # Convert sets to lists for JSON serialization
        result = []
        for loc in location_counts.values():
            loc['actions'] = list(loc['actions'])
            if min_visits is None or loc['visit_count'] >= min_visits:
                result.append(loc)
        
        return result
    
    def get_attempts(self, location_id: str, agent_id: Optional[str] = None, 
                     success_only: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get action attempts for a location.
        
        Args:
            location_id: ID of the location.
            agent_id: Optional agent ID to filter by.
            success_only: Optional filter for success status.
            
        Returns:
            List of action attempts with metadata.
        """
        # Load all agent histories
        all_records: List[Dict[str, Any]] = []
        
        if agent_id:
            all_records.extend(self._load_history(agent_id))
        else:
            # Load all agent history files
            for history_file in self.history_dir.glob("*_path_history.json"):
                all_records.extend(self._load_history(history_file.stem.replace('_path_history', '')))
        
        # Filter by location
        attempts = [
            r for r in all_records 
            if r['location_id'] == location_id 
            and r.get('record_type') in ['attempt', 'success', 'failure']
        ]
        
        # Apply success filter
        if success_only is not None:
            attempts = [r for r in attempts if r['success'] == success_only]
        
        return attempts
    
    def get_patterns(self, query: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Query for patterns in navigation history.
        
        Supported queries:
        - "locations_visited_more_than_N": Find locations visited more than N times
        - "most_visited_locations": Sort locations by visit count
        - "fastest_locations": Find locations with lowest average time spent
        - "success_rate_by_location": Success rates per location
        - "repeated_actions": Actions repeated at same location
        
        Args:
            query: Pattern query string.
            agent_id: Optional agent ID to filter by.
            
        Returns:
            Pattern results as dictionary.
        """
        # Load all records
        all_records: List[Dict[str, Any]] = []
        
        if agent_id:
            all_records.extend(self._load_history(agent_id))
        else:
            for history_file in self.history_dir.glob("*_path_history.json"):
                agent = history_file.stem.replace('_path_history', '')
                all_records.extend(self._load_history(agent))
        
        # Parse query
        if query.startswith("locations_visited_more_than_"):
            try:
                threshold = int(query.split("_")[-1])
                locations = self.get_visited_locations(agent_id or "", min_visits=threshold)
                return {
                    "query": query,
                    "threshold": threshold,
                    "matching_locations": locations,
                    "count": len(locations)
                }
            except ValueError:
                return {
                    "query": query,
                    "error": "Invalid threshold value",
                    "matching_locations": [],
                    "count": 0
                }
        
        elif query == "most_visited_locations":
            locations = self.get_visited_locations(agent_id or "")
            locations.sort(key=lambda x: x['visit_count'], reverse=True)
            return {
                "query": query,
                "sorted_locations": locations,
                "count": len(locations)
            }
        
        elif query == "fastest_locations":
            locations = self.get_visited_locations(agent_id or "")
            for loc in locations:
                if loc['visit_count'] > 0:
                    loc['avg_time_per_visit'] = loc['total_time_spent'] / loc['visit_count']
            locations.sort(key=lambda x: x.get('avg_time_per_visit', float('inf')))
            return {
                "query": query,
                "sorted_locations": locations,
                "count": len(locations)
            }
        
        elif query == "success_rate_by_location":
            locations = self.get_visited_locations(agent_id or "")
            for loc in locations:
                total = loc['successes'] + loc['failures']
                if total > 0:
                    loc['success_rate'] = loc['successes'] / total
                else:
                    loc['success_rate'] = 0.0
            return {
                "query": query,
                "location_rates": locations,
                "count": len(locations)
            }
        
        elif query == "repeated_actions":
            # Find actions repeated at same location
            action_counts: Dict[str, Dict[str, Any]] = {}
            
            for record in all_records:
                key = (record['location_id'], record['action'])
                if key not in action_counts:
                    action_counts[key] = {
                        'location_id': record['location_id'],
                        'action': record['action'],
                        'count': 0,
                        'first_seen': record['timestamp'],
                        'last_seen': record['timestamp']
                    }
                
                ac = action_counts[key]
                ac['count'] += 1
                if record['timestamp'] < ac['first_seen']:
                    ac['first_seen'] = record['timestamp']
                if record['timestamp'] > ac['last_seen']:
                    ac['last_seen'] = record['timestamp']
            
            repeated = [ac for ac in action_counts.values() if ac['count'] > 1]
            repeated.sort(key=lambda x: x['count'], reverse=True)
            
            return {
                "query": query,
                "repeated_actions": repeated,
                "count": len(repeated)
            }
        
        else:
            return {
                "query": query,
                "error": "Unknown query type",
                "count": 0
            }
    
    def record(self, record: PathRecord) -> bool:
        """Record a navigation event.
        
        Args:
            record: PathRecord to record.
            
        Returns:
            True if successful, False otherwise.
        """
        # Load existing history
        history = self._load_history(record.agent_id)
        
        # Add new record
        history.append(record.to_index_record())
        
        # Save to disk
        return self._save_history(record.agent_id, history)
    
    def clear_history(self, agent_id: str) -> bool:
        """Clear all history for an agent.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            True if successful, False otherwise.
        """
        history_file = self._get_history_file(agent_id)
        
        try:
            if history_file.exists():
                history_file.unlink()
            if agent_id in self._agent_history_files:
                del self._agent_history_files[agent_id]
            return True
        except (IOError, OSError):
            return False
    
    def get_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get navigation statistics for an agent.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            Dictionary of navigation statistics.
        """
        locations = self.get_visited_locations(agent_id)
        
        total_visits = sum(loc['visit_count'] for loc in locations)
        unique_locations = len(locations)
        total_time = sum(loc['total_time_spent'] for loc in locations)
        total_successes = sum(loc['successes'] for loc in locations)
        total_failures = sum(loc['failures'] for loc in locations)
        
        return {
            "agent_id": agent_id,
            "total_visits": total_visits,
            "unique_locations": unique_locations,
            "total_time_spent_ms": total_time,
            "successes": total_successes,
            "failures": total_failures,
            "success_rate": total_successes / (total_successes + total_failures) if (total_successes + total_failures) > 0 else 0.0
        }


# Global instance for convenience
_path_history: Optional[PathHistory] = None


def get_path_history(data_root: str = "data") -> PathHistory:
    """Get or create the global path history instance.
    
    Args:
        data_root: Root directory for persisted data.
        
    Returns:
        Global PathHistory instance.
    """
    global _path_history
    
    if _path_history is None:
        _path_history = PathHistory(data_root)
    
    return _path_history


def reset_path_history() -> None:
    """Reset the global path history instance."""
    global _path_history
    _path_history = None
