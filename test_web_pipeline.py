#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки роботи веб-інтерфейсу з термінальним пайплайном
"""

import json
import subprocess
import sys
from pathlib import Path

def test_pipeline_integration():
    """Тестує інтеграцію веб-інтерфейсу з термінальним пайплайном"""
    
    print("🧪 Тестування інтеграції веб-інтерфейсу з термінальним пайплайном")
    
    # Створюємо тестовий конфіг
    test_config = {
        "session_id": "test_session_123",
        "video_path": "input/test_video.mp4",  # Припускаємо, що файл існує
        "output_dir": "output",
        "temp_dir": "temp_audio",
        "translation_engine": "helsinki",
        "source_language": "ru",
        "target_language": "uk",
        "whisper_model": "base",
        "use_gpu": False,  # Використовуємо CPU для тесту
        "subtitle_style": "magi_pipeline/ass_generator_module/styles/Dialogue.ass",
        "source_type": "transcribe",
        "web_interface": True
    }
    
    # Зберігаємо конфіг
    config_path = Path("temp_audio/test_config.json")
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(test_config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Конфіг створено: {config_path}")
    
    # Тестуємо запуск пайплайну з аргументами
    try:
        cmd = [
            sys.executable,
            "scripts/run_pipeline.py",
            "--config", str(config_path),
            "--session", "test_session_123",
            "--status", "temp_audio/test_status.json"
        ]
        
        print(f"🚀 Запуск команди: {' '.join(cmd)}")
        
        # Запускаємо пайплайн (без очікування завершення для тесту)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Чекаємо трохи, щоб побачити початкові повідомлення
        import time
        time.sleep(3)
        
        # Перевіряємо чи процес ще працює
        if process.poll() is None:
            print("✅ Пайплайн запущено успішно")
            
            # Перевіряємо статус-файл
            status_path = Path("temp_audio/test_status.json")
            if status_path.exists():
                with open(status_path, 'r', encoding='utf-8') as f:
                    status = json.load(f)
                print(f"📊 Статус: {status}")
            else:
                print("⚠️ Статус-файл ще не створено")
            
            # Зупиняємо процес для тесту
            process.terminate()
            process.wait(timeout=5)
            print("🛑 Пайплайн зупинено (тест)")
            
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Пайплайн завершився з помилкою:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            
    except Exception as e:
        print(f"❌ Помилка запуску: {e}")
    
    # Очищаємо тестові файли
    try:
        if config_path.exists():
            config_path.unlink()
        status_path = Path("temp_audio/test_status.json")
        if status_path.exists():
            status_path.unlink()
        print("🧹 Тестові файли очищено")
    except Exception as e:
        print(f"⚠️ Помилка очищення: {e}")

def test_helsinki_import():
    """Тестує імпорт Helsinki-NLP"""
    print("\n🧪 Тестування імпорту Helsinki-NLP")
    
    try:
        from magi_pipeline.translate.translate import translate_line
        print("✅ Модуль translate імпортовано успішно")
        
        # Тестуємо простий переклад
        test_text = "Привет, мир!"
        try:
            result = translate_line(test_text)
            print(f"✅ Тестовий переклад: '{test_text}' -> '{result}'")
        except Exception as e:
            print(f"⚠️ Помилка перекладу: {e}")
            
    except ImportError as e:
        print(f"❌ Помилка імпорту: {e}")
    except Exception as e:
        print(f"❌ Неочікувана помилка: {e}")

if __name__ == "__main__":
    print("🎬 MakeMyAnimeUA - Тестування інтеграції")
    print("=" * 50)
    
    test_helsinki_import()
    test_pipeline_integration()
    
    print("\n✅ Тестування завершено!") 