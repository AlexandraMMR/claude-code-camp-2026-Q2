# Play MUD Agent Skill

A skill that enables AI agents to connect to and interact with a local CircleMUD server via Telnet.

## Prerequisites

1. Python 3.x installed
2. CircleMUD server running on `localhost:4000`
3. Character `dummy` with password `helloworld` created on the MUD

## Installation

This skill is self-contained. Simply place it in your agent skills directory or reference it directly.

## Structure

```
play-mud/
├── SKILL.md              # Agent instructions and workflow
├── config.json           # Connection configuration
├── scripts/
│   └── mud_client.py    # Main Python client
├── references/
│   └── circlemud_commands.md  # Command reference
├── data/
│   ├── player.md        # Player state template
│   └── world.md         # World state template
├── test_skill.py        # Verification script
└── README.md            # This file
```

## Usage Examples

### Agent Usage
When the agent needs to interact with the MUD, it should:

1. Read the `SKILL.md` file for workflow guidance
2. Consult `references/circlemud_commands.md` for command translation
3. Use `scripts/mud_client.py` with appropriate subcommands
4. Update `data/player.md` and `data/world.md` with current state

### Direct Python Usage
```bash
# Connect to MUD
python scripts/mud_client.py connect

# Send a command
python scripts/mud_client.py cmd --command "look"

# Send multiple commands
python scripts/mud_client.py run --commands "n" "look" "score"

# Get character status
python scripts/mud_client.py status --output status.json

# Interactive session
python scripts/mud_client.py session
```

## Natural Language Translation

The agent should translate natural language instructions using the command reference:

- "go north and look around" → `run --commands "n" "look"`
- "check my inventory and stats" → `run --commands "inventory" "score"`
- "attack the goblin" → `cmd --command "kill goblin"`

## Configuration

Edit `config.json` to change connection settings:
```json
{
  "host": "localhost",
  "port": 4000,
  "character": "dummy",
  "password": "helloworld"
}
```

## Testing

Run the verification script to check the skill structure:
```bash
python test_skill.py
```

## Error Handling

The client includes:
- Automatic reconnection with retries
- Timeout detection
- Prompt recognition (HP:, >, Huh?)
- Graceful error reporting

## Memory Management

The skill maintains state in:
- `data/player.md`: Current player status, inventory, location
- `data/world.md`: Explored rooms, NPCs, items, quests

Agents should update these files after significant actions.

## License

This skill is provided as part of the Claude Bootcamp 2026-Q2 curriculum.