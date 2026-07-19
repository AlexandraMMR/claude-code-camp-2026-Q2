"""
Skill Registry for managing skill metadata and dependencies.

This module provides the SkillRegistry class that handles:
- Skill registration with metadata
- Skill discovery and lookup
- Dependency graph generation
- Circular dependency detection

Validates: Requirements 11.1, 11.4 (Skill Registration and Dependency Management)
"""

import time
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

# Import models from data folder
from ..data.models import SkillMetadata, ParameterSchema


class SkillRegistry:
    """
    Registry for managing skill metadata and dependencies.
    
    Provides fast lookups (under 100ms for queries) and dependency graph
    generation with circular dependency detection.
    
    Supports at least 100 skills with efficient data structures.
    """
    
    def __init__(self) -> None:
        """Initialize the skill registry with empty storage and indexes."""
        # Main storage for skill metadata
        self._skills: Dict[str, SkillMetadata] = {}
        # Index for fast lookup by name
        self._name_index: Dict[str, str] = {}
        # Index for fast lookup by version
        self._version_index: Dict[str, List[str]] = {}
        # Dependency graph storage
        self._dependency_graph: Dict[str, List[str]] = {}
    
    def register(self, metadata: SkillMetadata) -> bool:
        """
        Register a new skill with the registry.
        
        Args:
            metadata: SkillMetadata containing skill information
            
        Returns:
            True if registration successful, False if validation failed
            
        Raises:
            ValueError: If circular dependency would be created
        """
        # Check for duplicate name
        if metadata.name in self._skills:
            return False
        
        # Build dependency graph for validation
        start_time = time.perf_counter()
        try:
            # Validate no circular dependencies would be created
            self._validate_no_circular_dependency(metadata)
            
            # Register the skill
            self._skills[metadata.name] = metadata
            self._name_index[metadata.name] = metadata.name
            self._dependency_graph[metadata.name] = metadata.dependencies
            
            # Update version index
            if metadata.version not in self._version_index:
                self._version_index[metadata.version] = []
            self._version_index[metadata.version].append(metadata.name)
            
            return True
            
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            # Performance tracking (not stored, but could be for metrics)
            if elapsed_ms > 100:
                pass  # Could log warning for slow registration
    
    def discover(self, skill_name: str) -> Optional[SkillMetadata]:
        """
        Discover a skill by name.
        
        Args:
            skill_name: Name of the skill to discover
            
        Returns:
            SkillMetadata if found, None otherwise
            
        Performance: Returns within 100ms for single skill lookup
        """
        start_time = time.perf_counter()
        try:
            return self._skills.get(skill_name)
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            # Performance check (could log for monitoring)
            if elapsed_ms > 100:
                pass  # Could log warning for slow lookup
    
    def list_skills(self, filter_by_version: Optional[str] = None) -> List[SkillMetadata]:
        """
        List all registered skills, optionally filtered by version.
        
        Args:
            filter_by_version: Optional version string to filter skills
            
        Returns:
            List of SkillMetadata objects
            
        Performance: Returns within 100ms for up to 100 skills
        """
        start_time = time.perf_counter()
        try:
            if filter_by_version:
                skill_names = self._version_index.get(filter_by_version, [])
                return [self._skills[name] for name in skill_names if name in self._skills]
            return list(self._skills.values())
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            # Performance check (could log for monitoring)
            if elapsed_ms > 100:
                pass  # Could log warning for slow listing
    
    def get_dependency_graph(self, skill_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Generate a dependency graph for skills.
        
        Args:
            skill_name: Optional specific skill to get graph for.
                       If None, returns graph for all skills.
            
        Returns:
            Dictionary mapping skill names to their dependencies
            
        Performance: Returns within 200ms for graphs up to 100 nodes
        """
        start_time = time.perf_counter()
        try:
            if skill_name:
                if skill_name not in self._skills:
                    return {}
                # Get transitive dependencies for the skill
                return self._build_subgraph(skill_name)
            else:
                # Return full dependency graph
                return dict(self._dependency_graph)
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            # Performance check (could log for monitoring)
            if elapsed_ms > 200:
                pass  # Could log warning for slow graph generation
    
    def get_dependents(self, skill_name: str) -> List[str]:
        """
        Get all skills that depend on the specified skill.
        
        Args:
            skill_name: Name of the skill to find dependents for
            
        Returns:
            List of skill names that depend on the specified skill
        """
        dependents = []
        for name, deps in self._dependency_graph.items():
            if skill_name in deps:
                dependents.append(name)
        return dependents
    
    def _validate_no_circular_dependency(self, metadata: SkillMetadata) -> None:
        """
        Validate that registering this skill won't create a circular dependency.
        
        Uses DFS-based cycle detection algorithm.
        
        Args:
            metadata: SkillMetadata being registered
            
        Raises:
            ValueError: If circular dependency would be created
        """
        # Build temporary graph including the new skill
        temp_graph = dict(self._dependency_graph)
        temp_graph[metadata.name] = metadata.dependencies
        
        # Check for cycles using DFS
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def has_cycle(node: str, path: List[str]) -> bool:
            """DFS to detect cycles in dependency graph."""
            if node in rec_stack:
                # Found a cycle - format the cycle path for error message
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                raise ValueError(
                    f"Circular dependency detected: {' -> '.join(cycle)}"
                )
            
            if node in visited:
                return False
            
            if node not in temp_graph:
                # Node doesn't exist in graph (not registered yet)
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for dep in temp_graph.get(node, []):
                if has_cycle(dep, path):
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        # Check for cycles starting from the new skill
        if has_cycle(metadata.name, []):
            raise ValueError(f"Circular dependency detected for skill '{metadata.name}'")
    
    def _build_subgraph(self, skill_name: str) -> Dict[str, List[str]]:
        """
        Build a subgraph containing the skill and all its dependencies.
        
        Args:
            skill_name: Root skill for the subgraph
            
        Returns:
            Dictionary mapping skill names to their dependencies
        """
        subgraph: Dict[str, List[str]] = {}
        visited: Set[str] = set()
        
        def traverse(skill: str) -> None:
            """Recursively traverse dependencies."""
            if skill in visited:
                return
            
            visited.add(skill)
            deps = self._dependency_graph.get(skill, [])
            subgraph[skill] = deps
            
            for dep in deps:
                traverse(dep)
        
        traverse(skill_name)
        return subgraph
    
    def get_skill_names(self) -> List[str]:
        """Get all registered skill names."""
        return list(self._skills.keys())
    
    def get_versions(self) -> List[str]:
        """Get all registered skill versions."""
        return list(self._version_index.keys())
    
    def get_skill_count(self) -> int:
        """Get the total number of registered skills."""
        return len(self._skills)
