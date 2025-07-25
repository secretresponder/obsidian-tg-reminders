import re
from pathlib import Path
from models import Task
from parser import parse_task_lines

# === Эмоджи, обозначающие приоритет задачи ===
PRIORITY_ICONS = ["⏫", "⏬", "🔺", "🔼", "🔽"]

def analyze_task_text(task: Task) -> dict:
    """
    Разбирает текст задачи и возвращает словарь с информацией:
    - cleaned_text: текст без временных тегов и приоритетов
    - has_priority: есть ли приоритетный значок
    - priority_emoji: какой значок найден (или дефолт)
    - time_range: форматированный диапазон времени
    """
    raw_text = task.text

    # Поиск одного из приоритетных символов
    priority_match = re.search(r"[" + "".join(PRIORITY_ICONS) + r"]", raw_text)
    has_priority = bool(priority_match)
    priority_emoji = priority_match.group(0) if has_priority else "⏫"  # дефолт приоритета

    # Очистка текста от приоритетных символов и временных тегов
    cleaned_text = raw_text
    cleaned_text = re.sub(r"[" + "".join(PRIORITY_ICONS) + r"]", "", cleaned_text)
    cleaned_text = re.sub(r"\[startTime::.*?\]", "", cleaned_text)
    cleaned_text = re.sub(r"\[endTime::.*?\]", "", cleaned_text)
    cleaned_text = cleaned_text.strip()

    return {
        "cleaned_text": cleaned_text,
        "has_priority": has_priority,
        "priority_emoji": priority_emoji,
        "time_range": task.get_time_range()
    }


def format_task_for_telegram(task: Task, prefix: str = "") -> str:
    """
    Формирует Markdown-сообщение для Telegram:
    - добавляет префикс (например, "in ⬇️2m\n\n")
    - добавляет строку времени 🕒
    - добавляет значок приоритета (если он был)
    """
    info = analyze_task_text(task)

    # Сбор заголовка строки: добавляем приоритет, если он был
    title_line = f"{info['priority_emoji']} {info['cleaned_text']}" if info["has_priority"] else info["cleaned_text"]

    # Финальное форматирование
    message = f"{prefix}🕒 *{info['time_range']}*\n\n🔔 {title_line}"
    return message


def load_tasks_from_folder(folder_path: str) -> list[Task]:
    """
    Загружает задачи из всех Markdown-файлов в указанной папке.
    """
    path = Path(folder_path)
    if not path.exists() or not path.is_dir():
        raise ValueError(f"Invalid folder path: {folder_path}")

    all_tasks = []
    for file_path in path.glob("*.md"):
        all_tasks.extend(parse_task_lines(str(file_path)))
    return all_tasks
