"""
Example script demonstrating Boukensha configuration.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path for imports
example_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(example_dir.parent))

# Override the config directory so the example works from the repo root.
# In real usage a user's ~/.boukensha is picked up automatically.
env_boukensha_dir = os.environ.get("BOUKENSHA_DIR")
if env_boukensha_dir is None:
    os.environ["BOUKENSHA_DIR"] = str(Path(__file__).resolve().parent.parent.parent.parent.parent / ".boukensha")

from boukensha import Config
from boukensha.tasks.player import Player

config = Config()
player_settings = config.tasks("player")

print("=== Boukensha Step 0: Configuration ===")
print()
print(f"Config dir:     {config.dir}")
print(f"Tasks:          {', '.join(config.tasks().keys())}")
print()
print("-- player task --")
print(f"Provider:       {Player.provider(player_settings)}")
print(f"Model:          {Player.model(player_settings)}")
print(f"Prompt override?{Player.prompt_override(player_settings, 'system')}")
system_prompt = Player.system_prompt(
    player_settings, 
    user_prompts_dir=str(config.user_prompts_dir()),
    default_prompts_dir=str(Config.PROMPTS_DIR)
)
print(f"System prompt:  {system_prompt[:60] if system_prompt else None}...")
print()
print(f"MUD host:       {config.mud_host()}:{config.mud_port()}")
print(f"MUD user:       {config.mud_username()}")
print()
print(f"API key set?    {os.environ.get('ANTHROPIC_API_KEY') is not None}")
print()
print(config)
