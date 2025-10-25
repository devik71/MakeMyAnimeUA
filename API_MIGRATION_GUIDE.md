# 🔄 Гід по міграції на нову API систему

## Що змінилося

### ✅ Покращення безпеки
- **API ключі винесено в змінні середовища** - більше немає хардкодених ключів у коді
- **Безпечний Flask secret key** - автоматична генерація або з .env файлу  
- **Валідація API ключів** - перевірка формату перед використанням

### ✅ Нова архітектура API
- **Модульна система** - окремі класи для кожного API
- **Автоматичний вибір движка** - система сама обирає найкращий доступний движок
- **Batch обробка** - оптимізований переклад великих обсягів тексту
- **Proper logging** - замість print() використовується система логування

### ✅ Зворотна сумісність
- Старий код продовжує працювати з попередженнями
- Поступова міграція без поломки існуючого функціоналу

## Швидка міграція

### 1. Створіть .env файл

```bash
# Скопіюйте шаблон
cp .env.template .env

# Відредагуйте .env файл
nano .env
```

### 2. Встановіть API ключі

```bash
# У .env файлі:
DEEPL_API_KEY=ваш_ключ_тут
FLASK_SECRET_KEY=згенерований_безпечний_ключ
```

### 3. Оновіть залежності

```bash
pip install -r requirements.txt
```

### 4. Протестуйте систему

```bash
python scripts/test_api_system.py
```

## Детальна міграція коду

### Старий спосіб (застарілий):

```python
# ЗАСТАРІЛИЙ КОД
from magi_pipeline.translate.deepl_translate import deepl_translate

# Хардкодений API ключ у файлі
result = deepl_translate("Привіт", api_key="hardcoded_key")
```

### Новий спосіб (рекомендований):

```python
# НОВИЙ КОД
from magi_pipeline.api.deepl_api import DeepLAPI
from magi_pipeline.api.translation_api import TranslationAPI

# API ключ з змінних середовища
deepl_api = DeepLAPI()
result = deepl_api.translate_text("Привіт")

# Або використовуйте універсальний API
translation_api = TranslationAPI()
result = translation_api.translate_text("Привіт", engine="auto")
```

### Оновлення Melchior:

```python
# Старий спосіб (все ще працює)
from magi_pipeline.utils.melchior import Melchior
result = Melchior.translate("Привіт", engine="deepl", api_key="key")

# Новий спосіб (рекомендований)
from magi_pipeline.utils.melchior import Melchior
result = Melchior.translate("Привіт", engine="auto")  # API ключ з .env
```

## Нові можливості

### 1. Автоматичний вибір движка

```python
from magi_pipeline.api.translation_api import TranslationAPI

api = TranslationAPI()

# Система автоматично обере найкращий доступний движок
result = api.translate_text("Текст", engine="auto")
```

### 2. Batch переклад

```python
texts = ["Привіт", "Як справи?", "До побачення"]

# Оптимізований batch переклад
results = api.translate_batch(texts, engine="deepl")
```

### 3. Інформація про движки

```python
# Дізнайтесь які движки доступні
available = api.get_available_engines()
print(f"Доступні: {available}")

# Детальна інформація
info = api.get_engine_info()
print(f"DeepL використання: {info['deepl']['usage']}")
```

### 4. Система логування

```python
from magi_pipeline.config import setup_logging

logger = setup_logging()
logger.info("Інформаційне повідомлення")
logger.warning("Попередження")
logger.error("Помилка")
```

## Конфігурація через .env

### Основні параметри:

```bash
# Безпека
FLASK_SECRET_KEY=your_secure_key_here
DEEPL_API_KEY=your_deepl_key_here

# Веб-сервер  
DEBUG=False
HOST=127.0.0.1
PORT=5001

# Переклад
TRANSLATION_ENGINE=auto
SOURCE_LANGUAGE=ru
TARGET_LANGUAGE=uk
```

### Whisper налаштування:

```bash
WHISPER_DEFAULT_MODEL=base
WHISPER_USE_GPU=True
WHISPER_DEVICE=auto
```

## Тестування

### Запуск повного тестування:

```bash
python scripts/test_api_system.py
```

### Тестування окремих компонентів:

```python
from magi_pipeline.api.deepl_api import test_deepl_connection
from magi_pipeline.api.translation_api import test_translation_engines

# Тест DeepL
deepl_result = test_deepl_connection()
print(deepl_result)

# Тест всіх движків
engines_result = test_translation_engines()
print(engines_result)
```

## Усунення проблем

### Проблема: "DeepL API недоступний"
**Рішення:** Перевірте DEEPL_API_KEY у .env файлі

### Проблема: "Helsinki-NLP модель не завантажується"
**Рішення:** 
```bash
pip install transformers torch
```

### Проблема: "Логи не створюються"
**Рішення:** Перевірте права на запис у папці проекту

### Проблема: "Flask secret key попередження"
**Рішення:** Додайте FLASK_SECRET_KEY у .env файл

## Переваги нової системи

### 🔒 Безпека
- Немає хардкодених ключів
- Автоматична валідація
- Безпечні сесії Flask

### 🚀 Продуктивність  
- Batch обробка
- Автоматичний вибір движка
- Кешування моделей

### 🛠 Зручність
- Централізована конфігурація
- Детальне логування
- Зворотна сумісність

### 📊 Моніторинг
- Статистика використання API
- Логування помилок
- Інформація про движки

## Підтримка

Якщо виникають проблеми з міграцією:

1. Запустіть тестування: `python scripts/test_api_system.py`
2. Перевірте логи у папці `logs/`
3. Переконайтесь що .env файл налаштований правильно
4. Перевірте що всі залежності встановлені: `pip install -r requirements.txt`