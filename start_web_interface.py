#!/usr/bin/env python3
"""
Скрипт для запуску веб-інтерфейсу MakeMyAnimeUA
"""

import os
import sys
from pathlib import Path

def main():
    print("🎬 MakeMyAnimeUA - Запуск веб-інтерфейсу")
    print("=" * 50)
    
    # Перевіряємо чи існує основний файл
    web_file = Path("main_pipeline_web.py")
    if not web_file.exists():
        print("❌ Файл main_pipeline_web.py не знайдено!")
        print("Переконайтеся, що ви знаходитесь у правильній директорії.")
        return
    
    # Створюємо необхідні директорії
    directories = ["temp_audio", "output", "input"]
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Директорія {dir_name}/ готова")
    
    # Перевіряємо залежності
    print("\n🔍 Перевірка залежностей...")
    
    try:
        import flask
        print("✅ Flask встановлено")
    except ImportError:
        print("❌ Flask не встановлено! Встановіть: pip install flask")
        return
    
    try:
        from transformers import MarianMTModel
        print("✅ Transformers встановлено")
    except ImportError:
        print("❌ Transformers не встановлено! Встановіть: pip install transformers")
        return
    
    try:
        import torch
        print("✅ PyTorch встановлено")
    except ImportError:
        print("❌ PyTorch не встановлено! Встановіть: pip install torch")
        return
    
    # Запускаємо веб-інтерфейс
    print("\n🚀 Запуск веб-інтерфейсу...")
    print("📍 Веб-інтерфейс буде доступний за адресою: http://localhost:5001")
    print("🛑 Для зупинки натисніть Ctrl+C")
    print("-" * 50)
    
    try:
        # Імпортуємо та запускаємо Flask додаток
        from main_pipeline_web import app
        
        # Запускаємо з правильними налаштуваннями
        app.run(
            debug=True,
            port=5001,
            host='0.0.0.0',
            use_reloader=False  # Вимикаємо автоперезавантаження для уникнення проблем
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Веб-інтерфейс зупинено користувачем")
    except Exception as e:
        print(f"\n❌ Помилка запуску: {e}")
        print("Спробуйте запустити вручну: python main_pipeline_web.py")

if __name__ == "__main__":
    main() 