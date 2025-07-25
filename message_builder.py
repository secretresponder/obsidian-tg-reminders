import re
from models import Task
from task_analyzer import analyze_task_text

def escape_markdown_v2(text: str) -> str:
    """
    Экранирует символы MarkdownV2 в тексте задачи.
    """
    # Экранируем все специальные символы, включая '-'
    escaped = re.sub(r'([\\_*[\]()~`>#+\-=|{}.!])', r'\\\1', text)

    # Если начинается с '-', экранируем отдельно
    if escaped.startswith('-'):
        escaped = '\\' + escaped

    return escaped


def format_notification_message(task: Task, notif_type: str, minutes_delta: int) -> str:
    # Заголовок
    if notif_type.startswith("before"):
        prefix = f"in ⬇️{minutes_delta}m"
    elif notif_type.startswith("overdue"):
        prefix = f"over⚠️{minutes_delta}m"
    elif notif_type.startswith("during"):
        prefix = "⏳ Now"
    else:
        prefix = ""

    # Разбор текста
    info = analyze_task_text(task)
    raw_text = info["cleaned_text"]
    emoji = info["priority_emoji"]

    # Только текст задачи и время экранируем — для MarkdownV2
    safe_text = escape_markdown_v2(raw_text)
    safe_time = escape_markdown_v2(info["time_range"])

    # Имя файла в формате YYYY-MM-DD
    from pathlib import Path
    stem = Path(task.file_path).stem
    safe_date = escape_markdown_v2(stem)

    # Финальное сообщение
    title_line = f"{emoji} {safe_text}" if info["has_priority"] else safe_text
    return f"`{prefix}`\n\n🕒 {safe_time}\n\n🔔 {title_line}\n\n`{safe_date}`"

