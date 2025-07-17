from pathlib import Path
import json

def ensure_dir(path: Path):
    """
    Створює директорію, якщо вона ще не існує.
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> list:
    """
    Читає JSON-файл і повертає список сегментів або інший Python-об'єкт.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(data: list | dict, path: Path):
    """
    Записує Python-об'єкт у JSON-файл з UTF-8.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def file_stem(file_path: Path) -> str:
    """
    Повертає ім'я файлу без розширення.
    """
    return file_path.stem
