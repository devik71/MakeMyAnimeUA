# Вирішення проблем з установкою

## 🚨 НАЙПОШИРЕНІША ПРОБЛЕМА (Windows)

**Якщо ви отримуєте помилку `CMAKE_C_COMPILER not set`:**

1. **Завантажте Visual Studio Community:** https://visualstudio.microsoft.com/vs/community/
2. **У вікні "Visual Studio Installer":**
   - Вкладка **"Workloads"** → секція **"Desktop & Mobile"**
   - Поставте галочку: ✅ **"Desktop development with C++"**
   - Праворуч переконайтеся, що вибрано: **MSVC**, **Windows SDK**, **CMake tools**
3. **Перезапустіть комп'ютер**
4. **Спробуйте установку знову**

Це вирішує 90% проблем з установкою на Windows!

---

## Детальні рішення для різних проблем

### 1. Помилка з CMake та компіляторами

**Проблема:** `CMAKE_C_COMPILER not set` або `CMAKE_CXX_COMPILER not set`

**⚠️ ГОЛОВНА ПРИЧИНА НА WINDOWS:** Відсутні Visual Studio Build Tools або C++ Development Tools

**Рішення для Windows (ОБОВ'ЯЗКОВО):**

#### Варіант 1: Visual Studio Community (Рекомендовано)
1. Завантажте Visual Studio Community: https://visualstudio.microsoft.com/vs/community/
2. У вікні "Visual Studio Installer":
   - Перейдіть на вкладку **"Workloads"**
   - Знайдіть секцію **"Desktop & Mobile"**
   - Поставте галочку біля: ✅ **"Desktop development with C++"**
3. Праворуч у колонці "Installation details" переконайтеся, що вибрано:
   - ✅ **"MSVC v143 - VS 2022 C++ x64/x86 build tools"**
   - ✅ **"Windows 10 SDK"** (або Windows 11 SDK, якщо є)
   - ✅ **"C++ CMake tools for Windows"**
4. Перезапустіть комп'ютер після установки

#### Варіант 2: Тільки Build Tools (мінімальний)
1. Завантажте Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. При установці оберіть:
   - ✅ **"C++ build tools"**
   - ✅ **"MSVC v143 - VS 2022 C++ x64/x86 build tools"**
   - ✅ **"Windows 11 SDK"**

#### Варіант 3: Через chocolatey
```bash
# Встановити chocolatey спочатку: https://chocolatey.org/install
choco install visualstudio2022buildtools --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools"
choco install cmake
```

#### Перевірка установки:
Відкрийте нову командну строку та виконайте:
```bash
cl
# Має показати версію Microsoft C/C++ Compiler

cmake --version
# Має показати версію CMake
```

**Рішення для Linux:**
```bash
sudo apt-get update
sudo apt-get install build-essential cmake
```

**Рішення для macOS:**
```bash
xcode-select --install
brew install cmake
```

### 2. Проблема з архітектурою платформи

**Проблема:** `does not support platform specification, but platform x64 was specified`

**Рішення:**
```bash
# Оновіть pip до останньої версії
pip install --upgrade pip

# Встановіть wheel
pip install wheel

# Спробуйте встановити без специфікації платформи
pip install --no-deps sentencepiece
```

### 3. Проблеми з sentencepiece

**Альтернативний спосіб встановлення:**
```bash
# Варіант 1: Встановлення з conda-forge
conda install -c conda-forge sentencepiece

# Варіант 2: Встановлення попередньо зібраного wheel
pip install sentencepiece --find-links https://download.pytorch.org/whl/torch_stable.html
```

### 4. Проблеми з PyTorch

**Рішення:**
```bash
# Для CPU-версії
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Для GPU (CUDA 11.8)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Для GPU (CUDA 12.1)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## Покрокова установка

### Крок 1: Підготовка середовища
```bash
# Створіть віртуальне середовище
python -m venv magi_env

# Активуйте його
# Windows:
magi_env\Scripts\activate
# Linux/macOS:
source magi_env/bin/activate

# Оновіть pip
pip install --upgrade pip setuptools wheel
```

### Крок 2: Встановлення основних залежностей
```bash
# Встановіть PyTorch спочатку
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Встановіть transformers
pip install transformers
```

### Крок 3: Встановлення проблемних пакетів
```bash
# Спробуйте встановити sentencepiece окремо
pip install sentencepiece

# Якщо не вдається, використайте conda
conda install -c conda-forge sentencepiece
```

### Крок 4: Встановлення решти залежностей
```bash
pip install language-tool-python
pip install openai-whisper
pip install ffmpeg-python
pip install deepl
pip install langdetect
pip install pyspellchecker
pip install requests
```

## Альтернативний requirements.txt

Створіть новий файл `requirements_safe.txt`:

```
# Основні залежності з фіксованими версіями
torch>=2.0.0
torchaudio>=2.0.0
transformers>=4.21.0
sentencepiece>=0.1.97

# Інші залежності
language-tool-python>=2.7.1
openai-whisper>=20230314
ffmpeg-python>=0.2.0
deepl>=1.12.0
langdetect>=1.0.9
pyspellchecker>=0.7.2
requests>=2.28.0
```

Потім встановіть:
```bash
pip install -r requirements_safe.txt
```

## Якщо нічого не допомагає

1. **Використайте Anaconda/Miniconda:**
```bash
conda create -n magi_env python=3.9
conda activate magi_env
conda install pytorch torchaudio cpuonly -c pytorch
conda install transformers -c huggingface
conda install sentencepiece -c conda-forge
pip install openai-whisper language-tool-python ffmpeg-python deepl langdetect pyspellchecker requests
```

2. **Встановіть Docker-версію** (якщо буде створена)

3. **Звертайтеся за допомогою** з повним логом помилки

## Проблеми після установки

### IndentationError при запуску
**Проблема:** `IndentationError: unindent does not match any outer indentation level`

**Рішення:**
Це означає, що ваш редактор змінив відступи в Python файлах. Завантажте найновішу версію з GitHub або виконайте:
```bash
git pull origin main
```

### Інші помилки запуску
Якщо виникають інші помилки при виконанні `python scripts/run_pipeline.py`, створіть issue на GitHub з повним текстом помилки.

## Перевірка установки

Після успішної установки перевірте:
```python
import torch
import transformers
import sentencepiece
import whisper
print("Всі модулі встановлені успішно!")
```