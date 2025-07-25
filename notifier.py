# notifier.py
import asyncio
import logging
from datetime import datetime
from typing import Callable, List

from models import Task
from task_analyzer import load_tasks_from_folder
from notification_logic import generate_notifications
from memory import load_sent_flags, mark_as_sent, save_sent_flags

log = logging.getLogger(__name__)

# 📌 Глобальный task_list
task_list: List[Task] = []

def should_send(now: datetime, when: datetime, key: str, tol_before: int, tol_during: int) -> bool:
    delta = (now - when).total_seconds()
    if key.startswith("overdue"):
        return delta >= 0
    if key.startswith("during"):
        return 0 <= delta <= tol_during
    if key.startswith("before"):
        return 0 <= delta <= tol_before
    return False

async def notification_loop(
    folder_path: str,
    warn_before: List[str],
    warn_during: List[str],
    warn_overdue: List[str],
    send_func: Callable,
    interval: int = 60,
    sent_flags: dict = None,
):
    log.info(f"[notifier] ✅ Started checking every {interval}s; folder={folder_path}")
    if sent_flags is None:
        sent_flags = load_sent_flags()

    from utils import load_config
    cfg = load_config()
    chat_args = {"chat_id": cfg["CHAT_ID"]}
    if cfg.get("TOPIC_ID"):
        chat_args["message_thread_id"] = cfg["TOPIC_ID"]

    tol_before = cfg.get("tolerance_before_sec", 300)
    tol_during = cfg.get("tolerance_during_sec", 1200)

    async def check_tasks_once():
        global task_list
        now = datetime.now()
        task_list = load_tasks_from_folder(folder_path)
        log.info(f"[notifier] 📋 Loaded {len(task_list)} tasks from {folder_path}")

        for task in task_list:
            task_id = task.stable_id
            already = sent_flags.get(task_id, set())
            notifications = generate_notifications(task, warn_before, warn_during, warn_overdue)

            for when, key, prefix, minutes_delta in notifications:
                if key in already:
                    continue
                if not should_send(now, when, key, tol_before, tol_during):
                    continue
                try:
                    await send_func(task, key, minutes_delta, chat_args)
                    already.add(key)
                    mark_as_sent(task_id, key)
                    log.info(f"[notifier] 📨 Sent {key} for {task_id}")
                except Exception as e:
                    log.warning(f"[notifier] ❌ Failed to send {key} for {task_id}, skipping save: {e}")
                    continue
            sent_flags[task_id] = already

        save_sent_flags(sent_flags)

    await check_tasks_once()
    while True:
        await asyncio.sleep(interval)
        await check_tasks_once()
