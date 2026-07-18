# Play MUD Agent Skill

This skill enables AI agents to connect to and interact with a local CircleMUD server via Telnet. It provides auto-login, command execution, natural language translation, character status queries, room mapping, and interactive sessions.

## Directory Structure

```
play-mud/
├── config.json           # Connection settings (host, port, credentials)
├── SKILL.md             # Main skill documentation and agent instructions
├── README.md            # This file - organization overview
├── scripts/             # Python scripts for MUD interaction
│   ├── mud_client.py         # Core MUD client with connection management
│   ├── simple_explorer.py    # Demonstration of goal decomposition and map saving
│   ├── systematic_agent.py   # Agent with structured exploration workflow
│   ├── final_demonstration.py # Complete demonstration of exploration patterns
│   └── debug_connection.py   # Connection troubleshooting utility
├── data/                # Runtime data storage
│   ├── player.md             # Current player state and stats
│   ├── world.md              # Explored rooms and discoveries
│   ├── explored_map.json     # Structured exploration data
│   ├── current_status.json   # Last status command output
│   └── explored_map.json     # Map data from exploration
├── test/                # Test scripts
│   ├── test_bakery_mission.py # Bakery finding test
│   └── test_skill.py         # Basic skill validation
└── references/          # Reference documentation
    └── circlemud_commands.md # Complete MUD command reference
```

## Scripts Overview

### mud_client.py (Core)
The main MUD client with:
- Persistent Telnet connection management
- Auto-login sequence
- Command execution with timeout handling
- State tracking (is_connected, connection_status)
- Command sequences via `run` subcommand
- Character status parsing
- Interactive session mode
- Map building capability

### simple_explorer.py
Demonstration script showing:
- Goal decomposition before execution
- Systematic map saving in JSON format
- Room discovery tracking
- Navigation path documentation

### systematic_agent.py
Agent implementation with:
- Goal decomposition engine
- State file management (player, world, discoveries)
- Command execution with retry logic
- Discovery parsing and storage
- Navigation notes tracking

### final_demonstration.py
Complete demonstration of:
- Goal decomposition workflow
- Systematic map saving
- Command discovery process
- Complete agent workflow structure

### debug_connection.py
Connection troubleshooting with:
- Raw Telnet session debugging
- Login sequence verification
- Timeout testing

## Quick Start

1. Ensure a CircleMUD server is running on `localhost:4000`
2. Verify credentials in `config.json` (`dummy`/`helloworld`)
3. Test connection: `python scripts/mud_client.py cmd look`
4. Explore: `python scripts/mud_client.py run --commands "n" "look" "s" "look"`

## Agent Instructions

See `SKILL.md` for comprehensive agent instructions including:
- Available commands and usage
- Natural language translation
- Configuration options
- Error handling
- Best practices for exploration
- Goal decomposition strategy

## Command Reference

All available MUD commands are documented in:
- `references/circlemud_commands.md` - Complete command reference (100+ commands)
- `scripts/mud_client.py` - Command implementation
- In-game: Use `commands` command to list all available verbs

## Development Workflow

1. **Discovery Phase**: Use `commands` to learn available actions
2. **Exploration Phase**: Systematically map areas with map saving
3. **Goal Phase**: Decompose tasks into executable steps
4. **Documentation Phase**: Update data files with discoveries

## Testing

Run tests from the play-mud directory:
```bash
cd week0_explore/explore_architecture/02_agent_skills/play-mud
python test/test_bakery_mission.py
python test/test_skill.py
```

## Troubleshooting

- **Connection timeouts**: Increase timeout in config.json or check MUD server
- **Login failures**: Verify credentials in config.json, check HOW_TO_PLAY.md for auth details
- **Commands not working**: Use `commands` to verify command names
- **Lost navigation**: Use `where` or `status` to check position
## Scripts

The skill includes several demonstration scripts in the `scripts/` folder:

| Script | Purpose |
|--------|---------|
| `mud_client.py` | Main Python client with Telnet connectivity |
| `debug_connection.py` | Debug tool for troubleshooting connections |
| `simple_explorer.py` | Simple demonstration of map saving and exploration |
| `final_demonstration.py` | Comprehensive demonstration of agent workflow |
| `systematic_agent.py` | Foundation for automated agent with goal decomposition |

## Tests

The `test/` folder contains:

| Script | Purpose |
|--------|---------|
| `test_skill.py` | Verifies skill structure and configuration |
| `test_bakery_mission.py` | Tests bakery finding workflow |

## Data

The `data/` folder stores:

| File | Purpose |
|------|---------|
| `explored_map.json` | Structured room and connection data |
| `player.md` | Player state template |
| `world.md` | World exploration template |
| `test_status.json` | Test character status (from tests) |