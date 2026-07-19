"""
Skill Executor for executing registered skills with validation and timeout protection.

This module provides the SkillExecutor class that handles:
- Parameter validation against skill metadata
- Skill execution with configurable timeout protection
- Structured result packaging with success/failure status
- Detailed error diagnostics with specific error types and suggested actions

Validates: Requirements 11.2, 11.5 (Skill Execution and Error Diagnostics)
"""

import time
from concurrent.futures import Executor, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple, Type

# Import models from data folder
from ..data.models import SkillMetadata, ParameterSchema

# Import SkillRegistry
from .registry import SkillRegistry


class ValidationError(Exception):
    """Raised when parameter validation fails."""
    def __init__(self, message: str, parameter: Optional[str] = None, suggested_action: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.parameter = parameter
        self.suggested_action = suggested_action


class TimeoutError(Exception):
    """Raised when skill execution exceeds the timeout."""
    def __init__(self, message: str, skill_name: str, timeout: float):
        super().__init__(message)
        self.message = message
        self.skill_name = skill_name
        self.timeout = timeout


class ExecutionError(Exception):
    """Raised when skill execution fails."""
    def __init__(self, message: str, error_type: str, skill_name: str, suggested_action: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.skill_name = skill_name
        self.suggested_action = suggested_action


class DependencyError(Exception):
    """Raised when skill dependencies are not satisfied."""
    def __init__(self, message: str, missing_dependencies: List[str], suggested_action: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.missing_dependencies = missing_dependencies
        self.suggested_action = suggested_action


@dataclass
class SkillResult:
    """
    Structured result from skill execution.
    
    Validates: Requirements 11.2 (Result Packaging)
    """
    status: str  # "success" or "failure"
    skill_name: str
    duration_ms: float
    output: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    error_type: Optional[str] = None
    suggested_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "status": self.status,
            "skill_name": self.skill_name,
            "duration_ms": self.duration_ms,
            "output": self.output,
            "errors": self.errors,
            "error_type": self.error_type,
            "suggested_actions": self.suggested_actions
        }


class SkillExecutor:
    """
    Executor for registered skills with parameter validation and timeout protection.
    
    Provides:
    - Parameter validation ensuring all required parameters are present and type-compatible
    - Execution with timeout protection (default 30 seconds, configurable)
    - Structured result packaging including success/failure status, execution duration, and any output or error messages
    - Detailed error diagnostics with specific error types and suggested actions
    """
    
    def __init__(
        self,
        registry: SkillRegistry,
        default_timeout: float = 30.0,
        timeout_buffer: float = 5.0
    ):
        """
        Initialize the skill executor.
        
        Args:
            registry: SkillRegistry for skill discovery
            default_timeout: Default timeout in seconds (default 30)
            timeout_buffer: Buffer time in seconds to allow cleanup (default 5)
            
        Performance: O(1) initialization
        """
        self._registry = registry
        self._default_timeout = default_timeout
        self._timeout_buffer = timeout_buffer
        self._executor_pool: Optional[Executor] = None
        self._execution_count = 0
        self._success_count = 0
        self._error_counts: Dict[str, int] = {}
    
    def execute(
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
            # Discover the skill
            skill = self._registry.discover(skill_name)
            if skill is None:
                return self._create_failure_result(
                    skill_name=skill_name,
                    duration_ms=0,
                    error_type="SkillNotFoundError",
                    message=f"Skill '{skill_name}' not found in registry",
                    suggested_actions=[f"Register skill '{skill_name}' using SkillRegistry.register()"]
                )
            
            # Validate parameters
            try:
                self.validate_parameters(skill_name, parameters)
            except ValidationError as e:
                return self._create_failure_result(
                    skill_name=skill_name,
                    duration_ms=0,
                    error_type="ValidationError",
                    message=str(e),
                    suggested_actions=[e.suggested_action] if e.suggested_action else []
                )
            
            # Check dependencies
            try:
                self._validate_dependencies(skill)
            except DependencyError as e:
                return self._create_failure_result(
                    skill_name=skill_name,
                    duration_ms=0,
                    error_type="DependencyError",
                    message=str(e),
                    suggested_actions=[e.suggested_action] if e.suggested_action else []
                )
            
            # Get actual timeout
            actual_timeout = timeout if timeout is not None else self._default_timeout
            
            # Execute with timeout protection
            try:
                result = self._execute_with_timeout(skill, parameters, actual_timeout)
                return result
            except TimeoutError as e:
                return self._create_failure_result(
                    skill_name=skill_name,
                    duration_ms=0,
                    error_type="TimeoutError",
                    message=str(e),
                    suggested_actions=[
                        "Increase timeout for this skill",
                        "Optimize skill implementation",
                        "Check for network or resource issues"
                    ]
                )
            except ExecutionError as e:
                return self._create_failure_result(
                    skill_name=skill_name,
                    duration_ms=0,
                    error_type=e.error_type,
                    message=e.message,
                    suggested_actions=[e.suggested_action] if e.suggested_action else []
                )
                
        finally:
            self._execution_count += 1
    
    def validate_parameters(
        self,
        skill_name: str,
        parameters: Dict[str, Any]
    ) -> None:
        """
        Validate parameters against skill metadata.
        
        Args:
            skill_name: Name of the skill to validate parameters for
            parameters: Dictionary of parameters to validate
            
        Returns:
            None if validation passes
            
        Raises:
            ValidationError: If validation fails
            
        Performance: O(n) where n is number of parameters
        """
        skill = self._registry.discover(skill_name)
        if skill is None:
            raise ValidationError(
                f"Skill '{skill_name}' not found",
                suggested_action=f"Register skill '{skill_name}' using SkillRegistry.register()"
            )
        
        missing_params = []
        type_mismatch_params = []
        
        for param_name, param_schema in skill.parameters.items():
            if param_schema.required and param_name not in parameters:
                missing_params.append(param_name)
            elif param_name in parameters:
                param_value = parameters[param_name]
                if not self._validate_type(param_value, param_schema):
                    type_mismatch_params.append((param_name, param_schema.type, type(param_value).__name__))
        
        if missing_params:
            raise ValidationError(
                f"Missing required parameters: {', '.join(missing_params)}",
                parameter=", ".join(missing_params),
                suggested_action=f"Add missing parameters: {', '.join(missing_params)}"
            )
        
        if type_mismatch_params:
            errors = [
                f"Parameter '{name}': expected {expected}, got {actual}"
                for name, expected, actual in type_mismatch_params
            ]
            raise ValidationError(
                "Type mismatch in parameters: " + "; ".join(errors),
                parameter=type_mismatch_params[0][0],
                suggested_action=f"Fix parameter types: {', '.join([p[0] for p in type_mismatch_params])}"
            )
    
    def _execute_with_timeout(
        self,
        skill: SkillMetadata,
        parameters: Dict[str, Any],
        timeout: float
    ) -> SkillResult:
        """
        Execute a skill with timeout protection.
        
        Args:
            skill: SkillMetadata to execute
            parameters: Parameters to pass to skill
            timeout: Timeout in seconds
            
        Returns:
            SkillResult with execution results
            
        Raises:
            TimeoutError: If execution exceeds timeout
        """
        # Use ThreadPoolExecutor for timeout control
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._run_skill, skill, parameters)
            
            try:
                result = future.result(timeout=timeout)
                return result
            except TimeoutError:
                raise TimeoutError(
                    f"Skill '{skill.name}' execution exceeded timeout of {timeout} seconds",
                    skill_name=skill.name,
                    timeout=timeout
                )
            except Exception as e:
                raise ExecutionError(
                    message=str(e),
                    error_type="ExecutionError",
                    skill_name=skill.name,
                    suggested_action="Check skill implementation for errors"
                )
    
    def _run_skill(
        self,
        skill: SkillMetadata,
        parameters: Dict[str, Any]
    ) -> SkillResult:
        """
        Run a skill and return structured result.
        
        This is a placeholder that simulates skill execution.
        In a real implementation, this would dynamically import and execute skill modules.
        
        Args:
            skill: SkillMetadata to execute
            parameters: Parameters to pass to skill
            
        Returns:
            SkillResult with execution results
        """
        # Simulate skill execution
        # In real implementation, this would:
        # 1. Find skill module/class by name
        # 2. Invoke the skill with parameters
        # 3. Capture output and errors
        
        start = time.perf_counter()
        
        try:
            # Placeholder for actual skill execution
            # This would typically involve importing and calling the skill function
            
            # Simulate some processing time
            time.sleep(0.001)
            
            duration = (time.perf_counter() - start) * 1000
            
            # Simulate successful execution with example output
            output = {
                "skill_executed": skill.name,
                "parameters_used": parameters,
                "result": "success"
            }
            
            # Track success
            self._success_count += 1
            
            return SkillResult(
                status="success",
                skill_name=skill.name,
                duration_ms=duration,
                output=output
            )
            
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            
            error_type = self._classify_error(e)
            
            return SkillResult(
                status="failure",
                skill_name=skill.name,
                duration_ms=duration,
                errors=[str(e)],
                error_type=error_type,
                suggested_actions=["Check skill implementation", "Verify parameters", "Review error logs"]
            )
    
    def _validate_dependencies(self, skill: SkillMetadata) -> None:
        """
        Validate that all skill dependencies are available.
        
        Args:
            skill: SkillMetadata to validate dependencies for
            
        Raises:
            DependencyError: If dependencies are not satisfied
        """
        missing = []
        for dep in skill.dependencies:
            if self._registry.discover(dep) is None:
                missing.append(dep)
        
        if missing:
            raise DependencyError(
                f"Skill '{skill.name}' has unsatisfied dependencies: {', '.join(missing)}",
                missing_dependencies=missing,
                suggested_action=f"Register missing dependencies: {', '.join(missing)}"
            )
    
    def _validate_type(self, value: Any, schema: ParameterSchema) -> bool:
        """
        Validate a value against a parameter schema type.
        
        Args:
            value: Value to validate
            schema: ParameterSchema with expected type
            
        Returns:
            True if value matches schema type
        """
        type_map: Dict[str, Type] = {
            "string": str,
            "str": str,
            "integer": int,
            "int": int,
            "float": float,
            "number": (int, float),
            "boolean": bool,
            "bool": bool,
            "object": dict,
            "array": list,
            "list": list
        }
        
        expected_type = type_map.get(schema.type.lower())
        if expected_type is None:
            # Unknown type, allow any
            return True
        
        # Special case: int is not a subclass of float
        if expected_type == float and isinstance(value, int) and not isinstance(value, bool):
            return True
        
        return isinstance(value, expected_type)
    
    def _classify_error(self, error: Exception) -> str:
        """
        Classify an error into a specific error type.
        
        Args:
            error: Exception that occurred
            
        Returns:
            Error type string
        """
        error_type_map: Dict[Type, str] = {
            TypeError: "TypeError",
            ValueError: "ValueError",
            AttributeError: "AttributeError",
            KeyError: "KeyError",
            IndexError: "IndexError",
            TimeoutError: "TimeoutError",
            ConnectionError: "ConnectionError",
            FileNotFoundError: "FileNotFoundError"
        }
        
        for error_class, error_type in error_type_map.items():
            if isinstance(error, error_class):
                return error_type
        
        return "ExecutionError"
    
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
        self._update_error_metrics(error_type)
        
        return SkillResult(
            status="failure",
            skill_name=skill_name,
            duration_ms=duration_ms,
            errors=[message],
            error_type=error_type,
            suggested_actions=suggested_actions
        )
    
    def _update_error_metrics(self, error_type: str) -> None:
        """Update error counting metrics."""
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get execution metrics.
        
        Returns:
            Dictionary with execution statistics
        """
        return {
            "total_executions": self._execution_count,
            "success_count": self._success_count,
            "error_counts": self._error_counts,
            "default_timeout": self._default_timeout,
            "timeout_buffer": self._timeout_buffer
        }
    
    def reset_metrics(self) -> None:
        """Reset all execution metrics."""
        self._execution_count = 0
        self._success_count = 0
        self._error_counts = {}
