# main.py

import asyncio
import os
from scheduler import main
from memory import load_message_ids
import logging




# === Логгер ===
log = logging.getLogger("main")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# 📍 Лог текущей рабочей директории
log.info(f"[BOOT] Python cwd: {os.getcwd()}")

# === Грузим ключи для удаления старых уведомлений ===

load_message_ids()

# === Пишем PID чтобы убить уже запущенный py, чтобы не дублировался при перезапусках 

PID_FILE = "C:\\obsidian-telegram-reminder-two\\main.pid"

def write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


if __name__ == "__main__":
    try:
        write_pid()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Shutdown by user")
