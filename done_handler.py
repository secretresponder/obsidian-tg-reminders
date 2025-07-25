# done_handler.py
import logging
import json
from telegram import Update
from telegram.ext import ContextTypes
from pathlib import Path

from memory import get_message_mapping  # 💡 Новый импорт

log = logging.getLogger(__name__)

async def handle_done_button(update: Update, context: ContextTypes.DEFAULT_TYPE, task_list):
    try:
        query = update.callback_query
        await query.answer()

        parts = query.data.split("::")
        if len(parts) < 2:
            await query.edit_message_text("⚠️ Неверный формат callback_data.")
            return

        task_id = parts[1]
        found_task = next((t for t in task_list if t.stable_id == task_id), None)

        if found_task:
            path = Path(found_task.file_path)
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            lines[found_task.line_num] = lines[found_task.line_num].replace("- [ ]", "- [x]", 1)

            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            await query.edit_message_text("✅ Задача завершена.")
            log.info(f"[DONE] ✅ {found_task.text.strip()} ({task_id})")
            return

        # === fallback через message_ids.json ===
        mapping = get_message_mapping()
        if task_id in mapping:
            file_path, line_num = mapping[task_id]
            path = Path(file_path)

            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if "- [ ]" in lines[line_num]:
                lines[line_num] = lines[line_num].replace("- [ ]", "- [x]", 1)
                with open(path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                await query.edit_message_text("✅ Задача завершена (через fallback).")
                log.info(f"[DONE] 🛠 Fallback: {file_path}:{line_num}")
                return

        await query.edit_message_text("⚠️ Задача не найдена или уже изменена.")

    except Exception as e:
        log.error(f"[ERROR] handle_done_button: {e}")
        await update.callback_query.edit_message_text("⚠️ Ошибка при обработке задачи.")
