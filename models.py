# models.py

from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Task:
    """
    Представление задачи из Obsidian-файла.
    """
    file_path: str              # Путь к файлу, где найдена задача
    line_num: int               # Номер строки задачи
    text: str                   # Текст задачи
    start_dt: datetime          # Время начала задачи
    end_dt: datetime            # Время конца задачи
    sent_notifications: set[str] = field(default_factory=set)  # Что уже отправлено

    def get_time_range(self) -> str:
        """Вернуть диапазон времени задачи в формате HH:MM–HH:MM"""
        return f"{self.start_dt.strftime('%H:%M')}–{self.end_dt.strftime('%H:%M')}"

    @property
    def stable_id(self) -> str:
        from hashlib import md5
        from task_analyzer import analyze_task_text
        cleaned = analyze_task_text(self)["cleaned_text"]
        key_str = f"{self.start_dt.isoformat()}|{self.end_dt.isoformat()}|{cleaned}"
        return md5(key_str.encode()).hexdigest()

