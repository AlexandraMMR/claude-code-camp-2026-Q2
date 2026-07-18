#!/usr/bin/env python3
"""
Test script for the Play MUD skill.
This script verifies the skill structure and provides a simple test.
"""

import os
import json
import sys
from pathlib import Path

def check_structure():
    """Verify the skill directory structure."""
    print("Checking skill structure...")
    
    current_dir = Path(__file__).parent.parent  # Go up one level to main skill dir
    required_files = [
        "SKILL.md",
        "config.json",
        "scripts/mud_client.py",
        "references/circlemud_commands.md",
        "data/player.md",
        "data/world.md"
    ]
    
    all_good = True
    for file_path in required_files:
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_good = False
    
    return all_good

def check_config():
    """Verify config.json structure."""
    print("\nChecking config.json...")
    
    config_path = Path(__file__).parent.parent / "config.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        required_keys = ['host', 'port', 'character', 'password']
        for key in required_keys:
            if key in config:
                print(f"✓ {key}: {config[key]}")
            else:
                print(f"✗ {key} - MISSING")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Error reading config.json: {e}")
        return False

def check_python_script():
    """Verify mud_client.py structure."""
    print("\nChecking mud_client.py...")
    
    script_path = Path(__file__).parent.parent / "scripts" / "mud_client.py"
    if not script_path.exists():
        print("✗ mud_client.py - MISSING")
        return False
    
    try:
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Check for required components
        checks = [
            ("telnetlib import", "telnetlib" in content),
            ("argparse import", "argparse" in content),
            ("MUDClient class", "class MUDClient" in content),
            ("connect method", "def connect" in content),
            ("send_command method", "def send_command" in content),
        ]
        
        all_passed = True
        for check_name, passed in checks:
            if passed:
                print(f"✓ {check_name}")
            else:
                print(f"✗ {check_name}")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"✗ Error reading mud_client.py: {e}")
        return False

def main():
    """Run all checks."""
    print("=" * 50)
    print("Play MUD Skill Verification")
    print("=" * 50)
    
    structure_ok = check_structure()
    config_ok = check_config()
    script_ok = check_python_script()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    if structure_ok and config_ok and script_ok:
        print("✅ All checks passed!")
        print("\nSkill is ready to use.")
        print("\nTo test the skill:")
        print("1. Ensure CircleMUD server is running on localhost:4000")
        print("2. Run: python scripts/mud_client.py connect")
        print("3. Test with: python scripts/mud_client.py cmd --command 'look'")
    else:
        print("❌ Some checks failed.")
        print("\nPlease fix the issues above before using the skill.")
    
    return 0 if (structure_ok and config_ok and script_ok) else 1

if __name__ == "__main__":
    sys.exit(main())