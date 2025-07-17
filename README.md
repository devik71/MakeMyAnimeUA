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

Встановіть залежності з `requirements.txt`:

```
pip install -r requirements.txt
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
