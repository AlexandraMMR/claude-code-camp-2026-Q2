#!/usr/bin/env python3
"""
Final demonstration of systematic MUD exploration with:
1. Goal decomposition before execution
2. Map saving during exploration  
3. Command discovery and documentation
4. Structured data collection
"""

import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class MUDExplorationDemo:
    """Demonstrate systematic MUD exploration."""
    
    def __init__(self):
        self.skill_dir = Path(__file__).parent
        self.data_dir = self.skill_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
    def run_mud_command(self, command: str, args: list = None):
        """Run a MUD command and return output."""
        cmd = ["python", "scripts/mud_client.py", command]
        if args:
            cmd.extend(args)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.skill_dir,
                capture_output=True,
                text=True,
                timeout=15
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            return "[TIMEOUT]"
    
    def demonstrate_goal_decomposition(self):
        """Show how to decompose goals before execution."""
        print("\n" + "="*70)
        print("GOAL DECOMPOSITION DEMONSTRATION")
        print("="*70)
        
        goal = "Discover all MUD commands and document them"
        
        print(f"\nGOAL: {goal}")
        print("\nDECOMPOSED STEPS:")
        
        steps = [
            ("1. Initial Assessment", "status --output data/initial_status.json", "Get character state"),
            ("2. Command Discovery", "cmd commands", "Get list of all available commands"),
            ("3. Help Overview", "cmd help", "See command categories"),
            ("4. Social Commands", "cmd socials", "Discover social interactions"),
            ("5. Save Findings", "# Manual: Save to data/commands_reference.md", "Document for future use"),
            ("6. Test Safe Commands", "cmd look; cmd score; cmd where", "Verify command functionality")
        ]
        
        for step_name, step_command, step_purpose in steps:
            print(f"  {step_name}")
            print(f"    Command: {step_command}")
            print(f"    Purpose: {step_purpose}")
            print()
    
    def demonstrate_map_saving(self):
        """Show systematic map saving approach."""
        print("\n" + "="*70)
        print("SYSTEMATIC MAP SAVING DEMONSTRATION")
        print("="*70)
        
        print("\nEXPLORATION PROTOCOL:")
        
        protocol = [
            "1. START: Check current location with 'look'",
            "2. RECORD: Save room description, exits, features",
            "3. EXPLORE: Systematically check each exit direction",
            "4. DOCUMENT: For each new room, record:",
            "   - Room name and description",
            "   - Available exits", 
            "   - NPCs, items, or features",
            "   - Connection to previous rooms",
            "5. UPDATE: After each exploration session:",
            "   - Update world_map.json with new rooms",
            "   - Update navigation_notes.md with paths",
            "   - Update discoveries.json with findings",
            "6. PLAN: Use map to plan future exploration routes"
        ]
        
        for step in protocol:
            print(f"  {step}")
        
        # Show example of structured data
        print("\nEXAMPLE STRUCTURED DATA (from our exploration):")
        
        example_map = {
            "navigation_path": {
                "bakery": ["Temple Altar", "Temple of Midgaard", "Temple Square", "Market Square", "Main Street", "Bakery"],
                "steps": ["d", "s", "s", "w", "n"]
            },
            "key_locations": {
                "The Bakery": {
                    "type": "shop",
                    "menu": {"danish": 7, "bread": 14, "waybread": 72},
                    "exits": ["s"],
                    "notes": "Baker present, sign with instructions"
                },
                "Market Square": {
                    "type": "central",
                    "exits": ["n", "e", "s", "w"],
                    "connections": {
                        "n": "Temple Square",
                        "e": "Main Street (general store)",
                        "w": "Main Street (bakery)",
                        "s": "Common Square"
                    }
                }
            }
        }
        
        print("\n  Navigation to bakery:", " → ".join(example_map["navigation_path"]["bakery"]))
        print("  Bakery menu:", example_map["key_locations"]["The Bakery"]["menu"])
    
    def demonstrate_command_discovery(self):
        """Show command discovery process."""
        print("\n" + "="*70)
        print("COMMAND DISCOVERY PROCESS")
        print("="*70)
        
        print("\nTo discover and learn MUD commands:")
        
        discovery_steps = [
            "1. BASIC DISCOVERY:",
            "   - 'commands': List all available verbs",
            "   - 'help': General help with categories",
            "   - 'help <command>': Details on specific command",
            "",
            "2. CATEGORY EXPLORATION:",
            "   - 'socials': Social interaction commands",
            "   - Movement: north, south, east, west, look, exits",
            "   - Objects: get, drop, inventory, examine, wear",
            "   - Information: score, who, where, time, weather",
            "   - Combat: kill, flee, wield, cast",
            "   - Utility: save, quit, bug, idea, typo",
            "",
            "3. PRACTICAL TESTING:",
            "   - Test safe commands first (look, score, who)",
            "   - Test in safe areas before dangerous ones",
            "   - Use 'auto' commands for automation (autoexits, automap)",
            "",
            "4. DOCUMENTATION:",
            "   - Create commands_reference.md with categories",
            "   - Note command syntax and examples",
            "   - Document useful command combinations"
        ]
        
        for step in discovery_steps:
            print(f"  {step}")
    
    def create_agent_workflow(self):
        """Create complete agent workflow document."""
        print("\n" + "="*70)
        print("COMPLETE AGENT WORKFLOW")
        print("="*70)
        
        workflow = {
            "pre_execution": [
                "1. Goal Definition: Clearly state what you want to achieve",
                "2. Goal Decomposition: Break into actionable steps",
                "3. Resource Check: Verify character status and location",
                "4. Command Discovery: Check available commands for task"
            ],
            "execution": [
                "1. Systematic Exploration: One direction at a time",
                "2. Continuous Documentation: Save after each discovery",
                "3. State Preservation: Maintain connection and position",
                "4. Error Handling: Plan for failures and dead ends"
            ],
            "post_execution": [
                "1. Data Consolidation: Combine all discoveries",
                "2. Map Update: Add new rooms and connections",
                "3. Knowledge Base: Update command references",
                "4. Progress Log: Document what was learned"
            ]
        }
        
        for phase, steps in workflow.items():
            print(f"\n{phase.upper().replace('_', ' ')}:")
            for step in steps:
                print(f"  {step}")
    
    def run(self):
        """Run the complete demonstration."""
        print("SYSTEMATIC MUD EXPLORATION SYSTEM")
        print("="*70)
        print("\nThis demonstrates how an agent should approach MUD exploration")
        print("with goal decomposition, map saving, and command discovery.")
        
        self.demonstrate_goal_decomposition()
        self.demonstrate_map_saving()
        self.demonstrate_command_discovery()
        self.create_agent_workflow()
        
        print("\n" + "="*70)
        print("IMPLEMENTATION STATUS")
        print("="*70)
        
        # Check what we've implemented
        implementations = [
            ("✓", "MUD Client Skill", "scripts/mud_client.py with persistent connections"),
            ("✓", "Goal Decomposition", "Structured approach to breaking down tasks"),
            ("✓", "Map Saving System", "JSON-based room and discovery tracking"),
            ("✓", "Command Discovery", "Process for finding and learning commands"),
            ("✓", "Structured Data", "explored_map.json with room connections"),
            ("→", "Automated Agent", "Systematic_agent.py (needs path fixes)"),
            ("→", "Real-time Exploration", "Live map updating during exploration"),
            ("→", "Command Testing Suite", "Automated command validation")
        ]
        
        for status, feature, description in implementations:
            print(f"{status} {feature}: {description}")
        
        print("\n" + "="*70)
        print("NEXT STEPS FOR AGENT IMPROVEMENT")
        print("="*70)
        
        next_steps = [
            "1. Fix path issues in systematic_agent.py",
            "2. Add real-time map updating to mud_client.py",
            "3. Create command testing and validation suite",
            "4. Add automated goal achievement tracking",
            "5. Implement exploration strategy patterns",
            "6. Create recovery protocols for getting lost"
        ]
        
        for i, step in enumerate(next_steps, 1):
            print(f"{i}. {step}")

def main():
    """Main execution."""
    demo = MUDExplorationDemo()
    demo.run()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\nThe agent skill now includes:")
    print("• Complete MUD command reference with 100+ commands")
    print("• Goal decomposition strategy for any task")
    print("• Systematic map saving with JSON structure")
    print("• Command discovery and learning process")
    print("• Working navigation to key locations (bakery found!)")
    print("• Persistent connection management")
    print("\nTo use: python scripts/mud_client.py <command>")
    print("Example: python scripts/mud_client.py cmd look")

if __name__ == "__main__":
    main()