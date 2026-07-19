# Play MUD — Skill Design Document

## 1. Skill Identity

| Field | Value |
|---|---|
| **Name** | `play-mud` |
| **Description** | Connect an AI agent to a local CircleMUD server via Telnet. Supports auto-login, raw command execution, natural-language-to-command translation, character status queries, room mapping, and interactive sessions. |
| **Install path** | `c:\Users\mmara\Claude bootcamp\claude-code-camp-2026-Q2\week0_explore\explore_architecture\02_agent_skills\play-mud\` |

---

## 2. Directory Structure

```
02_agent_skills/
└── play-mud/
    ├── SKILL.md                   ← Agent instructions & workflow
    ├── config.json                ← Stored credentials (host, port, char, pass)
    └── scripts/
        └── mud_client.py          ← Main CLI helper script
    └── references/
        └── circlemud_commands.md  ← Reference sheet of stock CircleMUD commands
```

---

## 3. Existing Skills Referenced

**None** — this skill is standalone. No science bundle skills overlap with MUD gameplay.

---

## 4. Credentials Storage

`config.json` (stored inside the skill directory, local to workspace):

```json
{
  "host": "localhost",
  "port": 4000,
  "character": "dummy",
  "password": "helloworld"
}
```

> [!WARNING]
> This file contains a plaintext password. It is local-only and never transmitted outside the machine.

---

## 5. Helper Script: `mud_client.py`

A Python CLI script using `argparse` with the following subcommands:

| Subcommand | Arguments | What it does |
|---|---|---|
| `connect` | `--output FILE` | Opens Telnet session, auto-logs in as `dummy`, returns initial room description |
| `cmd` | `--command TEXT`, `--output FILE` | Sends a single raw MUD command, streams response until prompt or 2s timeout |
| `run` | `--commands TEXT...`, `--output FILE` | Sends a sequence of commands one-by-one, collects all responses |
| `status` | `--output FILE` | Sends `score` and `inventory`, returns parsed character stats as JSON |
| `session` | *(none)* | Starts an interactive REPL loop — type commands, see live output |
| `map` | `--output FILE` | Sends `look` + movement commands, builds/updates `room_map.json` |

### Connection behaviour
- **Transport:** Python `telnetlib` (stdlib, no pip install needed)
- **Auto-login:** Sends character name → password during handshake
- **Prompt detection:** Reads until `HP:` / `>` prompt pattern OR 2-second silence
- **Retry on drop:** Up to **3 retries** with 2s backoff before failing loudly

### Natural-language translation
- Handled in **SKILL.md** — the agent receives the natural-language instruction and uses the `references/circlemud_commands.md` cheat-sheet to decompose it into a sequence of raw commands, then calls `run` with that sequence.
- No LLM API call is made inside the script itself.

---

## 6. Rate Limiting

CircleMUD is a local server with no external API — no HTTP rate limiting needed.  
A **command delay of 200ms** between successive commands will be enforced in `run` mode to avoid flooding the MUD server's command queue.

---

## 7. Memory 

Use data/player.md and data/world.md to record the current player and world state during each loop.        

---

## 8. Error Handling Strategy

| Scenario | Behaviour |
|---|---|
| Server down / port refused | Retry 3× with 2s backoff → fail with clear error message |
| Login rejected (wrong password) | Fail immediately with `LoginError` |
| Command timeout (>2s no response) | Return whatever was received + `[TIMEOUT]` marker |
| Unknown command (MUD returns `Huh?`) | Surface raw response; agent decides next step |
| Map file missing | Create a fresh `room_map.json` automatically |

---

## 8. CircleMUD Command Reference (bundled)

A `circlemud_commands.md` reference covering:
- **Movement:** `n`, `s`, `e`, `w`, `u`, `d`, `look`, `exits`
- **Combat:** `kill`, `flee`, `cast`, `rescue`
- **Interaction:** `say`, `tell`, `buy`, `sell`, `open`, `close`, `unlock`
- **Inventory:** `inventory`, `get`, `drop`, `wear`, `remove`, `wield`
- **Info:** `score`, `stats`, `who`, `where`, `map`
- **Admin/misc:** `quit`, `save`, `help`

---

## 9. Sample Query / Validation

**Input to agent:** *"Connect to the MUD, check my character's HP and gold, then go north and look around."*

**Expected skill behaviour:**
1. Run `connect` → get room description
2. Run `status` → parse `score` output → report HP and gold
3. Run `cmd --command "n"` → get new room description
4. Run `cmd --command "look"` → get room details
5. Write all output to a file and report results

---

## 10. Open Questions (resolved)

| Question | Answer |
|---|---|
| Telnet or REST? | Raw Telnet on `localhost:4000` |
| Character exists? | Yes — `dummy` / `helloworld` |
| Stock CircleMUD? | Assumed stock 3.x (treat unknowns gracefully) |
| NL translation? | Agent-side using command reference cheat-sheet |
| Map subcommand? | Yes |
| Install location? | `c:\Users\mmara\Claude bootcamp\claude-code-camp-2026-Q2\week0_explore\explore_architecture\02_agent_skills\play-mud\` |
