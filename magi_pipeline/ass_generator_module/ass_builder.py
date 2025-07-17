import os
import re

def normalize_spaces(text):
    """
    Комплексна нормалізація пробілів у тексті.
    Видаляє всі типи пробілів (звичайні, табуляція, невидимі символи)
    та замінює їх на одиночні пробіли.
    """
    if not text:
        return text
    # Нормалізуємо всі типи пробілів
    text = re.sub(r'\s+', ' ', text)
    # Видаляємо пробіли на початку та в кінці
    text = text.strip()
    # Додатково видаляємо пробіли безпосередньо після тегів
    text = re.sub(r'(\{.*?\})\s+', r'\1', text)
    return text

def final_cleanup_spaces(text):
    """
    Фінальна очистка пробілів - додаткова перевірка для видалення
    будь-яких залишкових подвійних пробілів.
    """
    if not text:
        return text
    # Повторна нормалізація для впевненості
    text = re.sub(r'\s+', ' ', text)
    # Видаляємо пробіли на початку та в кінці
    text = text.strip()
    # Видаляємо пробіли безпосередньо після тегів
    text = re.sub(r'(\{.*?\})\s+', r'\1', text)
    # Видаляємо пробіли безпосередньо перед тегами
    text = re.sub(r'\s+(\{.*?\})', r'\1', text)
    return text

# Функція форматування часу у формат ASS (г:хв:сек.соті частки секунди)
def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h:01}:{m:02}:{s:02}.{cs:02}"

# Основна функція генерації ASS-файлу з шаблону стилів
def generate_ass(
    subs,
    output_path="output/episode01.ass",
    style_path="magi_pipeline/ass_generator_module/styles/Dialogue.ass",
    style_map=None,
):
    # Завантажуємо заголовок із шаблону стилів
    with open(style_path, "r", encoding="utf-8") as f:
        header = f.read()

    # Призначаємо стилі (можна кастомізувати через style_map)
    if style_map is None:
        style_map = {"op": "OP", "ed": "ED", "default": "Default"}

    # Готуємо директорію виводу
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    lines = [header]

    for segment in subs:
        start = format_timestamp(segment["start"])
        end = format_timestamp(segment["end"])
        text = segment["text"].replace("\n", " ").replace(",", "，")
        # --- Покращена нормалізація пробілів ---
        text = normalize_spaces(text)
        # Фінальна очистка для впевненості
        text = final_cleanup_spaces(text)

        # Вибір стилю — opening, ending чи default
        style = style_map["default"]
        if segment["start"] < 60:
            style = style_map["op"]
        elif segment["end"] > subs[-1]["end"] * 0.9:
            style = style_map["ed"]

        # Формуємо рядок субтитру
        dialogue = f"Dialogue: 0,{start},{end},{style},,0,0,0,,{text}"
        lines.append(dialogue)

    # Записуємо результат
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    # Тестові саби
    dummy_subs = [
        {"start": 0.5, "end": 2.0, "text": "Привіт, світ!"},
        {"start": 61.0, "end": 63.5, "text": "Це звичайний діалог."},
        {"start": 165.0, "end": 170.0, "text": "Фінальна сцена."},
    ]

    # Запускаємо генерацію .ass
    generate_ass(dummy_subs)
