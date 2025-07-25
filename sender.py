# sender.py
from telegram.constants import ParseMode
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from pathlib import Path
import logging
import random

from message_builder import format_notification_message
from memory import (
    save_message_id,
    get_message_id,
    delete_message_id,
    get_all_message_ids,
)
from task_analyzer import analyze_task_text

log = logging.getLogger(__name__)

def build_send_notification(bot: Bot):
    async def send_notification(task, key, minutes_delta, chat_args):
        notif_type = (
            "before" if key.startswith("before") else
            "overdue" if key.startswith("overdue") else
            "during" if key.startswith("during") else
            "main"
        )

        task_id = task.stable_id
        filename = Path(task.file_path).stem

        try:
            # Удаление устаревших уведомлений этого task_id
            existing_keys = get_all_message_ids(task_id).keys()
            to_check = []

            if notif_type == "before":
                current_idx = int(key.replace("before", ""))
                to_check = [f"before{i}" for i in range(1, current_idx)]

            elif notif_type == "during":
                to_check = [k for k in existing_keys if k.startswith("before")]

            elif notif_type == "overdue":
                current_idx = int(key.replace("overdue", ""))
                to_check = (
                    [k for k in existing_keys if k.startswith("before") or k.startswith("during")]
                    + [f"overdue{i}" for i in range(1, current_idx)]
                )

            for old_key in to_check:
                msg_id = get_message_id(task_id, old_key)
                if msg_id:
                    try:
                        await bot.delete_message(chat_id=chat_args["chat_id"], message_id=msg_id)
                        delete_message_id(task_id, old_key)
                        log.info(f"[🗑] Deleted outdated notification {old_key} for {task_id} [{filename}]")
                    except Exception as e:
                        log.warning(f"[⚠️] Could not delete old {old_key} message: {e}")

            # Кнопка завершения с доп.данными
            callback_data = f"done::{task.stable_id}"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✔ Завершить", callback_data=callback_data)]])

            # Отправка
            await asyncio.sleep(random.uniform(0.2, 0.5))
            text = format_notification_message(task, notif_type, minutes_delta)
            sent = await bot.send_message(
                chat_id=chat_args["chat_id"],
                text=text,
                message_thread_id=chat_args.get("message_thread_id"),
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=keyboard
            )

            save_message_id(task_id, key, sent.message_id)
            log.info(f"[SENT] {notif_type.upper()} | {task.text.strip()} ({task_id}) [{filename}]")

        except Exception as e:
            log.error(f"[ERROR] Failed to send {notif_type} for task {task_id} [{filename}]: {e}")
            raise

    return send_notification
