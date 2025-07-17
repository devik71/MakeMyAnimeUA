from pathlib import Path
import json

# 🧱 Імпортуємо нашу утиліту для створення ASS-файлу
from magi_pipeline.ass_generator_module.ass_builder import build_ass_file

def generate_ass_subs(json_path: Path, ass_path: Path, style_path: Path):
    """
    Створює ASS-файл із перекладеного JSON-файлу.
    
    Parameters:
    - json_path: шлях до json-файлу з субтитрами
    - ass_path: шлях до збереження .ass-файлу
    - style_path: шлях до .ass стилю, який буде інклюджений у фінальний субтитр
    """

    # 📂 Завантажуємо перекладені репліки
    with open(json_path, "r", encoding="utf-8") as f:
        segments = json.load(f)

    # 🧱 Створюємо ASS-файл на основі шаблону стилю + таймінгів із JSON
    build_ass_file(segments=segments, output_path=ass_path, style_path=style_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("❗ Usage: python generate_ass.py input.json output.ass style.ass")
    else:
        generate_ass_subs(
            json_path=Path(sys.argv[1]),
            ass_path=Path(sys.argv[2]),
            style_path=Path(sys.argv[3])
        )
