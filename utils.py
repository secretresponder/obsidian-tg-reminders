# utils.py

import json
import os
import re
from pathlib import Path
from datetime import timedelta

# === CONFIG LOADER ===

# Assumes config.json lives next to this utils.py
CONFIG_PATH = Path(__file__).parent / "config.json"

def load_config() -> dict:
    """
    Load the bot configuration from config.json.
    """
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# === TIME PARSING UTILITY ===

def parse_relative_time(offset_str: str) -> timedelta:
    """
    Convert a string like '10m', '-2h', '+15m' into a timedelta.
    Supports 'm' (minutes) and 'h' (hours). Invalid formats return zero timedelta.
    """
    offset_str = offset_str.strip()
    match = re.fullmatch(r"([+-]?)(\d+)\s*([mh])", offset_str)
    if not match:
        # Unrecognized format → zero offset
        return timedelta()

    sign_str, value_str, unit = match.groups()
    value = int(value_str)
    sign = -1 if sign_str == '-' else 1

    if unit == 'm':
        return timedelta(minutes=sign * value)
    else:  # unit == 'h'
        return timedelta(hours=sign * value)

# === ARGS ====

def telegram_args() -> dict:
    return {
        "chat_id": config.get("CHAT_ID"),
        "message_thread_id": config.get("TOPIC_ID")
    }

