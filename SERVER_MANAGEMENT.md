# 🎬 MakeMyAnimeUA — Управління Веб-Сервером

## 🚀 **Швидкий старт**

### **Запуск сервера:**
```bash
./start_pipeline_server.sh start
```

### **Перевірка статусу:**
```bash
./start_pipeline_server.sh status
```

### **Доступ до веб-інтерфейсу:**
- 🌐 **URL:** http://localhost:5001
- 📱 **Порт:** 5001
- 🔗 **Інтерфейси:** localhost (127.0.0.1) та 0.0.0.0

---

## 📋 **Повний список команд**

| Команда | Опис |
|---------|------|
| `./start_pipeline_server.sh start` | Запустити сервер |
| `./start_pipeline_server.sh stop` | Зупинити сервер |
| `./start_pipeline_server.sh restart` | Перезапустити сервер |
| `./start_pipeline_server.sh status` | Показати статус |
| `./start_pipeline_server.sh logs` | Показати логи |

### **Короткі алiаси (після перезавантаження терміналу):**
```bash
start-pipeline    # Запустити
stop-pipeline     # Зупинити  
status-pipeline   # Статус
```

---

## 🔧 **Автозапуск**

### **Налаштовано:**
- ✅ **При відкритті терміналу** — автоматично запускається
- ✅ **Алiаси** — короткі команди для управління
- ⚠️ **Cron** — недоступний в цьому середовищі

### **Ручне налаштування автозапуску:**
```bash
./setup_autostart.sh
```

---

## 🐛 **Діагностика та виправлення помилок**

### **Сервер не запускається:**

1. **Перевірити залежності:**
   ```bash
   python3 -c "import flask"
   ```

2. **Перевірити порт:**
   ```bash
   curl -I http://localhost:5001
   ```

3. **Переглянути логи:**
   ```bash
   ./start_pipeline_server.sh logs
   ```

### **Сервер не відповідає:**

1. **Примусово зупинити всі процеси:**
   ```bash
   pkill -f main_pipeline_web.py
   ```

2. **Перезапустити:**
   ```bash
   ./start_pipeline_server.sh restart
   ```

### **Порт зайнятий:**
```bash
# Знайти процес на порту 5001
ps aux | grep 5001

# Вбити процес по PID
kill [PID_NUMBER]
```

---

## 📝 **Логи та моніторинг**

### **Файли логів:**
- 📄 **Основні логи:** `/workspace/pipeline_server.log`
- 📄 **PID файл:** `/workspace/pipeline_server.pid`

### **Моніторинг в реальному часі:**
```bash
# Слідкувати за логами
tail -f pipeline_server.log

# Показати останні 50 рядків
tail -50 pipeline_server.log
```

---

## ⚙️ **Конфігурація**

### **Налаштування Flask:**
- **Host:** `0.0.0.0` (всі інтерфейси)
- **Port:** `5001`
- **Debug:** `True` (тільки для розробки)

### **Зміна порту:**
Відредагуйте файл `main_pipeline_web.py`:
```python
app.run(debug=True, port=5002, host='0.0.0.0')  # Змінити 5001 на 5002
```

---

## 🔒 **Безпека**

### **⚠️ Важливо для продакшену:**
- Вимкнути debug режим
- Використовувати WSGI сервер (gunicorn, uwsgi)
- Налаштувати nginx reverse proxy
- Додати HTTPS

### **Поточні налаштування (тільки для розробки):**
- Debug режим увімкнено
- Flask development server
- HTTP без шифрування

---

## 🚨 **Часті проблеми та рішення**

| Проблема | Причина | Рішення |
|----------|---------|---------|
| "Connection refused" | Сервер не запущено | `./start_pipeline_server.sh start` |
| "Port already in use" | Інший процес займає порт | `pkill -f main_pipeline_web.py` |
| "Module not found" | Відсутні залежності | `sudo apt install python3-flask` |
| "Permission denied" | Неправильні дозволи | `chmod +x start_pipeline_server.sh` |
| Сервер "зависає" | Помилка в коді | Перевірити логи, перезапустити |

---

## 📞 **Швидка довідка**

**Щоб швидко запустити сервер:**
```bash
./start_pipeline_server.sh start && echo "Сервер: http://localhost:5001"
```

**Щоб швидко перезапустити:**
```bash
./start_pipeline_server.sh restart
```

**Щоб подивитися чи все працює:**
```bash
./start_pipeline_server.sh status && curl -s http://localhost:5001 > /dev/null && echo "✅ Все працює!"
```