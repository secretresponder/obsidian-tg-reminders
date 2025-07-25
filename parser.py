import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List
import logging

from models import Task
from utils import load_config

log = logging.getLogger(__name__)
cfg = load_config()

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

def parse_task_lines(file_path: str) -> List[Task]:
    tasks: List[Task] = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            if "- [ ]" not in line or "- [x]" in line:
                continue

            log.debug(f"[parser] 🔍 Found task candidate in {file_path}:{i} → {line_stripped}")

            start_m = re.search(r"\[startTime::\s*(\d{2}:\d{2})\]", line)
            end_m   = re.search(r"\[endTime::\s*(\d{2}:\d{2})\]",   line)

            if not start_m:
                log.debug(f"[parser] ⛔ No [startTime:: .. ] found in {file_path}:{i}")
                continue

            try:
                # Надёжно извлекаем дату из имени файла
                stem = Path(file_path).stem
                date_match = DATE_RE.search(stem)
                if not date_match:
                    raise ValueError(f"No valid date in filename: {stem}")

                date_str = date_match.group(0)
                start_dt = datetime.strptime(f"{date_str} {start_m.group(1)}", "%Y-%m-%d %H:%M")

                if end_m:
                    end_dt = datetime.strptime(f"{date_str} {end_m.group(1)}", "%Y-%m-%d %H:%M")
                else:
                    end_dt = start_dt + timedelta(minutes=15)

                task = Task(
                    file_path=file_path,
                    line_num=i,
                    text=line_stripped,
                    start_dt=start_dt,
                    end_dt=end_dt
                )
                tasks.append(task)
                log.info(f"[parser] ✅ Parsed task ({date_str}): {task.text}")

            except Exception as e:
                log.warning(f"[parser] ⚠️ Time parse error in {file_path}:{i} → {e}")

    except Exception as e:
        log.error(f"[parser] ❌ Failed to read file {file_path} → {e}")

    return tasks


def parse_tasks_from_files() -> List[Task]:
    tasks: List[Task] = []
    base_path = Path(cfg["TASKS_FOLDER"])

    if not base_path.exists():
        log.warning(f"[parser] 📁 Task folder not found: {base_path}")
        return tasks

    for file_path in base_path.rglob("*.md"):
        log.debug(f"[parser] 📄 Scanning file: {file_path}")
        tasks.extend(parse_task_lines(str(file_path)))

    log.info(f"[parser] ✅ Loaded {len(tasks)} tasks from Obsidian")
    return tasks
