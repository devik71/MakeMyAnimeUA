# 🚨 Швидке рішення для Windows

## Помилка: `CMAKE_C_COMPILER not set` або подібні

### ✅ РІШЕННЯ (5 хвилин):

1. **Завантажте Visual Studio Community:**
   👉 https://visualstudio.microsoft.com/vs/community/

2. **У вікні "Visual Studio Installer":**
   - Перейдіть на вкладку **"Workloads"**
   - Знайдіть секцію **"Desktop & Mobile"**
   - Поставте галочку біля: ✅ **"Desktop development with C++"**

3. **Праворуч у колонці "Installation details" переконайтеся, що вибрано:**
   - ✅ **MSVC v143 - VS 2022 C++ x64/x86 build tools**
   - ✅ **Windows 10 SDK** (або 11, якщо є)
   - ✅ **C++ CMake tools for Windows**

4. **Перезапустіть комп'ютер**

5. **Спробуйте установку знову:**
   ```bash
   pip install -r requirements.txt
   ```

### 🔍 Альтернативи:
- Використайте `requirements_safe.txt`
- Дивіться детальний гайд у `INSTALLATION_TROUBLESHOOTING.md`

---
**Це вирішує 90% проблем з установкою на Windows!** 🎉