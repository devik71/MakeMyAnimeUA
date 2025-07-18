# MakeMyAnimeUA — Пайплайн для перекладу та генерації субтитрів

Автоматизований пайплайн для витягання, транскрипції, перекладу та генерації субтитрів з відеофайлів.

## Структура модулів

- **magi_pipeline/utils/**
  - `balthasar.py` — Витягування аудіо та транскрипція (Whisper)
  - `melchior.py` — Переклад тексту (DeepL, HuggingFace)
  - `caspar.py` — Постобробка тексту (очищення, виправлення)
  - `file_utils.py` — Робота з файлами
- **magi_pipeline/translate/**
  - `translate.py`, `deepl_translate.py` — Переклад субтитрів
- **magi_pipeline/ass_generator_module/**
  - `ass_builder.py`, `generate_ass.py` — Генерація стилізованих ASS субтитрів

## Основні можливості

- Автоматичне витягання аудіо з відео
- Транскрипція аудіо (Whisper, підтримка GPU)
- Переклад субтитрів (DeepL, HuggingFace)
- Генерація ASS-файлів з різними стилями
- Постобробка та виправлення тексту
- Підтримка форматів: MKV, MP4, AVI, MOV

## Швидкий старт

1. Помістіть відеофайл у папку `input/`
2. Запустіть:
   ```bash
   python scripts/run_pipeline.py
   ```
3. Дотримуйтесь інструкцій у консолі (вибір потоку, стилю тощо)
4. Готові субтитри зʼявляться у папці `output/`

## Вимоги

**⚠️ Важливо:** Якщо виникають проблеми з установкою, дивіться файл `INSTALLATION_TROUBLESHOOTING.md`

### Швидка установка:
```bash
pip install -r requirements.txt
```

### Якщо виникають помилки, використовуйте:
```bash
pip install -r requirements_safe.txt
```

### Покрокова установка (рекомендовано):
```bash
# 1. Створіть віртуальне середовище
python -m venv magi_env
source magi_env/bin/activate  # Linux/macOS
# або magi_env\Scripts\activate  # Windows

# 2. Оновіть pip
pip install --upgrade pip setuptools wheel

# 3. Встановіть PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# 4. Встановіть решту залежностей
pip install -r requirements_safe.txt
```

**Основні залежності:**
- transformers
- torch, torchaudio
- sentencepiece
- language-tool-python
- openai-whisper
- ffmpeg-python
- deepl
- langdetect
- pyspellchecker
- requests

## Ліцензія

Проект розповсюджується під ліцензією MIT. Ви можете вільно використовувати, змінювати та розповсюджувати цей код з обовʼязковим збереженням авторства.
