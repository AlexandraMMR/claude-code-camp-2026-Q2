# MUD Skill Guide

## Overview

This document describes the MUD-specific commands and workflows for the `mud-player` agent.

## Connection Details

- **Host**: localhost
- **Port**: 4000
- **Username**: dummy
- **Password**: helloworld

## Command Categories

### Navigation Commands

| Command | Description |
|---------|-------------|
| `n` | Move north |
| `s` | Move south |
| `e` | Move east |
| `w` | Move west |
| `u` | Move up |
| `d` | Move down |
| `look` | Examine current room |
| `examine <item>` | Examine a specific item |
| `exits` | List available exits from current room |

### Combat Commands

| Command | Description |
|---------|-------------|
| `kill <target>` | Attack a target |
| `kick <target>` | Kick a target |
| `bash <target>` | Bash a target or door |
| `flee` | Attempt to flee from combat |
| `backstab <target>` | Backstab a target (rogues/thieves) |
| `rescue <player>` | Rescue another player from combat |
| `consider <target>` | Evaluate target strength |

### Character Commands

| Command | Description |
|---------|-------------|
| `score` | Show character statistics |
| `stats` | Show character stats (alias for score) |
| `inventory` | Show carried items |
| `where` | Show locations of other players |
| `who` | Show online players |

### Inventory Commands

| Command | Description |
|---------|-------------|
| `get <item>` | Pick up an item |
| `drop <item>` | Drop an item |
| `wear <item>` | Wear an item |
| `remove <item>` | Remove worn item |
| `use <item>` | Use an item |

### System Commands

| Command | Description |
|---------|-------------|
| `commands` | List all available commands |
| `help <command>` | Show help for a specific command |
| `socials` | List available social commands |
| `quit` | Exit the game |

## Skill Workflows

### Exploration Workflow

1. Start with `look` and `score` to assess status
2. Use `exits` to see available directions
3. Move in one direction at a time
4. After each move, record `look` output and exits
5. Update `data/player.md` with current location
6. Update `data/world.md` with new room details
7. Periodically update `data/explored_map.json`

### Combat Workflow

1. Use `consider <target>` to evaluate combat viability
2. Enter combat with `kill <target>` or `kick <target>`
3. Monitor health and inventory during combat
4. Use `flee` if outmatched
5. Loot fallen enemies with `get all` (when safe)
6. Update `data/player.md` with loot and damage taken

### Practice Workflow

1. Find a safe combat area (practice dummies or weak NPCs)
2. Use `practice kick` or similar commands
3. Monitor success rate in combat log
4. Adjust tactics based on practice results
5. Document improvements in `data/player.md`

### Shopping Workflow

1. Use `commands` to find shop-related verbs
2. Use `help <shop-command>` for specific shop commands
3. Use `list` to see available items
4. Use `buy <item>` to purchase
5. Verify purchase with `inventory`

## Mapping Protocol

### Room Data Structure

```json
{
  "room_id": "unique_identifier",
  "name": "Room Name",
  "description": "Full room description",
  "exits": {
    "north": "target_room_id",
    "south": "target_room_id"
  },
  "npcs": ["npc_name_1", "npc_name_2"],
  "items": ["item_name_1", "item_name_2"],
  "features": ["special_feature"]
}
```

### Map Saving Steps

1. Record room details after each `look`
2. Map exits to target room IDs
3. Note NPCs, items, and special features
4. Add room to `data/explored_map.json`
5. Update `data/world.md` with navigation connections

## Troubleshooting

### Connection Issues
- Verify MUD is running on localhost:4000
- Check network connectivity with `telnet localhost 4000`
- Verify credentials in `.kiro/agents/mud-player.md`

### Navigation Problems
- Use `where` to see other players' locations
- Use `exits` frequently to avoid getting lost
- Keep track of previous rooms for backtracking

### Combat Difficulties
- Always `consider` targets before attacking
- Use `flee` when health is low
- Practice combat skills in safe areas first

## Best Practices

1. **Always assess**: Start every action with `look` and `score`
2. **Document discoveries**: Update memory files after each session
3. **Plan routes**: Map exits before moving through unknown areas
4. **Practice safely**: Train combat skills in practice areas
5. **Review periodically**: Check `data/player.md` and `data/world.md` for progress