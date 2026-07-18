#!/usr/bin/env python3
"""
Systematic MUD Agent with Goal Decomposition and Map Saving

This agent follows a structured approach to MUD exploration:
1. Goal decomposition before execution
2. Systematic exploration with map saving
3. Continuous state documentation
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess

class SystematicMUDAgent:
    """Agent that systematically explores MUD with goal decomposition."""
    
    def __init__(self, skill_dir: str = None):
        """Initialize agent with skill directory."""
        if skill_dir:
            self.skill_dir = Path(skill_dir)
        else:
            # Default: parent directory of this script
            self.skill_dir = Path(__file__).parent.parent
        
        self.data_dir = self.skill_dir / "data"
        self.script_path = self.skill_dir / "scripts" / "mud_client.py"
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize state files
        self.state_files = {
            "player": self.data_dir / "player_state.json",
            "world": self.data_dir / "world_map.json",
            "navigation": self.data_dir / "navigation_notes.md",
            "discoveries": self.data_dir / "discoveries.json"
        }
        
        # Initialize empty state if files don't exist
        self.initialize_state_files()
    
    def initialize_state_files(self):
        """Initialize state files with empty structure if they don't exist."""
        # Player state
        if not self.state_files["player"].exists():
            self.save_player_state({
                "character": "dummy",
                "last_location": "unknown",
                "last_updated": datetime.now().isoformat(),
                "stats": {},
                "inventory": [],
                "known_commands": []
            })
        
        # World map
        if not self.state_files["world"].exists():
            self.save_world_map({
                "rooms": {},
                "connections": {},
                "last_explored": datetime.now().isoformat()
            })
        
        # Discoveries
        if not self.state_files["discoveries"].exists():
            self.save_discoveries({
                "npcs": {},
                "items": {},
                "shops": {},
                "locations": {},
                "last_updated": datetime.now().isoformat()
            })
    
    def run_command(self, command: str, args: List[str] = None) -> Dict[str, Any]:
        """Run a MUD client command and return result."""
        if args is None:
            args = []
        
        cmd = ["python", str(self.script_path), command] + args
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.skill_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Command timed out after 30 seconds",
                "returncode": -1
            }
    
    def save_player_state(self, state: Dict[str, Any]):
        """Save player state to file."""
        with open(self.state_files["player"], 'w') as f:
            json.dump(state, f, indent=2)
    
    def save_world_map(self, world_map: Dict[str, Any]):
        """Save world map to file."""
        with open(self.state_files["world"], 'w') as f:
            json.dump(world_map, f, indent=2)
    
    def save_discoveries(self, discoveries: Dict[str, Any]):
        """Save discoveries to file."""
        with open(self.state_files["discoveries"], 'w') as f:
            json.dump(discoveries, f, indent=2)
    
    def update_navigation_notes(self, notes: str):
        """Update navigation notes."""
        with open(self.state_files["navigation"], 'a') as f:
            f.write(f"\n--- {datetime.now().isoformat()} ---\n")
            f.write(notes + "\n")
    
    def goal_decomposition(self, goal: str) -> List[Dict[str, Any]]:
        """
        Decompose a goal into actionable steps.
        
        Returns list of steps with:
        - description: What to do
        - command: MUD command to execute
        - expected_outcome: What to look for
        - save_map: Whether to save map after this step
        """
        goal_lower = goal.lower()
        
        if "bakery" in goal_lower or "menu" in goal_lower:
            return self._decompose_bakery_goal(goal)
        elif "explore" in goal_lower or "map" in goal_lower:
            return self._decompose_exploration_goal(goal)
        elif "commands" in goal_lower or "help" in goal_lower:
            return self._decompose_discovery_goal(goal)
        else:
            # Generic goal decomposition
            return [
                {
                    "description": "Check current status and location",
                    "command": "status",
                    "args": ["--output", "data/current_status.json"],
                    "expected_outcome": "Get character stats and location",
                    "save_map": False
                },
                {
                    "description": "Look around current location",
                    "command": "cmd",
                    "args": ["look"],
                    "expected_outcome": "See room description and exits",
                    "save_map": True
                },
                {
                    "description": "Explore immediate area",
                    "command": "run",
                    "args": ["--commands", "n", "look", "s", "e", "look", "w", "look"],
                    "expected_outcome": "Discover surrounding rooms",
                    "save_map": True
                }
            ]
    
    def _decompose_bakery_goal(self, goal: str) -> List[Dict[str, Any]]:
        """Decompose bakery-related goals."""
        steps = [
            {
                "description": "Check character status and location",
                "command": "cmd",
                "args": ["look"],
                "expected_outcome": "Determine starting point",
                "save_map": False
            },
            {
                "description": "Navigate to Market Square if not already there",
                "command": "run",
                "args": ["--commands", "d", "s", "s"],
                "expected_outcome": "Reach Market Square",
                "save_map": True
            },
            {
                "description": "Go to Main Street (west of Market Square)",
                "command": "cmd",
                "args": ["w"],
                "expected_outcome": "Reach Main Street where bakery is mentioned",
                "save_map": True
            },
            {
                "description": "Check for bakery direction",
                "command": "cmd",
                "args": ["look"],
                "expected_outcome": "See 'bakery is to the north' in description",
                "save_map": False
            },
            {
                "description": "Go north to bakery",
                "command": "cmd",
                "args": ["n"],
                "expected_outcome": "Enter The Bakery",
                "save_map": True
            },
            {
                "description": "Look at bakery sign",
                "command": "cmd",
                "args": ["look sign"],
                "expected_outcome": "See bakery instructions",
                "save_map": False
            },
            {
                "description": "Get bakery menu",
                "command": "cmd",
                "args": ["list"],
                "expected_outcome": "See prices and available items",
                "save_map": False
            },
            {
                "description": "Save discoveries about bakery",
                "command": "status",
                "args": ["--output", "data/bakery_discovery.json"],
                "expected_outcome": "Document bakery findings",
                "save_map": False
            }
        ]
        return steps
    
    def _decompose_exploration_goal(self, goal: str) -> List[Dict[str, Any]]:
        """Decompose exploration goals."""
        return [
            {
                "description": "Get current location",
                "command": "cmd",
                "args": ["look"],
                "expected_outcome": "Room description with exits",
                "save_map": True
            },
            {
                "description": "Systematically explore all exits",
                "command": "run",
                "args": ["--commands", "n", "look", "s", "look", "e", "look", "w", "look", "u", "look", "d", "look"],
                "expected_outcome": "Discover all connected rooms",
                "save_map": True
            },
            {
                "description": "Create area map",
                "command": "map",
                "args": ["--output", "data/area_map.json"],
                "expected_outcome": "Structured map data",
                "save_map": True
            },
            {
                "description": "Update navigation notes",
                "command": "cmd",
                "args": ["where"],
                "expected_outcome": "See player locations in area",
                "save_map": False
            }
        ]
    
    def _decompose_discovery_goal(self, goal: str) -> List[Dict[str, Any]]:
        """Decompose command discovery goals."""
        return [
            {
                "description": "Get all available commands",
                "command": "cmd",
                "args": ["commands"],
                "expected_outcome": "List of all MUD commands",
                "save_map": False
            },
            {
                "description": "Get help overview",
                "command": "cmd",
                "args": ["help"],
                "expected_outcome": "Command categories and basic help",
                "save_map": False
            },
            {
                "description": "Discover social commands",
                "command": "cmd",
                "args": ["socials"],
                "expected_outcome": "List of social interactions",
                "save_map": False
            },
            {
                "description": "Save command discoveries",
                "command": "status",
                "args": ["--output", "data/commands_discovery.json"],
                "expected_outcome": "Document available commands",
                "save_map": False
            }
        ]
    
    def execute_goal(self, goal: str):
        """Execute a goal with systematic decomposition."""
        print(f"\n{'='*60}")
        print(f"GOAL: {goal}")
        print(f"{'='*60}")
        
        # Step 1: Decompose goal
        print("\n1. DECOMPOSING GOAL...")
        steps = self.goal_decomposition(goal)
        
        print(f"   Found {len(steps)} steps:")
        for i, step in enumerate(steps, 1):
            print(f"   {i}. {step['description']}")
        
        # Step 2: Execute each step
        print("\n2. EXECUTING STEPS...")
        results = []
        
        for i, step in enumerate(steps, 1):
            print(f"\n   Step {i}: {step['description']}")
            print(f"   Command: {step['command']} {' '.join(step.get('args', []))}")
            print(f"   Expected: {step['expected_outcome']}")
            
            # Execute command
            result = self.run_command(step["command"], step.get("args", []))
            results.append({
                "step": i,
                "description": step["description"],
                "success": result["success"],
                "output_preview": result["output"][:200] + "..." if len(result["output"]) > 200 else result["output"]
            })
            
            if result["success"]:
                print(f"   ✓ Success")
                
                # Save map if requested
                if step.get("save_map", False):
                    self._save_current_map()
                    
                # Parse and save useful information
                self._parse_and_save_discoveries(result["output"], step["description"])
            else:
                print(f"   ✗ Failed: {result.get('error', 'Unknown error')}")
            
            # Brief pause between commands
            time.sleep(1)
        
        # Step 3: Summarize results
        print(f"\n{'='*60}")
        print("GOAL EXECUTION SUMMARY")
        print(f"{'='*60}")
        
        successful = sum(1 for r in results if r["success"])
        print(f"Steps completed: {successful}/{len(steps)}")
        
        # Update navigation notes
        self.update_navigation_notes(
            f"Goal: {goal}\n"
            f"Completed: {datetime.now().isoformat()}\n"
            f"Success rate: {successful}/{len(steps)} steps\n"
        )
        
        return results
    
    def _save_current_map(self):
        """Save current map state."""
        # Run map command
        result = self.run_command("map", ["--output", "data/current_map.json"])
        
        if result["success"]:
            print("   Map saved to data/current_map.json")
            
            # Also update world map file
            try:
                with open(self.data_dir / "current_map.json", 'r') as f:
                    current_map = json.load(f)
                
                with open(self.state_files["world"], 'r') as f:
                    world_map = json.load(f)
                
                # Merge current map into world map
                # (This is a simple merge - could be enhanced)
                world_map["last_updated"] = datetime.now().isoformat()
                
                with open(self.state_files["world"], 'w') as f:
                    json.dump(world_map, f, indent=2)
                    
            except Exception as e:
                print(f"   Warning: Could not update world map: {e}")
    
    def _parse_and_save_discoveries(self, output: str, context: str):
        """Parse command output for discoveries and save them."""
        discoveries = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "output_snippet": output[:500]  # Save first 500 chars
        }
        
        # Simple parsing for common patterns
        if "bakery" in output.lower():
            discoveries["type"] = "bakery"
        elif "shop" in output.lower() or "store" in output.lower():
            discoveries["type"] = "shop"
        elif "inn" in output.lower() or "tavern" in output.lower():
            discoveries["type"] = "inn"
        elif "guild" in output.lower():
            discoveries["type"] = "guild"
        elif "temple" in output.lower():
            discoveries["type"] = "temple"
        
        # Save to discoveries file
        try:
            with open(self.state_files["discoveries"], 'r') as f:
                all_discoveries = json.load(f)
        except:
            all_discoveries = {"discoveries": []}
        
        if "discoveries" not in all_discoveries:
            all_discoveries["discoveries"] = []
        
        all_discoveries["discoveries"].append(discoveries)
        all_discoveries["last_updated"] = datetime.now().isoformat()
        
        with open(self.state_files["discoveries"], 'w') as f:
            json.dump(all_discoveries, f, indent=2)

def main():
    """Main execution function."""
    # Get skill directory
    skill_dir = Path(__file__).parent.parent
    
    # Create agent
    agent = SystematicMUDAgent(str(skill_dir))
    
    # Example goals to execute
    goals = [
        "Discover all available MUD commands",
        "Find the bakery and get menu",
        "Explore current area and save map"
    ]
    
    print("Systematic MUD Agent")
    print("=" * 60)
    print("\nAvailable goals:")
    for i, goal in enumerate(goals, 1):
        print(f"  {i}. {goal}")
    
    print("\nSelect goal to execute (1-3) or enter custom goal:")
    choice = input("> ").strip()
    
    if choice.isdigit() and 1 <= int(choice) <= len(goals):
        selected_goal = goals[int(choice) - 1]
    else:
        selected_goal = choice if choice else goals[0]
    
    # Execute goal
    agent.execute_goal(selected_goal)
    
    print("\n" + "=" * 60)
    print("AGENT COMPLETE")
    print("=" * 60)
    print("\nData saved to:")
    for name, path in agent.state_files.items():
        if path.exists():
            print(f"  • {name}: {path}")

if __name__ == "__main__":
    main()