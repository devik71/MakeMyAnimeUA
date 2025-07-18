# 🔧 Діагностика помилок завантаження файлів

## 🚨 **Якщо у вас виникає помилка при завантаженні файлу:**

### **📋 Крок 1: Перевірте консоль браузера**

1. **Відкрийте Developer Tools:**
   - **Chrome/Edge:** F12 або Ctrl+Shift+I
   - **Firefox:** F12 або Ctrl+Shift+K
   - **Safari:** Cmd+Option+I

2. **Перейдіть на вкладку "Console"**

3. **Спробуйте завантажити файл знову**

4. **Шукайте повідомлення з емодзі:**
   - 📤 Початок завантаження файлу
   - 📡 Отримано відповідь від сервера
   - 📋 Content-Type
   - ✅ Отримано JSON (успіх)
   - ❌ Помилки (детальна інформація)

---

## 🧪 **Крок 2: Використайте тестову сторінку**

Перейдіть на: **http://localhost:5001/test**

Ця сторінка показує детальну діагностику завантаження.

---

## 🔍 **Крок 3: Перевірте логи сервера**

```bash
./start_pipeline_server.sh logs
```

Шукайте помилки Python у логах.

---

## 💾 **Крок 4: Перевірте розмір файлу**

### **Ліміти:**
- **Максимальний розмір:** 2GB
- **Підтримувані формати:** MP4, AVI, MOV, MKV

### **Перевірка:**
```bash
ls -lh your_video_file.mp4
```

---

## 🌐 **Крок 5: Перевірте мережу**

### **Локальна перевірка:**
```bash
curl -I http://localhost:5001
```

### **Тест завантаження через командний рядок:**
```bash
curl -X POST -F "video=@your_file.mp4" http://localhost:5001/upload_video
```

---

## 🔧 **Часті проблеми та рішення:**

| Симптом | Можлива причина | Рішення |
|---------|----------------|---------|
| "Connection refused" | Сервер не працює | `./start_pipeline_server.sh start` |
| "HTTP 413" | Файл занадто великий | Використайте файл < 2GB |
| "HTTP 400" | Невалідний файл | Перевірте формат відео |
| "Network error" | Проблеми з мережею | Перезапустіть браузер |
| JSON parsing error | Сервер повернув HTML | Перезапустіть сервер |
| "Module not found" | Відсутні залежності | Встановіть залежності |

---

## 🔥 **Швидке виправлення:**

### **Універсальний reset:**
```bash
# 1. Зупинити сервер
./start_pipeline_server.sh stop

# 2. Очистити тимчасові файли
rm -rf uploads/* /tmp/pipeline_*

# 3. Перезапустити сервер
./start_pipeline_server.sh start

# 4. Перевірити статус
./start_pipeline_server.sh status
```

### **Перевірка залежностей:**
```bash
# Flask
python3 -c "import flask; print('Flask OK')"

# ffmpeg
ffprobe -version | head -1

# Permissions
ls -la start_pipeline_server.sh
```

---

## 📞 **Детальна діагностика:**

### **1. Перевірка JavaScript:**
Відкрийте http://localhost:5001 та дивіться консоль:

```javascript
// Має бути:
📤 Початок завантаження файлу: filename.mp4 Розмір: 12345678
📡 Отримано відповідь від сервера: 200 OK
📋 Content-Type: application/json
✅ Отримано JSON: {session_id: "...", analysis: {...}}
```

### **2. Перевірка Python:**
```bash
# В окремому терміналі
tail -f pipeline_server.log

# Потім завантажте файл і дивіться логи
```

### **3. Тест файлової системи:**
```bash
# Перевірка папки uploads
ls -la uploads/

# Перевірка дискового простору
df -h .

# Перевірка дозволів
ls -la . | grep uploads
```

---

## 🆘 **Якщо нічого не допомагає:**

### **Збір інформації для звіту:**

1. **Операційна система:**
   ```bash
   uname -a
   ```

2. **Версія Python:**
   ```bash
   python3 --version
   ```

3. **Розмір та тип файлу:**
   ```bash
   file your_video.mp4
   ls -lh your_video.mp4
   ```

4. **Логи сервера:**
   ```bash
   ./start_pipeline_server.sh logs > server_logs.txt
   ```

5. **Консоль браузера:** Скопіюйте всі повідомлення з консолі

---

## ✨ **Швидкі команди:**

```bash
# Статус системи
./start_pipeline_server.sh status && curl -I http://localhost:5001

# Повний reset
./start_pipeline_server.sh restart && echo "Сервер перезапущено"

# Діагностика
echo "=== ДІАГНОСТИКА ===" && \
python3 -c "import flask; print('✅ Flask OK')" && \
ffprobe -version >/dev/null && echo "✅ ffmpeg OK" && \
ls uploads/ >/dev/null && echo "✅ uploads OK" && \
curl -s http://localhost:5001 >/dev/null && echo "✅ Server OK"
```