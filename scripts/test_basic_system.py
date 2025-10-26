#!/usr/bin/env python3
"""
Базове тестування нової API системи без зовнішніх залежностей
"""

import sys
import os
from pathlib import Path

# Додаємо шлях до проекту
sys.path.append(str(Path(__file__).parent.parent))

def test_imports():
    """Тестує імпорти основних модулів"""
    print("📦 Тестування імпортів...")
    
    try:
        from magi_pipeline.config import get_config, setup_logging
        print("  ✅ Config модуль імпортовано")
        
        config = get_config()
        print(f"  ✅ Конфігурація створена: {type(config)}")
        
        return True
    except Exception as e:
        print(f"  ❌ Помилка імпорту: {e}")
        return False

def test_config_basic():
    """Тестує базову конфігурацію"""
    print("\n🔧 Тестування базової конфігурації...")
    
    try:
        from magi_pipeline.config import get_config
        config = get_config()
        
        # Перевіряємо основні властивості
        print(f"  ✓ Debug режим: {config.debug_mode}")
        print(f"  ✓ Хост: {config.host}")
        print(f"  ✓ Порт: {config.port}")
        print(f"  ✓ Upload папка: {config.upload_folder}")
        print(f"  ✓ Output папка: {config.output_folder}")
        
        # Перевіряємо Flask secret key
        secret_key = config.flask_secret_key
        print(f"  ✓ Flask secret key: {'встановлено' if secret_key else 'НЕ ВСТАНОВЛЕНО'}")
        
        return True
    except Exception as e:
        print(f"  ❌ Помилка конфігурації: {e}")
        return False

def test_logging_basic():
    """Тестує базове логування"""
    print("\n📝 Тестування базового логування...")
    
    try:
        from magi_pipeline.config import setup_logging
        
        logger = setup_logging()
        print(f"  ✅ Logger створено: {type(logger)}")
        
        # Тестуємо запис логів
        logger.info("Тестове повідомлення")
        print("  ✅ Тестове повідомлення записано")
        
        # Перевіряємо папку логів
        log_dir = Path('logs')
        if log_dir.exists():
            print(f"  ✅ Папка логів створена: {log_dir}")
        else:
            print("  ⚠️ Папка логів не створена (можливо, немає прав)")
        
        return True
    except Exception as e:
        print(f"  ❌ Помилка логування: {e}")
        return False

def test_melchior_import():
    """Тестує імпорт оновленого Melchior"""
    print("\n🧙 Тестування Melchior...")
    
    try:
        from magi_pipeline.utils.melchior import Melchior
        print("  ✅ Melchior імпортовано")
        
        # Тестуємо метод отримання доступних движків
        try:
            engines = Melchior.get_available_engines()
            print(f"  ✅ Доступні движки: {engines}")
        except Exception as e:
            print(f"  ⚠️ Помилка отримання движків: {e}")
        
        return True
    except Exception as e:
        print(f"  ❌ Помилка імпорту Melchior: {e}")
        return False

def test_file_structure():
    """Перевіряє структуру файлів"""
    print("\n📁 Перевірка структури файлів...")
    
    required_files = [
        "magi_pipeline/config.py",
        "magi_pipeline/api/__init__.py", 
        "magi_pipeline/api/deepl_api.py",
        "magi_pipeline/api/translation_api.py",
        ".env.template",
        "API_MIGRATION_GUIDE.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - НЕ ЗНАЙДЕНО")
            all_exist = False
    
    return all_exist

def main():
    """Головна функція тестування"""
    print("🧪 Базове тестування нової API системи MakeMyAnimeUA")
    print("=" * 60)
    
    tests = [
        ("Імпорти модулів", test_imports),
        ("Базова конфігурація", test_config_basic),
        ("Базове логування", test_logging_basic),
        ("Melchior модуль", test_melchior_import),
        ("Структура файлів", test_file_structure),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Критична помилка в тесті '{test_name}': {e}")
            results[test_name] = False
    
    # Підсумки
    print("\n" + "=" * 60)
    print("📊 ПІДСУМКИ БАЗОВОГО ТЕСТУВАННЯ")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕНО" if result else "❌ НЕ ПРОЙДЕНО"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Пройдено: {passed}/{total} тестів ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 Всі базові тести пройдено успішно!")
        print("💡 Для повного тестування встановіть залежності:")
        print("   pip install -r requirements.txt")
        print("   python3 scripts/test_api_system.py")
        return 0
    else:
        print("⚠️ Деякі базові тести не пройдено.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)