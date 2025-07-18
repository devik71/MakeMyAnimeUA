#!/bin/bash

# 🎬 MakeMyAnimeUA — Стартовий скрипт для веб-сервера пайплайну

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/pipeline_server.pid"
LOG_FILE="$SCRIPT_DIR/pipeline_server.log"

echo "🎬 MakeMyAnimeUA — Веб-сервер пайплайну"
echo "======================================="

# Функція для перевірки чи процес працює
check_process() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # Процес працює
        else
            rm -f "$PID_FILE"  # Видаляємо застарілий PID файл
            return 1  # Процес не працює
        fi
    fi
    return 1  # PID файл не існує
}

# Функція для зупинки сервера
stop_server() {
    echo "🛑 Зупинка сервера..."
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            sleep 2
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "⚠️  Процес не зупинився, примусова зупинка..."
                kill -9 "$PID"
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    # Додаткова перевірка через pkill
    pkill -f "main_pipeline_web.py" 2>/dev/null || true
    echo "✅ Сервер зупинено"
}

# Функція для запуску сервера
start_server() {
    echo "🚀 Запуск сервера..."
    
    cd "$SCRIPT_DIR"
    
    # Перевіряємо Python3
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 не знайдено"
        exit 1
    fi
    
    # Перевіряємо Flask
    if ! python3 -c "import flask" 2>/dev/null; then
        echo "⚠️  Flask не знайдено, спроба встановлення..."
        sudo apt update && sudo apt install -y python3-flask
    fi
    
    # Запускаємо сервер у фоні
    nohup python3 main_pipeline_web.py > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    
    # Зберігаємо PID
    echo "$SERVER_PID" > "$PID_FILE"
    
    # Чекаємо кілька секунд та перевіряємо статус
    sleep 3
    if check_process; then
        echo "✅ Сервер запущено успішно!"
        echo "📍 URL: http://localhost:5001"
        echo "📋 PID: $SERVER_PID"
        echo "📝 Логи: $LOG_FILE"
        
        # Перевіряємо чи сервер відповідає
        if curl -s -f http://localhost:5001 > /dev/null; then
            echo "🌐 Сервер працює та відповідає на запити"
        else
            echo "⚠️  Сервер запущено, але поки не відповідає (чекайте кілька секунд)"
        fi
    else
        echo "❌ Не вдалося запустити сервер"
        echo "📝 Перевірте логи: $LOG_FILE"
        exit 1
    fi
}

# Функція для перезапуску
restart_server() {
    echo "🔄 Перезапуск сервера..."
    stop_server
    sleep 1
    start_server
}

# Функція для статусу
status_server() {
    if check_process; then
        PID=$(cat "$PID_FILE")
        echo "✅ Сервер працює (PID: $PID)"
        echo "📍 URL: http://localhost:5001"
        
        # Перевіряємо відповідь
        if curl -s -f http://localhost:5001 > /dev/null; then
            echo "🌐 Сервер відповідає на запити"
        else
            echo "⚠️  Сервер запущено, але не відповідає"
        fi
    else
        echo "❌ Сервер не працює"
    fi
}

# Основна логіка
case "${1:-start}" in
    start)
        if check_process; then
            echo "⚠️  Сервер вже працює"
            status_server
        else
            start_server
        fi
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        status_server
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            echo "📝 Останні логи сервера:"
            tail -20 "$LOG_FILE"
        else
            echo "📝 Логи не знайдено"
        fi
        ;;
    *)
        echo "Використання: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Команди:"
        echo "  start   - Запустити сервер"
        echo "  stop    - Зупинити сервер" 
        echo "  restart - Перезапустити сервер"
        echo "  status  - Показати статус сервера"
        echo "  logs    - Показати останні логи"
        exit 1
        ;;
esac