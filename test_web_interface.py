#!/usr/bin/env python3
"""
🧪 Тест веб-інтерфейсу головного пайплайну
"""

import requests
import time

def test_web_interface():
    """Перевіряє чи працює веб-інтерфейс"""
    base_url = "http://localhost:5001"
    
    try:
        # Тест головної сторінки
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ Головна сторінка завантажується")
            
            # Перевіряємо наявність ключових елементів
            content = response.text
            checks = [
                ("🎬 MakeMyAnimeUA", "Заголовок"),
                ("uploadArea", "Зона завантаження"),
                ("stepUpload", "Крок завантаження"),
                ("stepAnalysis", "Крок аналізу"),
                ("stepConfig", "Крок конфігурації"),
                ("translation_engine", "Вибір движка перекладу"),
                ("whisper_model", "Модель Whisper"),
                ("subtitle_style", "Стиль субтитрів")
            ]
            
            for check, description in checks:
                if check in content:
                    print(f"✅ {description} присутній")
                else:
                    print(f"❌ {description} відсутній")
        else:
            print(f"❌ Помилка HTTP: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Сервер не відповідає. Запустіть main_pipeline_web.py")
    except Exception as e:
        print(f"❌ Помилка: {e}")

def test_static_files():
    """Перевіряє статичні файли"""
    base_url = "http://localhost:5001"
    static_files = [
        "/static/js/pipeline.js"
    ]
    
    for file_path in static_files:
        try:
            response = requests.get(base_url + file_path, timeout=5)
            if response.status_code == 200:
                print(f"✅ {file_path} завантажується")
            else:
                print(f"❌ {file_path} не знайдено ({response.status_code})")
        except Exception as e:
            print(f"❌ Помилка завантаження {file_path}: {e}")

if __name__ == "__main__":
    print("🧪 Тестування веб-інтерфейсу пайплайну...")
    print("=" * 50)
    
    test_web_interface()
    print()
    test_static_files()
    
    print("\n🔗 Відкрийте у браузері: http://localhost:5001")
    print("📋 Для зупинки сервера натисніть Ctrl+C у терміналі з main_pipeline_web.py")