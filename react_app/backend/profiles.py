"""Configuration profile persistence."""

import json
import os

PROFILES_FILE = os.path.join(os.path.dirname(__file__), "config_profiles.json")


def load_profiles() -> dict:
    if not os.path.exists(PROFILES_FILE):
        return {}
    with open(PROFILES_FILE) as f:
        return json.load(f)


def save_profile(name: str, config: dict) -> None:
    profiles = load_profiles()
    profiles[name] = config
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)


def delete_profile(name: str) -> None:
    profiles = load_profiles()
    profiles.pop(name, None)
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)
