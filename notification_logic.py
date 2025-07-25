"""
Module to calculate all notification trigger points for a given Task.
Each notification is defined by:
- when it should be sent
- a unique key (for deduplication)
- a human-friendly prefix
- how many minutes before/after the event it is triggered
"""

from datetime import datetime
from typing import List, Tuple

from models import Task
from utils import parse_relative_time


def generate_notifications(
    task: Task,
    warn_before: List[str],
    warn_during: List[str],
    warn_overdue: List[str],
) -> List[Tuple[datetime, str, str, int]]:
    """
    For a given task and warning offsets, return a list of:
    (send_time, unique_key, prefix, minutes_delta) for each notification.

    - BEFORE: offsets before start_dt (e.g. 15m before)
    - DURING: offsets from start_dt (e.g. 0m = at start)
    - OVERDUE: offsets after end_dt (e.g. 15m after)

    Args:
        task: Task object with .start_dt and .end_dt
        warn_before: list of strings like ["15m", "5m"]
        warn_during: list of strings like ["0m"]
        warn_overdue: list of strings like ["15m", "5m"]

    Returns:
        List of (datetime, str, str, int) for each notification:
            - when to send
            - unique key for deduplication
            - message prefix for formatting
            - delta in minutes from event anchor
    """
    notifications: List[Tuple[datetime, str, str, int]] = []

    # --- BEFORE start ---
    for idx, offset in enumerate(warn_before, start=1):
        delta = parse_relative_time(offset)
        send_time = task.start_dt - delta
        minutes = abs(int(delta.total_seconds() // 60))
        key = f"before{idx}"
        prefix = f"in ⬇️{minutes}m\n\n"
        notifications.append((send_time, key, prefix, minutes))

    # --- DURING task ---
    for idx, offset in enumerate(warn_during, start=1):
        delta = parse_relative_time(offset)
        send_time = task.start_dt + delta
        minutes = abs(int(delta.total_seconds() // 60))
        key = f"during{idx}"
        prefix = "" if idx == 1 else f"▶️ +{minutes}m\n\n"
        notifications.append((send_time, key, prefix, minutes))

    # --- OVERDUE after end ---
    for idx, offset in enumerate(warn_overdue, start=1):
        delta = parse_relative_time(offset)
        send_time = task.end_dt + delta
        minutes = abs(int(delta.total_seconds() // 60))
        key = f"overdue{idx}"
        prefix = f"over⚠️{minutes}m\n\n"
        notifications.append((send_time, key, prefix, minutes))

    return notifications
