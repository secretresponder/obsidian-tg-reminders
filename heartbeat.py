# heartbeat.py
from utils import load_config
import logging
import asyncio
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

def get_current_slot():
    now = datetime.now()
    hour = now.hour
    minute = now.minute

    # Номер слота от 1 до 48 (по 30 мин)
    slot_index = hour * 2 + (1 if minute >= 30 else 0) + 1

    # Формируем границы слота
    slot_start = now.replace(minute=0 if minute < 30 else 30, second=0, microsecond=0)
    slot_end = slot_start + timedelta(minutes=30)

    time_fmt = lambda dt: dt.strftime("%H:%M")
    return f"slot {slot_index} ({time_fmt(slot_start)}–{time_fmt(slot_end)})"

async def heartbeat(bot, interval=1800):  # 1800s = 30 минут
    cfg = load_config()
    chat_args = {"chat_id": cfg["CHAT_ID"]}
    if cfg.get("TOPIC_ID"):
        chat_args["message_thread_id"] = cfg["TOPIC_ID"]

    while True:
        try:
            slot_info = get_current_slot()
            text = f"🕯 {slot_info}"
            await bot.send_message(**chat_args, text=text, parse_mode="HTML")
            log.info(f"✅ Heartbeat sent: {slot_info}")
        except Exception as e:
            log.error(f"❌ Heartbeat failed: {e}")
        await asyncio.sleep(interval)
