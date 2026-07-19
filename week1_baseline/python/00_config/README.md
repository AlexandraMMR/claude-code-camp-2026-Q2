# 00 · Configuration (Python)

This is the Python implementation of the Boukensha configuration system.

## Installation

```bash
pip install -r requirements.txt
```

## Running the Example

```bash
python examples/example.py
```

## Project Structure

```
week1_baseline/python/00_config/
├── boukensha/
│   ├── __init__.py       # Top-level package init
│   ├── config.py         # Configuration class
│   └── tasks/
│       ├── __init__.py
│       ├── base.py       # Abstract base task class
│       └── player.py     # Concrete player task
├── examples/
│   └── example.py        # Runnable smoke-test
├── prompts/
│   └── system.md         # Default system prompt
├── tests/
│   └── test_config.py    # pytest test suite
├── requirements.txt
└── pytest.ini
```

## Configuration

Configuration is loaded from `.boukensha/settings.yml` and `.boukensha/.env`.

### Settings Schema

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true

mud:
  host: localhost
  port: 4000
  username: dummy
  password: helloworld
```

## Environment Variables

Set `BOUKENSHA_DIR` to override the config directory (defaults to `~/.boukensha`).
