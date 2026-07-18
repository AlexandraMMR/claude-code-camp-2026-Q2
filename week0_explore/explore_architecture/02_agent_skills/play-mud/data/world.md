# World State

**Last Explored**: [timestamp]

## Explored Rooms
```yaml
Rooms:
  - id: 
    name: 
    description: 
    exits:
      north: 
      south: 
      east: 
      west: 
      up: 
      down: 
    items: 
    npcs: 
    visited: 
    last_visit: 
```

## Known NPCs
```yaml
NPCs:
  - name: 
    type: 
    location: 
    disposition: 
    last_seen: 
    known_dialogue: 
```

## Discovered Items
```yaml
Items:
  - name: 
    type: 
    location_found: 
    properties: 
    value: 
```

## Shops & Services
```yaml
Shops:
  - name: 
    location: 
    type: 
    known_items: 
    prices: 
```

## Quests & Objectives
```yaml
Quests:
  - name: 
    status: active/completed/failed
    description: 
    objectives: 
    rewards: 
    giver: 
    location: 
```

## Hazards & Dangers
```yaml
Dangerous Areas:
  - location: 
    threat_level: 
    enemies: 
    warnings: 
```

## Secrets & Discoveries
```yaml
Secrets:
  - location: 
    type: hidden door/secret passage/trap
    discovered: 
    details: 
```

## Navigation Notes
```yaml
Landmarks:
  - name: 
    location: 
    description: 
    relative_position: 

Pathways:
  - from: 
    to: 
    directions: 
    distance: 
    notes: 
```

## Map Data
```yaml
Coordinate System:
  origin: 
  explored_range: 
  grid_notes: 

Key Locations:
  - spawn_point: 
    safe_zones: 
    resource_nodes: 
    dungeons: 
    towns: 
```