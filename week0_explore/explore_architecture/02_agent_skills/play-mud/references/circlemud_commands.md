# CircleMUD Command Reference

This document provides a reference for standard CircleMUD commands to help translate natural language instructions into MUD commands.

## Movement Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `n` | `north` | Move north |
| `s` | `south` | Move south |
| `e` | `east` | Move east |
| `w` | `west` | Move west |
| `u` | `up` | Move up |
| `d` | `down` | Move down |
| `ne` | `northeast` | Move northeast |
| `nw` | `northwest` | Move northwest |
| `se` | `southeast` | Move southeast |
| `sw` | `southwest` | Move southwest |
| `look` | `l` | Look at current room |
| `exits` | | Show available exits |

## Combat Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `kill` | `k`, `attack` | Attack a target |
| `flee` | `run` | Attempt to flee from combat |
| `cast` | | Cast a spell (requires spell name) |
| `rescue` | | Rescue another player from combat |
| `hit` | | Continue attacking current target |
| `bash` | | Bash a door or opponent |
| `backstab` | | Backstab a target (rogues/thieves) |

## Interaction Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `say` | `'` | Say something to room |
| `tell` | | Tell something to specific player |
| `buy` | | Buy an item from a shop |
| `sell` | | Sell an item to a shop |
| `open` | | Open a door or container |
| `close` | | Close a door or container |
| `unlock` | | Unlock a door or container |
| `lock` | | Lock a door or container |
| `knock` | | Knock on a door |
| `give` | | Give an item to someone |

## Inventory Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `inventory` | `i`, `inv` | Show inventory |
| `get` | `take` | Pick up an item |
| `drop` | | Drop an item |
| `wear` | `wield` | Wear/wield equipment |
| `remove` | `rem` | Remove equipment |
| `equipment` | `eq` | Show equipped items |
| `put` | | Put item in container |
| `get` | | Get item from container |

## Information Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `score` | | Show character stats |
| `stats` | | Show detailed character statistics |
| `who` | | Show who is online |
| `where` | | Show where players are |
| `time` | | Show game time |
| `help` | `?` | Get help on commands |
| `help <topic>` | | Get help on specific topic |
| `map` | | Show ASCII map of area |
| `consider` | | Evaluate a target's strength |
| `quests` | | Show active quests |

## Character Development

| Command | Aliases | Description |
|---------|---------|-------------|
| `train` | | Train skills at trainer |
| `practice` | | Practice skills |
| `study` | | Study spells |
| `skills` | | Show learned skills |
| `spells` | | Show known spells |

## Social Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `emote` | `:` | Perform an emote |
| `socials` | | List available social commands |
| `group` | | Manage group |
| `follow` | | Follow another player |
| `stop` | | Stop following |

## Admin/Misc Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `quit` | | Quit the game |
| `save` | | Save character |
| `afk` | | Set AFK status |
| `bug` | | Report a bug |
| `idea` | | Submit an idea |
| `typo` | | Report a typo |

## Natural Language Translation Guide

### Movement Instructions
- "go north" → `n`
- "move east" → `e`
- "walk south" → `s`
- "head west" → `w`
- "go up/down" → `u`/`d`
- "look around" → `look`

### Combat Instructions
- "attack the goblin" → `kill goblin`
- "cast fireball" → `cast fireball`
- "flee from combat" → `flee`

### Interaction Instructions
- "say hello" → `say hello`
- "buy a sword" → `buy sword`
- "open the door" → `open door`

### Inventory Instructions
- "pick up the key" → `get key`
- "drop the rock" → `drop rock`
- "wear the armor" → `wear armor`

### Information Instructions
- "check my stats" → `score`
- "see who's online" → `who`
- "look at inventory" → `inventory`

## Common Command Sequences

For natural language instructions that require multiple actions:

- "go north and look around" → `run --commands "n" "look"`
- "check stats and inventory" → `run --commands "score" "inventory"`
- "explore the area" → `run --commands "look" "n" "look" "s" "look" "e" "look" "w" "look"`

## Notes

1. Most commands can be abbreviated (e.g., `n` for `north`)
2. Some commands require targets (e.g., `kill goblin`)
3. Commands are case-insensitive
4. Multiple commands can be combined with `;` in some MUDs
5. Use `help <command>` for detailed information on any command