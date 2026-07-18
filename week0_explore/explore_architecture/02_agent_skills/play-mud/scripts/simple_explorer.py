#!/usr/bin/env python3
"""
Simple explorer demonstrating goal decomposition and map saving.
"""

import json
import time
from datetime import datetime
from pathlib import Path

def save_discovery(location: str, description: str, exits: list, discoveries: dict = None):
    """Save a room discovery to the map."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    map_file = data_dir / "explored_map.json"
    
    # Load existing map or create new
    if map_file.exists():
        with open(map_file, 'r') as f:
            map_data = json.load(f)
    else:
        map_data = {
            "rooms": {},
            "connections": {},
            "exploration_log": []
        }
    
    # Add room
    map_data["rooms"][location] = {
        "description": description,
        "exits": exits,
        "discovered": datetime.now().isoformat(),
        "discoveries": discoveries or {}
    }
    
    # Add to log
    map_data["exploration_log"].append({
        "timestamp": datetime.now().isoformat(),
        "action": "discovered",
        "location": location
    })
    
    # Save
    with open(map_file, 'w') as f:
        json.dump(map_data, f, indent=2)
    
    print(f"✓ Saved discovery: {location}")
    return map_data

def goal_decomposition(goal: str):
    """Demonstrate goal decomposition."""
    print(f"\nGoal: {goal}")
    print("Decomposed steps:")
    
    if "bakery" in goal.lower():
        steps = [
            "1. Check current location (look)",
            "2. Navigate to Market Square if needed",
            "3. Go west to Main Street",
            "4. Look for bakery direction",
            "5. Go north to bakery",
            "6. Read sign and get menu",
            "7. Save bakery discovery"
        ]
    elif "explore" in goal.lower():
        steps = [
            "1. Look at current room",
            "2. Check all exits (exits command)",
            "3. Explore north, save discovery",
            "4. Explore south, save discovery", 
            "5. Explore east, save discovery",
            "6. Explore west, save discovery",
            "7. Update map with all connections"
        ]
    elif "commands" in goal.lower():
        steps = [
            "1. Get all commands (commands)",
            "2. Get help overview (help)",
            "3. Discover social commands (socials)",
            "4. Save command reference"
        ]
    else:
        steps = [
            "1. Assess current situation",
            "2. Gather information",
            "3. Plan approach",
            "4. Execute systematically",
            "5. Document results"
        ]
    
    for step in steps:
        print(f"  {step}")
    
    return steps

def demonstrate_exploration():
    """Demonstrate the exploration process."""
    print("=" * 60)
    print("SYSTEMATIC EXPLORATION DEMONSTRATION")
    print("=" * 60)
    
    # Example: Discovering the bakery area
    print("\nExample: We discovered these locations:")
    
    # Simulate discoveries from our actual exploration
    discoveries = [
        {
            "location": "By The Temple Altar",
            "description": "Northern end of Temple of Midgaard with altar and Odin statue",
            "exits": ["n", "s"],
            "discoveries": {"type": "temple", "landmark": "Odin statue"}
        },
        {
            "location": "The Temple Of Midgaard", 
            "description": "Southern temple hall with ATM, Reading Room to west",
            "exits": ["n", "e", "s", "w", "d"],
            "discoveries": {"type": "temple", "feature": "ATM", "west": "Reading Room"}
        },
        {
            "location": "The Temple Square",
            "description": "Square with fountain, Clerics' Guild west, Grunting Boar Inn east",
            "exits": ["n", "e", "s", "w"],
            "discoveries": {"type": "square", "npc": "Peacekeeper", "feature": "fountain"}
        },
        {
            "location": "Market Square",
            "description": "Center of Midgaard with peculiar statue, roads in all directions",
            "exits": ["n", "e", "s", "w"],
            "discoveries": {"type": "market", "central": True}
        },
        {
            "location": "Main Street (west of Market Square)",
            "description": "Passing through City of Midgaard, bakery to north, armory south",
            "exits": ["n", "e", "s", "w"],
            "discoveries": {"type": "street", "north": "bakery", "south": "armory"}
        },
        {
            "location": "The Bakery",
            "description": "Small bakery with sweet scent, sign on counter, baker present",
            "exits": ["s"],
            "discoveries": {
                "type": "shop", 
                "shop_type": "bakery",
                "menu": {
                    "danish pastry": 7,
                    "bread": 14,
                    "waybread": 72
                },
                "npc": "baker",
                "sign": "Buy - buy bread/pastry, List - see prices"
            }
        }
    ]
    
    # Save each discovery
    for discovery in discoveries:
        save_discovery(
            discovery["location"],
            discovery["description"],
            discovery["exits"],
            discovery["discoveries"]
        )
        time.sleep(0.5)  # Simulate exploration time
    
    print(f"\n✓ Saved {len(discoveries)} locations to explored_map.json")
    
    # Demonstrate goal decomposition
    print("\n" + "=" * 60)
    print("GOAL DECOMPOSITION EXAMPLES")
    print("=" * 60)
    
    goals = [
        "Find the bakery and get menu",
        "Explore the temple area",
        "Discover all available commands"
    ]
    
    for goal in goals:
        goal_decomposition(goal)
        print()

def main():
    """Main function."""
    print("MUD Exploration System")
    print("=" * 60)
    
    demonstrate_exploration()
    
    print("=" * 60)
    print("EXPLORATION COMPLETE")
    print("=" * 60)
    print("\nCreated structured map with:")
    print("  • Room descriptions")
    print("  • Exit connections")
    print("  • Discoveries (NPCs, items, shops)")
    print("  • Exploration timeline")
    print("\nMap saved to: data/explored_map.json")
    
    # Show what command discovery would look like
    print("\n" + "=" * 60)
    print("COMMAND DISCOVERY STRATEGY")
    print("=" * 60)
    print("To discover commands, an agent should:")
    print("  1. Use 'commands' to see all available verbs")
    print("  2. Use 'help <command>' for details on specific commands")
    print("  3. Use 'socials' to discover social interactions")
    print("  4. Test commands in safe areas first")
    print("  5. Document useful commands for future reference")

if __name__ == "__main__":
    main()