# Agent Task: Find the Bakery in CircleMUD

## Objective
Locate and document the bakery in the CircleMUD world using the play-mud skill.

## Success Criteria
- [ ] Bakery location identified
- [ ] Path to bakery documented
- [ ] Bakery description recorded
- [ ] Any NPCs or items in bakery noted
- [ ] World state updated in `data/world.md`

## Required Tools
- `play-mud` skill with `mud_client.py`
- Natural language understanding of room descriptions
- Basic mapping/navigation skills

## Step-by-Step Approach

### 1. Initial Assessment
```bash
# Connect and see starting location
python scripts/mud_client.py cmd --command "look"
```
**Expected Output Analysis**: 
- Note room name and description
- Identify available exits (n, s, e, w, u, d)
- Look for any bakery-related clues

### 2. Character Status Check
```bash
# Understand character capabilities
python scripts/mud_client.py status --output data/player_status.json
```
**Purpose**: Know HP, inventory, and abilities before exploring.

### 3. Immediate Area Exploration
```bash
# Explore all exits from starting point
python scripts/mud_client.py run --commands "n" "look" "s" "e" "look" "w" "look"
```
**Strategy**: 
- For each direction, execute command and look
- Parse room descriptions for bakery clues
- Build mental map of immediate area

### 4. Bakery Identification Clues
Look for these keywords in room descriptions:
- **Primary**: "bakery", "bakehouse", "bread shop"
- **Secondary**: "oven", "flour", "dough", "pastry", "loaf"
- **Tertiary**: "aroma of bread", "warm smell", "freshly baked"
- **NPCs**: "baker", "pastry chef", "mill worker"
- **Items**: "bread", "rolls", "cakes", "pies", "flour sacks"

### 5. Systematic Exploration Pattern
If bakery not found immediately:
```bash
# Explore northward
python scripts/mud_client.py run --commands "n" "n" "look" "e" "look" "w" "look"

# Explore southward  
python scripts/mud_client.py run --commands "s" "s" "look" "e" "look" "w" "look"

# Explore eastward
python scripts/mud_client.py run --commands "e" "e" "look" "n" "look" "s" "look"

# Explore westward
python scripts/mud_client.py run --commands "w" "w" "look" "n" "look" "s" "look"
```

### 6. Advanced Techniques
If still not found:
```bash
# Check for other players who might know
python scripts/mud_client.py run --commands "who" "say Hello, can anyone direct me to the bakery?"

# Look for commercial district patterns
# (Multiple shops clustered together, market squares, etc.)
```

### 7. Documentation
Once bakery found:
1. **Update `data/world.md`**:
   - Add bakery room description
   - Note path from starting location
   - Document any NPCs or items
2. **Update `data/player.md`**:
   - Current location
   - Path taken
   - Items discovered
3. **Create navigation notes**:
   - Step-by-step directions from starting point
   - Landmarks along the way

## Troubleshooting

### If Connection Fails
- Verify MUD server is running: `docker compose up --build` in `week0_explore/infrastructure`
- Check config.json credentials
- Use `--debug` flag for connection issues

### If Lost
- Use `quit` command to return to starting point
- Look for familiar landmarks
- Create simple map using pencil and paper or notes

### If No Bakery Found
- Expand search radius
- Look for alternative food sources (taverns, inns, markets)
- Ask NPCs if interactive (try `say` to NPCs)

## Expected MUD Commands Used
- `look` - Examine current room
- `n`/`s`/`e`/`w`/`u`/`d` - Movement
- `exits` - Show all exits
- `who` - Show online players
- `where` - Show player locations
- `say` - Communicate with others
- `score` - Check character status
- `inventory` - Check carried items

## Agent Notes
- **Be methodical**: Don't wander randomly
- **Take notes**: Document room descriptions and exits
- **Look for patterns**: Commercial areas often cluster together
- **Ask for help**: Use `say` if other players are present
- **Stay safe**: Avoid dangerous areas if character is low level

## Completion Checklist
- [ ] Bakery location confirmed
- [ ] Path documented with directions
- [ ] Room description recorded
- [ ] NPCs/items documented
- [ ] Data files updated
- [ ] Agent can reliably return to bakery