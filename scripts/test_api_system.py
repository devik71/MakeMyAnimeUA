#!/usr/bin/env python3
"""
Скрипт для тестування нової API системи MakeMyAnimeUA
Перевіряє всі компоненти та їх взаємодію
"""

import sys
import os
from pathlib import Path

# Додаємо шлях до проекту
sys.path.append(str(Path(__file__).parent.parent))

from magi_pipeline.config import get_config, setup_logging
from magi_pipeline.api.deepl_api import test_deepl_connection
from magi_pipeline.api.translation_api import test_translation_engines
from magi_pipeline.utils.melchior import Melchior
import logging

def test_configuration():
    """Тестує систему конфігурації"""
    print("🔧 Тестування конфігурації...")
    
    config = get_config()
    
    # Перевіряємо основні налаштування
    print(f"  ✓ Flask Secret Key: {'встановлено' if config.flask_secret_key else 'НЕ ВСТАНОВЛЕНО'}")
    print(f"  ✓ DeepL API Key: {'встановлено' if config.deepl_api_key else 'не встановлено'}")
    print(f"  ✓ Debug режим: {config.debug_mode}")
    print(f"  ✓ Хост: {config.host}")
    print(f"  ✓ Порт: {config.port}")
    
    # Перевіряємо попередження
    warnings = config.validate_config()
    if warnings:
        print("  ⚠️ Попередження:")
        for warning_type, message in warnings.items():
            print(f"    - {warning_type}: {message}")
    else:
        print("  ✅ Конфігурація без попереджень")
    
    return len(warnings) == 0

def test_deepl_api():
    """Тестує DeepL API"""
    print("\n🌐 Тестування DeepL API...")
    
    try:
        result = test_deepl_connection()
        
        print(f"  ✓ Доступність: {result['available']}")
        
        if result['available']:
            print(f"  ✓ З'єднання: {result['connection']}")
            
            if result['usage']:
                usage = result['usage']
                print(f"  ✓ Використання: {usage['character_count']}/{usage['character_limit']} символів")
                print(f"  ✓ Використано: {usage['character_usage_percent']:.1f}%")
            
            if result['test_translation']:
                print(f"  ✓ Тестовий переклад: '{result['test_translation']}'")
        else:
            print("  ❌ DeepL API недоступний")
        
        return result['available'] and result['connection']
        
    except Exception as e:
        print(f"  ❌ Помилка тестування DeepL: {e}")
        return False

def test_translation_system():
    """Тестує систему перекладу"""
    print("\n🔄 Тестування системи перекладу...")
    
    try:
        result = test_translation_engines()
        
        print(f"  ✓ Доступні движки: {result['engines_info']['available_engines']}")
        
        # Тестуємо кожен движок
        for engine, test_result in result['test_results'].items():
            if test_result['success']:
                print(f"  ✅ {engine}: '{test_result['result']}'")
            else:
                print(f"  ❌ {engine}: {test_result['error']}")
        
        return len(result['test_results']) > 0
        
    except Exception as e:
        print(f"  ❌ Помилка тестування перекладу: {e}")
        return False

def test_melchior_compatibility():
    """Тестує зворотну сумісність Melchior"""
    print("\n🧙 Тестування Melchior (зворотна сумісність)...")
    
    test_text = "Привіт, світ!"
    
    try:
        # Тестуємо доступні движки
        available_engines = Melchior.get_available_engines()
        print(f"  ✓ Доступні движки через Melchior: {available_engines}")
        
        # Тестуємо переклад з кожним движком
        for engine in available_engines:
            try:
                result = Melchior.translate(test_text, engine=engine)
                print(f"  ✅ {engine} через Melchior: '{result}'")
            except Exception as e:
                print(f"  ❌ {engine} через Melchior: {e}")
        
        # Тестуємо автоматичний вибір
        try:
            auto_result = Melchior.translate(test_text, engine="auto")
            print(f"  ✅ auto через Melchior: '{auto_result}'")
        except Exception as e:
            print(f"  ❌ auto через Melchior: {e}")
        
        return len(available_engines) > 0
        
    except Exception as e:
        print(f"  ❌ Помилка тестування Melchior: {e}")
        return False

def test_batch_translation():
    """Тестує batch переклад"""
    print("\n📦 Тестування batch перекладу...")
    
    test_texts = [
        "Привіт!",
        "Як справи?",
        "До побачення!"
    ]
    
    try:
        results = Melchior.translate_batch(test_texts, engine="auto")
        
        print("  ✓ Результати batch перекладу:")
        for original, translated in zip(test_texts, results):
            print(f"    '{original}' -> '{translated}'")
        
        return len(results) == len(test_texts)
        
    except Exception as e:
        print(f"  ❌ Помилка batch перекладу: {e}")
        return False

def test_logging_system():
    """Тестує систему логування"""
    print("\n📝 Тестування системи логування...")
    
    try:
        logger = setup_logging()
        
        # Тестуємо різні рівні логування
        logger.debug("Тестове debug повідомлення")
        logger.info("Тестове info повідомлення")
        logger.warning("Тестове warning повідомлення")
        
        # Перевіряємо чи створюється файл логів
        log_dir = Path('logs')
        if log_dir.exists():
            log_files = list(log_dir.glob('*.log'))
            print(f"  ✓ Знайдено файлів логів: {len(log_files)}")
            if log_files:
                print(f"  ✓ Останній лог файл: {log_files[-1].name}")
        else:
            print("  ❌ Папка logs не створена")
            return False
        
        print("  ✅ Система логування працює")
        return True
        
    except Exception as e:
        print(f"  ❌ Помилка системи логування: {e}")
        return False

def main():
    """Головна функція тестування"""
    print("🧪 Тестування нової API системи MakeMyAnimeUA")
    print("=" * 60)
    
    tests = [
        ("Конфігурація", test_configuration),
        ("DeepL API", test_deepl_api),
        ("Система перекладу", test_translation_system),
        ("Melchior сумісність", test_melchior_compatibility),
        ("Batch переклад", test_batch_translation),
        ("Система логування", test_logging_system),
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
    print("📊 ПІДСУМКИ ТЕСТУВАННЯ")
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
        print("🎉 Всі тести пройдено успішно!")
        return 0
    else:
        print("⚠️ Деякі тести не пройдено. Перевірте конфігурацію.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)