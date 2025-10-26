"""
Melchior - модуль перекладу з підтримкою різних движків
Оновлено для використання нової API системи
"""

import logging
from typing import Optional, List

try:
    from ..api.translation_api import create_translation_api, TranslationEngine
except ImportError:
    # Fallback для випадку коли залежності не встановлені
    create_translation_api = None
    TranslationEngine = None
from ..config import get_config

logger = logging.getLogger(__name__)


class Melchior:
    """Клас для перекладу тексту з підтримкою різних движків"""
    
    def __init__(self):
        self.translation_api = create_translation_api()
        self.config = get_config()
    
    @staticmethod
    def translate(
        text: str, 
        engine: str = "auto", 
        api_key: Optional[str] = None, 
        source_lang: str = "ru", 
        target_lang: str = "uk"
    ) -> str:
        """
        Переклад тексту з вибором движка
        
        Args:
            text: Текст для перекладу
            engine: "helsinki", "deepl", або "auto" (автоматичний вибір)
            api_key: API ключ для DeepL (застарілий параметр)
            source_lang: Вихідна мова
            target_lang: Цільова мова
        
        Returns:
            Перекладений текст
        
        Raises:
            ValueError: При невідомому движку або недоступності API
            RuntimeError: При помилці перекладу
        """
        if not text.strip():
            return ""
        
        # Попередження про застарілий параметр api_key
        if api_key:
            logger.warning(
                "Параметр api_key застарів. "
                "Встановіть DEEPL_API_KEY у змінних середовища або .env файлі"
            )
        
        # Створюємо екземпляр API
        if create_translation_api is None:
            raise ImportError("Translation API недоступний. Встановіть залежності: pip install -r requirements.txt")
        
        translation_api = create_translation_api()
        
        # Мапінг старих назв движків на нові
        engine_mapping = {
            "helsinki": TranslationEngine.HELSINKI,
            "deepl": TranslationEngine.DEEPL,
            "auto": TranslationEngine.AUTO
        }
        
        if engine not in engine_mapping:
            available_engines = list(engine_mapping.keys())
            raise ValueError(
                f"Непідтримуваний движок перекладу: {engine}. "
                f"Доступні: {', '.join(available_engines)}"
            )
        
        try:
            result = translation_api.translate_text(
                text=text,
                engine=engine_mapping[engine],
                source_lang=source_lang,
                target_lang=target_lang
            )
            
            if result is None:
                raise RuntimeError(f"Помилка перекладу з движком {engine}")
            
            return result
            
        except Exception as e:
            logger.error(f"Помилка перекладу: {e}")
            raise
    
    @staticmethod
    def translate_batch(
        texts: List[str], 
        engine: str = "auto", 
        source_lang: str = "ru", 
        target_lang: str = "uk",
        batch_size: int = 10
    ) -> List[str]:
        """
        Переклад списку текстів
        
        Args:
            texts: Список текстів для перекладу
            engine: Движок перекладу
            source_lang: Вихідна мова
            target_lang: Цільова мова
            batch_size: Розмір батчу
            
        Returns:
            Список перекладених текстів
        """
        if not texts:
            return []
        
        translation_api = create_translation_api()
        
        # Мапінг движків
        engine_mapping = {
            "helsinki": TranslationEngine.HELSINKI,
            "deepl": TranslationEngine.DEEPL,
            "auto": TranslationEngine.AUTO
        }
        
        if engine not in engine_mapping:
            raise ValueError(f"Непідтримуваний движок: {engine}")
        
        try:
            results = translation_api.translate_batch(
                texts=texts,
                engine=engine_mapping[engine],
                source_lang=source_lang,
                target_lang=target_lang,
                batch_size=batch_size
            )
            
            # Конвертуємо None в порожні рядки для зворотної сумісності
            return [result or "" for result in results]
            
        except Exception as e:
            logger.error(f"Помилка batch перекладу: {e}")
            raise
    
    @staticmethod
    def get_available_engines() -> List[str]:
        """
        Повертає список доступних движків перекладу
        
        Returns:
            Список назв движків
        """
        if create_translation_api is None:
            return ["helsinki"]  # Базовий движок завжди доступний
        
        try:
            translation_api = create_translation_api()
            return translation_api.get_available_engines()
        except Exception:
            return ["helsinki"]
    
    @staticmethod
    def test_engines() -> dict:
        """
        Тестує всі доступні движки
        
        Returns:
            Результати тестування
        """
        from ..api.translation_api import test_translation_engines
        return test_translation_engines()


# Функції для зворотної сумісності
def translate_text(text: str, engine: str = "auto", **kwargs) -> str:
    """Функція-обгортка для зворотної сумісності"""
    return Melchior.translate(text, engine, **kwargs)


def get_translation_info() -> dict:
    """Отримує інформацію про систему перекладу"""
    translation_api = create_translation_api()
    return translation_api.get_engine_info() 