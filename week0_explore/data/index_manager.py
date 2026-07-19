"""Index manager for efficient in-memory lookups with file persistence.

This module provides a centralized index management system for the agent's
memory stores. It maintains in-memory dictionaries for fast O(1) lookups
while persisting data to JSON files for durability.

The index supports multiple entity types:
- locations: World locations
- objects: World objects
- npcs: Non-player characters
- quests: Quest information
- connections: Map connections between locations
- skills: Agent skills
- personas: Exploration personas

Performance targets:
- Single-key lookup: <100ms for 10,000+ records
- Atomic writes: File locking with temp file + rename pattern
- Index rebuild: From file system on startup

Cross-platform file locking is handled via the portalocker library for 
cross-platform compatibility, with fallback to a simple lock file approach.
"""

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum

# Try to import portalocker for cross-platform file locking
try:
    import portalocker
    HAS_PORTALOCKER = True
except ImportError:
    HAS_PORTALOCKER = False


class FileLock:
    """Context manager for file-based locking.
    
    Provides cross-platform file locking using either portalocker (if available)
    or a simple polling-based approach with lock files.
    """
    
    def __init__(self, lock_file_path: str, timeout: float = 5.0, poll_interval: float = 0.1):
        self.lock_file_path = lock_file_path
        self.lock_file = None
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._locked = False
    
    def acquire(self) -> bool:
        """Acquire file lock, returns False if lock cannot be acquired within timeout."""
        start_time = time.time()
        
        # Try portalocker first if available
        if HAS_PORTALOCKER:
            try:
                self.lock_file = open(self.lock_file_path, 'w')
                portalocker.lock(self.lock_file, portalocker.LOCK_EX | portalocker.LOCK_NB)
                self._locked = True
                return True
            except (IOError, OSError, portalocker.exceptions.LockException):
                if self.lock_file:
                    self.lock_file.close()
                    self.lock_file = None
                return False
        
        # Fallback: simple polling with lock file
        lock_path = Path(self.lock_file_path)
        
        while time.time() - start_time < self.timeout:
            try:
                # Try to create the lock file exclusively
                self.lock_file = open(lock_path, 'x')
                # Write PID to lock file
                self.lock_file.write(str(os.getpid()))
                self.lock_file.flush()
                self._locked = True
                return True
            except FileExistsError:
                # Lock file exists, check if it's stale
                try:
                    if lock_path.exists():
                        # Read lock file and check if process is alive
                        with open(lock_path, 'r') as f:
                            try:
                                pid = int(f.read().strip())
                                # Check if process exists
                                if os.name == 'nt':
                                    # Windows: use tasklist to check
                                    import subprocess
                                    try:
                                        result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                                                capture_output=True, text=True)
                                        if 'No tasks' in result.stdout:
                                            # Process dead, steal lock
                                            lock_path.unlink()
                                            continue
                                    except Exception:
                                        pass
                                else:
                                    # Unix: use os.kill with signal 0
                                    os.kill(pid, 0)
                            except (ProcessLookupError, PermissionError):
                                # Process doesn't exist, steal lock
                                lock_path.unlink()
                                continue
                except Exception:
                    pass
                
                # Wait before retrying
                time.sleep(self.poll_interval)
            except Exception:
                time.sleep(self.poll_interval)
        
        return False
    
    def release(self):
        """Release file lock."""
        if self.lock_file:
            try:
                if HAS_PORTALOCKER:
                    portalocker.unlock(self.lock_file)
                self.lock_file.close()
            except (IOError, OSError):
                pass
            self.lock_file = None
        
        # Remove lock file
        try:
            lock_path = Path(self.lock_file_path)
            if lock_path.exists():
                lock_path.unlink()
        except Exception:
            pass
        
        self._locked = False
    
    def __enter__(self):
        if not self.acquire():
            raise BlockingIOError(f"Could not acquire lock on {self.lock_file_path} within {self.timeout}s")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


@dataclass
class IndexedRecord:
    """Represents a record stored in the index with metadata."""
    id: str
    type: str
    data: Dict[str, Any]
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndexedRecord':
        """Create instance from dictionary."""
        return cls(
            id=data['id'],
            type=data['type'],
            data=data['data'],
            version=data.get('version', 1),
            created_at=data.get('created_at', datetime.utcnow().isoformat()),
            updated_at=data.get('updated_at', datetime.utcnow().isoformat())
        )


class IndexType(Enum):
    """Supported index types."""
    LOCATIONS = "locations"
    OBJECTS = "objects"
    NPCS = "npcs"
    QUESTS = "quests"
    CONNECTIONS = "connections"
    SKILLS = "skills"
    PERSONAS = "personas"


