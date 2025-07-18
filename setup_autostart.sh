#!/bin/bash

# 🎬 MakeMyAnimeUA — Налаштування автозапуску веб-сервера

echo "🎬 MakeMyAnimeUA — Налаштування автозапуску"
echo "==========================================="

WORKSPACE_DIR=$(pwd)
START_SCRIPT="$WORKSPACE_DIR/start_pipeline_server.sh"

echo "📁 Робоча директорія: $WORKSPACE_DIR"
echo "🚀 Стартовий скрипт: $START_SCRIPT"

# Перевіряємо чи скрипт існує
if [ ! -f "$START_SCRIPT" ]; then
    echo "❌ Стартовий скрипт не знайдено: $START_SCRIPT"
    exit 1
fi

# Метод 1: Додаємо в .bashrc (для інтерактивних сесій)
echo ""
echo "📝 Метод 1: Додавання в .bashrc"
BASHRC_LINE="# MakeMyAnimeUA автозапуск"
BASHRC_COMMAND="$START_SCRIPT start >/dev/null 2>&1"

if grep -q "MakeMyAnimeUA автозапуск" ~/.bashrc 2>/dev/null; then
    echo "⚠️  Запис вже є в .bashrc"
else
    echo "$BASHRC_LINE" >> ~/.bashrc
    echo "$BASHRC_COMMAND" >> ~/.bashrc
    echo "✅ Додано в ~/.bashrc"
fi

# Метод 2: Cron job (якщо доступний)
echo ""
echo "📝 Метод 2: Cron job"
if command -v crontab >/dev/null 2>&1; then
    CRON_LINE="@reboot $START_SCRIPT start >/dev/null 2>&1"
    
    # Перевіряємо чи cron job вже існує
    if crontab -l 2>/dev/null | grep -q "start_pipeline_server.sh"; then
        echo "⚠️  Cron job вже існує"
    else
        # Додаємо cron job
        (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
        echo "✅ Додано cron job для автозапуску"
    fi
else
    echo "⚠️  Cron не доступний"
fi

# Метод 3: Алiас для швидкого запуску
echo ""
echo "📝 Метод 3: Алiас для швидкого запуску"
ALIAS_LINE="alias start-pipeline='$START_SCRIPT start'"
ALIAS_LINE2="alias stop-pipeline='$START_SCRIPT stop'"
ALIAS_LINE3="alias status-pipeline='$START_SCRIPT status'"

if grep -q "start-pipeline" ~/.bashrc 2>/dev/null; then
    echo "⚠️  Алiаси вже існують"
else
    echo "" >> ~/.bashrc
    echo "# MakeMyAnimeUA алiаси" >> ~/.bashrc
    echo "$ALIAS_LINE" >> ~/.bashrc
    echo "$ALIAS_LINE2" >> ~/.bashrc
    echo "$ALIAS_LINE3" >> ~/.bashrc
    echo "✅ Додано алiаси: start-pipeline, stop-pipeline, status-pipeline"
fi

echo ""
echo "🎉 Налаштування завершено!"
echo ""
echo "📋 Доступні команди:"
echo "   ./start_pipeline_server.sh start   - Запустити сервер"
echo "   ./start_pipeline_server.sh stop    - Зупинити сервер"
echo "   ./start_pipeline_server.sh status  - Статус сервера"
echo "   ./start_pipeline_server.sh restart - Перезапустити"
echo "   ./start_pipeline_server.sh logs    - Показати логи"
echo ""
echo "📱 Після перезавантаження термінала:"
echo "   start-pipeline   - Запустити"
echo "   stop-pipeline    - Зупинити"
echo "   status-pipeline  - Статус"
echo ""
echo "🌐 URL сервера: http://localhost:5001"