# Play MUD Agent Skill

This skill enables AI agents to connect to and interact with a local CircleMUD server via Telnet. It provides auto-login, command execution, natural language translation, character status queries, room mapping, and interactive sessions.

## Quick Start

1. Ensure a CircleMUD server is running on `localhost:4000`
2. Verify credentials in `config.json` (`dummy`/`helloworld`)
3. Use the skill commands to connect and interact

## Available Commands

The skill uses `scripts/mud_client.py` with these subcommands:

### `connect` - Connect to MUD and auto-login
```bash
python scripts/mud_client.py connect
```
Opens Telnet session, auto-logs in, returns initial room description.
**Note**: Connection remains open after this command. Use `disconnect` when done.

### `cmd` - Send a single raw command
```bash
python scripts/mud_client.py cmd look
```
Sends a single raw MUD command. If not already connected, establishes connection first.
**Connection remains open** after command for further actions.

### `disconnect` - Close connection
```bash
python scripts/mud_client.py disconnect
```
Manually disconnect from MUD server.

### `run` - Send a sequence of commands
```bash
python scripts/mud_client.py run --commands "n" "look" "score" --output response.txt
```
Sends commands one-by-one with 200ms delay between each, collects all responses.

### `status` - Get character status
```bash
python scripts/mud_client.py status --output status.json
```
Sends `score` and `inventory`, returns parsed character stats as JSON.

### `session` - Interactive REPL
```bash
python scripts/mud_client.py session
```
Starts an interactive loop - type commands, see live output.

### `map` - Build room map
```bash
python scripts/mud_client.py map --output room_map.json
```
Sends `look` + movement commands, builds/updates `room_map.json`.

## Natural Language Translation

When the agent receives a natural language instruction (e.g., "go north and look around"):

1. Consult `references/circlemud_commands.md` for command translations
2. Decompose into sequence of raw commands
3. Use `run` subcommand with the sequence
4. Example: "go north and look" → `run --commands "n" "look"`

## Configuration

Edit `config.json` to modify connection settings:
```json
{
  "host": "localhost",
  "port": 4000,
  "character": "dummy",
  "password": "helloworld"
}
```

**Note on Authentication**: Based on the HOW_TO_PLAY.md documentation and observed behavior, CircleMUD may use simplified authentication. If connection fails, try:

1. **Name-only authentication**: Some MUD setups use the character name as both username and password
2. **Debug mode**: Use `--debug` flag to see raw communication
3. **Manual test**: Run `python debug_connection.py` to troubleshoot

Alternative config if name-only authentication is needed:
```json
{
  "host": "localhost",
  "port": 4000,
  "character": "dummy",
  "password": "dummy"
}
```

## Error Handling

- **Server down**: 3 retries with 2s backoff
- **Login rejected**: Immediate failure
- **Command timeout**: Returns `[TIMEOUT]` marker
- **Unknown command**: Surface raw "Huh?" response

## Memory

During gameplay, the agent should maintain:
- `data/player.md`: Current player stats, inventory, location
- `data/world.md`: Explored rooms, NPCs, items discovered

## Agent Workflow Examples

### Example 1: Simple Exploration
**Agent task**: "Explore the area north of the temple"
```bash
python scripts/mud_client.py run --commands "n" "look" "n" "look" "s" "s" "look"
```

### Example 2: Character Status Check
**Agent task**: "Check character health and inventory"
```bash
python scripts/mud_client.py status --output data/player_status.json
```

### Example 3: Bakery Search Mission
**Agent task**: "Find the bakery"
```bash
# Explore systematically
python scripts/mud_client.py run --commands "look" "n" "look" "e" "look" "s" "look" "w" "look"

# Check for bakery clues in output
# If not found, expand search
python scripts/mud_client.py run --commands "n" "n" "look" "e" "e" "look" "s" "s" "look"
```

### Example 4: Complete Session
**Agent task**: "Connect, explore, check status, disconnect"
```bash
# Single connection, multiple operations
python scripts/mud_client.py connect
python scripts/mud_client.py cmd look
python scripts/mud_client.py cmd n
python scripts/mud_client.py cmd look
python scripts/mud_client.py status --output status.json
python scripts/mud_client.py disconnect
```

### Best Practice for Agents
1. Use `run` for sequences of related commands
2. Use `status` to get character info
3. Use `connect` + multiple `cmd` + `disconnect` for complex sessions
4. Always check room descriptions for clues
5. Update `data/player.md` and `data/world.md` with discoveries

## References

- `references/circlemud_commands.md`: Complete command reference sheet
- Standard CircleMUD 3.x commands apply


## Example: Finding the Bakery

Here's a specific example of how an agent could find the bakery in CircleMUD:

### Phase 1: Initial Exploration
```bash
# Connect and get initial bearings
python scripts/mud_client.py cmd --command "look"

# Check inventory and stats to understand character capabilities
python scripts/mud_client.py status --output status.json

# Explore immediate area
python scripts/mud_client.py run --commands "n" "look" "s" "e" "look" "w" "look" "u" "look" "d" "look"
```

### Phase 2: Systematic Search
The agent should:
1. Read room descriptions carefully for bakery-related keywords
2. Note down all exits from each room
3. Create a mental map of explored areas
4. Look for patterns (market districts, commercial areas)

### Phase 3: Advanced Techniques
If bakery isn't found in immediate area:
```bash
# Ask for directions if other players are present
python scripts/mud_client.py cmd --command "say Does anyone know where the bakery is?"

# Check who's online and where they are
python scripts/mud_client.py run --commands "who" "where"

# Explore further in promising directions
python scripts/mud_client.py run --commands "n" "n" "look" "e" "e" "look" "s" "s" "look" "w" "w" "look"
```

### Phase 4: Documentation
After finding the bakery, the agent should:
1. Update `data/world.md` with bakery location
2. Update `data/player.md` with current location
3. Note any important NPCs or items in the bakery

### Agent Thought Process
When searching for the bakery, the agent should:
- Parse room descriptions looking for: "bakery", "oven", "bread", "pastry", "flour", "bake"
- Look for NPCs with names like "baker", "pastry chef"
- Check for food-related items in room descriptions
- Note commercial areas vs residential areas
- Remember paths taken to avoid getting lost

### Common Bakery Locations in MUDs
Based on typical MUD geography:
- Often in market districts or town squares
- Sometimes near taverns or inns
- May be in commercial areas with other shops
- Could be near grain mills or farms (for supply chain)

### If Lost
If the agent gets lost, it can:
1. Use `quit` and reconnect to return to starting point
2. Look for landmarks to reorient
3. Ask other players for help with `say`
4. Systematically map the area using the `map` command