class IndexManager:
    """Manages in-memory indexes for efficient lookups with file persistence.
    
    The IndexManager maintains separate index dictionaries for each entity type,
    with O(1) lookup time for single-key queries. Indexes are rebuilt from
    the file system on startup and updated atomically on changes.
    
    Thread safety is provided via a lock that ensures only one write operation
    at a time, while multiple readers can access the index concurrently.
    
    Performance characteristics:
    - Single-key lookup: O(1) average case
    - Index rebuild: O(n) where n = total records across all indexes
    - Write operations: Atomic with file locking
    - Concurrency: Multiple readers, single writer
    """
    
    def __init__(self, data_root: str = "data"):
        """Initialize the index manager with the given data root directory.
        
        Args:
            data_root: Root directory for persisted data files.
        """
        self.data_root = Path(data_root)
        self.indexes: Dict[str, Dict[str, IndexedRecord]] = {}
        self._lock = threading.RLock()
        
        # Initialize empty indexes for all supported types
        for index_type in IndexType:
            self.indexes[index_type.value] = {}
        
        # Directory mapping for persistence
        self._directory_map = {
            IndexType.LOCATIONS: self.data_root / "world" / "locations",
            IndexType.OBJECTS: self.data_root / "world" / "objects",
            IndexType.NPCS: self.data_root / "world" / "npcs",
            IndexType.QUESTS: self.data_root / "world" / "quests",
            IndexType.CONNECTIONS: self.data_root / "world" / "connections",
            IndexType.SKILLS: self.data_root / "player",
            IndexType.PERSONAS: self.data_root / "personas",
        }
        
        # Track which indexes need persistence
        self._dirty_indexes: Set[str] = set()
    
    def rebuild(self) -> Dict[str, int]:
        """Rebuild all indexes from the file system.
        
        Scans the data directory structure and loads all persisted records
        into their respective indexes. This should be called on startup
        to restore state from disk.
        
        Returns:
            Dict mapping index type to number of records loaded.
        """
        records_loaded = {}
        
        for index_type in IndexType:
            index_name = index_type.value
            directory = self._directory_map[index_type]
            count = 0
            
            if directory.exists():
                for file_path in directory.glob("*.json"):
                    try:
                        record = self._load_record_from_file(file_path)
                        if record:
                            self.indexes[index_name][record.id] = record
                            count += 1
                    except Exception as e:
                        # Log error but continue loading other files
                        print(f"Warning: Failed to load {file_path}: {e}")
            
            records_loaded[index_name] = count
        
        return records_loaded
    
    def get(self, index_type: IndexType, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a record from the index by ID.
        
        Args:
            index_type: Type of index to search.
            record_id: ID of the record to retrieve.
            
        Returns:
            Record data if found, None otherwise.
        """
        with self._lock:
            index = self.indexes.get(index_type.value)
            if index is None:
                return None
            
            record = index.get(record_id)
            if record:
                return record.data
            
            return None
    
    def get_record(self, index_type: IndexType, record_id: str) -> Optional[IndexedRecord]:
        """Get the full IndexedRecord from the index by ID.
        
        Args:
            index_type: Type of index to search.
            record_id: ID of the record to retrieve.
            
        Returns:
            Full IndexedRecord if found, None otherwise.
        """
        with self._lock:
            index = self.indexes.get(index_type.value)
            if index is None:
                return None
            
            return index.get(record_id)
    
    def list_ids(self, index_type: IndexType) -> List[str]:
        """Get all IDs in an index.
        
        Args:
            index_type: Type of index to list.
            
        Returns:
            List of all record IDs in the index.
        """
        with self._lock:
            index = self.indexes.get(index_type.value)
            if index is None:
                return []
            
            return list(index.keys())
    
    def list_all(self, index_type: IndexType) -> List[Dict[str, Any]]:
        """Get all records from an index.
        
        Args:
            index_type: Type of index to list.
            
        Returns:
            List of all record data in the index.
        """
        with self._lock:
            index = self.indexes.get(index_type.value)
            if index is None:
                return []
            
            return [record.data for record in index.values()]
    
    def upsert(self, index_type: IndexType, record_id: str, data: Dict[str, Any]) -> bool:
        """Insert or update a record in the index.
        
        This is an atomic operation that updates both the in-memory index
        and persists the record to disk using file locking.
        
        Args:
            index_type: Type of index to modify.
            record_id: ID of the record to insert/update.
            data: Record data to store.
            
        Returns:
            True if the operation succeeded, False otherwise.
        """
        with self._lock:
            index = self.indexes.get(index_type.value)
            if index is None:
                return False
            
            existing_record = index.get(record_id)
            version = 1
            created_at = datetime.utcnow().isoformat()
            
            if existing_record:
                version = existing_record.version + 1
                created_at = existing_record.created_at
            
            updated_at = datetime.utcnow().isoformat()
            record = IndexedRecord(
                id=record_id,
                type=index_type.value,
                data=data,
                version=version,
                created_at=created_at,
                updated_at=updated_at
            )
            
            index[record_id] = record
            self._dirty_indexes.add(index_type.value)
            
            # Persist to file
            return self._persist_record(index_type, record_id, record)
    
    def delete(self, index_type: IndexType, record_id: str) -> bool:
        """Delete a record from the index.
        
        Args:
            index_type: Type of index to modify.
            record_id: ID of the record to delete.
            
        Returns:
            True if the record was deleted, False if not found.
        """
        with self._lock:
            index = self.indexes.get(index_type.value)
            if index is None:
                return False
            
            if record_id not in index:
                return False
            
            del index[record_id]
            self._dirty_indexes.add(index_type.value)
            
            # Delete from file system
            return self._delete_record_file(index_type, record_id)
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all indexes.
        
        Returns:
            Dict containing record counts and metadata for each index.
        """
        with self._lock:
            stats = {}
            for index_type in IndexType:
                index = self.indexes.get(index_type.value, {})
                stats[index_type.value] = {
                    "record_count": len(index),
                    "dirty": index_type.value in self._dirty_indexes
                }
            return stats
    
    def flush(self) -> Dict[str, int]:
        """Flush all dirty indexes to disk.
        
        Returns:
            Dict mapping index type to number of records persisted.
        """
        records_flushed = {}
        
        with self._lock:
            for index_name in list(self._dirty_indexes):
                index = self.indexes.get(index_name, {})
                count = 0
                
                for record_id, record in index.items():
                    # Re-persist all records in this index
                    index_type = IndexType(index_name)
                    if self._persist_record(index_type, record_id, record):
                        count += 1
                
                records_flushed[index_name] = count
                self._dirty_indexes.discard(index_name)
        
        return records_flushed
    
    def _load_record_from_file(self, file_path: Path) -> Optional[IndexedRecord]:
        """Load a record from a JSON file.
        
        Args:
            file_path: Path to the JSON file.
            
        Returns:
            IndexedRecord if successful, None otherwise.
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return IndexedRecord.from_dict(data)
        except (json.JSONDecodeError, KeyError, IOError) as e:
            print(f"Error loading {file_path}: {e}")
            return None
    
    def _persist_record(self, index_type: IndexType, record_id: str, record: IndexedRecord) -> bool:
        """Persist a record to disk using atomic write pattern.
        
        Uses file locking to ensure only one writer at a time,
        writes to a temp file, then renames for atomicity.
        
        Args:
            index_type: Type of index.
            record_id: ID of the record.
            record: Record to persist.
            
        Returns:
            True if successful, False otherwise.
        """
        directory = self._directory_map.get(index_type)
        if not directory:
            return False
        
        try:
            # Ensure directory exists
            directory.mkdir(parents=True, exist_ok=True)
            
            file_path = directory / f"{record_id}.json"
            temp_path = directory / f"{record_id}.json.tmp"
            lock_path = directory / f"{record_id}.lock"
            
            # Use file-based locking
            with FileLock(str(lock_path)):
                # Write to temp file
                with open(temp_path, 'w') as f:
                    json.dump(record.to_dict(), f, indent=2)
                
                # Atomic rename
                os.replace(temp_path, file_path)
            
            return True
        except (IOError, OSError) as e:
            print(f"Error persisting {record_id}: {e}")
            return False
    
    def _delete_record_file(self, index_type: IndexType, record_id: str) -> bool:
        """Delete a record file from disk.
        
        Args:
            index_type: Type of index.
            record_id: ID of the record.
            
        Returns:
            True if successful, False otherwise.
        """
        directory = self._directory_map.get(index_type)
        if not directory:
            return False
        
        try:
            file_path = directory / f"{record_id}.json"
            lock_path = directory / f"{record_id}.lock"
            
            # Use file-based locking
            with FileLock(str(lock_path)):
                if file_path.exists():
                    file_path.unlink()
            
            return True
        except (IOError, OSError) as e:
            print(f"Error deleting {record_id}: {e}")
            return False
    
    def get_index_names(self) -> List[str]:
        """Get names of all managed indexes.
        
        Returns:
            List of index type names.
        """
        return [index_type.value for index_type in IndexType]
    
    def clear(self, index_type: Optional[IndexType] = None) -> None:
        """Clear indexes, optionally for a specific type only.
        
        Args:
            index_type: Specific index to clear, or None for all.
        """
        with self._lock:
            if index_type:
                self.indexes[index_type.value].clear()
                self._dirty_indexes.add(index_type.value)
            else:
                for index in self.indexes.values():
                    index.clear()
                self._dirty_indexes.update(self.indexes.keys())


# Singleton instance for global access
_index_manager: Optional[IndexManager] = None


def get_index_manager(data_root: str = "data") -> IndexManager:
    """Get or create the global index manager instance.
    
    Args:
        data_root: Root directory for persisted data.
        
    Returns:
        Global IndexManager instance.
    """
    global _index_manager
    
    if _index_manager is None:
        _index_manager = IndexManager(data_root)
    
    return _index_manager


def reset_index_manager() -> None:
    """Reset the global index manager instance.
    
    Useful for testing or reinitialization.
    """
    global _index_manager
    _index_manager = None
