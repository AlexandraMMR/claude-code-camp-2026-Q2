#!/usr/bin/env python3
"""
Test script for bakery finding mission.
Demonstrates how an agent would use the play-mud skill.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd):
    """Run a shell command and return output."""
    print(f"\n>>> Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr and "DeprecationWarning" not in result.stderr:
        print(f"STDERR: {result.stderr}")
    return result.returncode, result.stdout

def main():
    """Test the bakery finding mission."""
    print("=" * 60)
    print("BAKERY FINDING MISSION TEST")
    print("=" * 60)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Test 1: Initial connection and look
    print("\n1. Initial assessment:")
    returncode, output = run_command('python scripts/mud_client.py cmd look')
    
    # Check if we're in a promising location for bakery
    if "temple" in output.lower() or "market" in output.lower():
        print("Good starting point - in a temple or market area")
    else:
        print("Note: May need to explore to find commercial areas")
    
    # Test 2: Explore immediate area
    print("\n2. Exploring immediate area:")
    returncode, output = run_command('python scripts/mud_client.py run --commands "n" "look" "s" "e" "look" "w" "look"')
    
    # Check for bakery clues
    bakery_keywords = ["bakery", "bread", "oven", "pastry", "bake", "flour"]
    found_clues = []
    for keyword in bakery_keywords:
        if keyword in output.lower():
            found_clues.append(keyword)
    
    if found_clues:
        print(f"Found bakery clues: {', '.join(found_clues)}")
    else:
        print("No immediate bakery clues found")
    
    # Test 3: Check character status
    print("\n3. Checking character status:")
    returncode, output = run_command('python scripts/mud_client.py status --output data/test_status.json')
    
    # Test 4: Systematic search pattern
    print("\n4. Systematic search (expanding radius):")
    search_commands = [
        'python scripts/mud_client.py run --commands "n" "n" "look" "s" "s"',
        'python scripts/mud_client.py run --commands "e" "e" "look" "w" "w"',
        'python scripts/mud_client.py run --commands "n" "e" "look" "w" "s"'
    ]
    
    for i, cmd in enumerate(search_commands, 1):
        print(f"\n  Search pattern {i}:")
        returncode, output = run_command(cmd)
        
        # Check output for bakery clues
        for keyword in bakery_keywords:
            if keyword in output.lower():
                print(f"    Found '{keyword}' in search!")
    
    # Test 5: Cleanup - disconnect
    print("\n5. Cleaning up:")
    returncode, output = run_command('python scripts/mud_client.py disconnect')
    
    print("\n" + "=" * 60)
    print("MISSION COMPLETE")
    print("=" * 60)
    print("\nAgent workflow demonstrated:")
    print("1. Initial assessment ✓")
    print("2. Area exploration ✓")
    print("3. Character status check ✓")
    print("4. Systematic search ✓")
    print("5. Clean disconnect ✓")
    print("\nFor actual bakery finding, the agent should:")
    print("- Parse room descriptions for bakery keywords")
    print("- Map explored areas")
    print("- Update data/player.md and data/world.md")
    print("- Use 'say' command to ask for directions if needed")

if __name__ == "__main__":
    main()