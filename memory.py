from pathlib import Path
import json
import logging
from typing import Dict, Set, Union, Tuple

log = logging.getLogger(__name__)

MEMORY_FILE = Path("sent_notifications.json")
MESSAGE_FILE = Path("message_ids.json")

_memory: Dict[str, Set[str]] = {}
_message_ids: Dict[str, Dict[str, int]] = {}
_message_meta: Dict[str, Tuple[str, int]] = {}  # task_id → (file_path, line_num)


def load_sent_flags(path: Union[str, Path] = None) -> Dict[str, Set[str]]:
    global _memory
    file = Path(path) if path else MEMORY_FILE

    if file.exists():
        try:
            with open(file, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            _memory = {task_id: set(flags) for task_id, flags in raw.items()}
            log.info(f"[memory] ✅ Loaded sent flags from {file}")
        except Exception as e:
            log.error(f"[memory] ❌ Error loading sent flags: {e}")
            _memory = {}
    else:
        _memory = {}
        log.info(f"[memory] ℹ No memory file at {file}, starting fresh")
        save_sent_flags()

    return _memory


def save_sent_flags(data: Dict[str, Set[str]] = None):
    to_save = data if data is not None else _memory
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump({k: list(v) for k, v in to_save.items()}, f, indent=2, ensure_ascii=False)
    log.info(f"[memory] 💾 Saved sent flags to {MEMORY_FILE}")


def mark_as_sent(task_id: str, key: str):
    if task_id not in _memory:
        _memory[task_id] = set()
    _memory[task_id].add(key)


def save_message_id(task_id: str, key: str, message_id: int, file_path: str = None, line_num: int = None):
    if task_id not in _message_ids:
        _message_ids[task_id] = {}

    _message_ids[task_id][key] = message_id

    if file_path is not None and line_num is not None:
        _message_meta[task_id] = (file_path, line_num)

    with open(MESSAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "ids": _message_ids,
            "meta": _message_meta
        }, f, indent=2, ensure_ascii=False)

    log.info(f"[memory] 💾 Saved message IDs to {MESSAGE_FILE}")


def get_message_id(task_id: str, key: str) -> Union[int, None]:
    return _message_ids.get(task_id, {}).get(key)


def delete_message_id(task_id: str, key: str):
    if task_id in _message_ids and key in _message_ids[task_id]:
        del _message_ids[task_id][key]
        with open(MESSAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "ids": _message_ids,
                "meta": _message_meta
            }, f, indent=2, ensure_ascii=False)
        log.info(f"[memory] 🗑 Deleted message_id for {task_id}::{key}")


def load_message_ids():
    global _message_ids, _message_meta
    if MESSAGE_FILE.exists():
        try:
            with open(MESSAGE_FILE, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            _message_ids = raw.get("ids", {})
            _message_meta = {k: tuple(v) for k, v in raw.get("meta", {}).items()}
            log.info(f"[memory] ✅ Loaded message IDs from {MESSAGE_FILE}")
        except Exception as e:
            log.error(f"[memory] ❌ Error loading message IDs: {e}")
            _message_ids = {}
            _message_meta = {}
    else:
        _message_ids = {}
        _message_meta = {}
        log.info(f"[memory] ℹ No message file, starting fresh")


def get_all_message_ids(task_id: str) -> dict:
    return _message_ids.get(task_id, {}).copy()


def get_message_mapping() -> Dict[str, Tuple[str, int]]:
    """Возвращает task_id → (file_path, line_num) для fallback-обработки кнопок."""
    return _message_meta.copy()
