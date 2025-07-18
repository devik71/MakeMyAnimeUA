#!/bin/bash

# 🎬 MakeMyAnimeUA — Стартовий скрипт для веб-інтерфейсу пайплайну

echo "🎬 MakeMyAnimeUA — Запуск веб-інтерфейсу пайплайну..."
echo "================================================="

# Перевіряємо чи Python3 встановлено
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не знайдено. Встановіть Python3."
    exit 1
fi

# Перевіряємо чи Flask встановлено
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask не знайдено. Спроба встановлення..."
    
    if command -v apt &> /dev/null; then
        echo "📦 Встановлення через apt..."
        sudo apt update && sudo apt install -y python3-flask
    elif command -v pip3 &> /dev/null; then
        echo "📦 Встановлення через pip3..."
        pip3 install --break-system-packages flask werkzeug
    else
        echo "❌ Не вдалося встановити Flask автоматично."
        echo "   Встановіть вручну: apt install python3-flask або pip3 install flask"
        exit 1
    fi
fi

# Перевіряємо залежності
echo "🔍 Перевірка залежностей..."
python3 -c "
try:
    import flask
    print('✅ Flask OK')
except ImportError:
    print('❌ Flask не встановлено')
    exit(1)

try:
    from magi_pipeline.utils.balthasar import Balthasar
    print('✅ Balthasar OK')
except ImportError as e:
    print(f'❌ Balthasar: {e}')

try:
    from magi_pipeline.utils.melchior import Melchior
    print('✅ Melchior OK')
except ImportError as e:
    print(f'⚠️  Melchior: {e}')
    print('   (deepl потрібно тільки для DeepL перекладу)')

try:
    from magi_pipeline.utils.caspar import Caspar
    print('✅ Caspar OK')
except ImportError as e:
    print(f'❌ Caspar: {e}')
"

echo ""
echo "🚀 Запуск веб-сервера..."
echo "🌐 Веб-інтерфейс буде доступний за адресою: http://localhost:5001"
echo "🛑 Для зупинки натисніть Ctrl+C"
echo ""

# Запускаємо веб-сервер
python3 main_pipeline_web.py