"""
DeepL API модуль для перекладу
Окремі функції для роботи з DeepL API
"""

import deepl
import logging
from typing import Optional, List, Dict, Any
from ..config import get_config, validate_api_key

logger = logging.getLogger(__name__)


class DeepLAPI:
    """Клас для роботи з DeepL API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Ініціалізація DeepL API
        
        Args:
            api_key: API ключ DeepL. Якщо не вказано, береться з конфігурації
        """
        self.config = get_config()
        self.api_key = api_key or self.config.deepl_api_key
        self._translator = None
        
        if self.api_key and not validate_api_key(self.api_key, 'deepl'):
            logger.warning("Невалідний формат DeepL API ключа")
            self.api_key = None
    
    @property
    def translator(self) -> Optional[deepl.Translator]:
        """Ліниво ініціалізує DeepL translator"""
        if not self.api_key:
            return None
            
        if self._translator is None:
            try:
                self._translator = deepl.Translator(self.api_key)
                logger.info("DeepL translator ініціалізовано успішно")
            except Exception as e:
                logger.error(f"Помилка ініціалізації DeepL: {e}")
                return None
        
        return self._translator
    
    def is_available(self) -> bool:
        """Перевіряє чи доступний DeepL API"""
        return self.translator is not None
    
    def get_usage_info(self) -> Optional[Dict[str, Any]]:
        """
        Отримує інформацію про використання API
        
        Returns:
            Dict з інформацією про використання або None при помилці
        """
        if not self.translator:
            return None
            
        try:
            usage = self.translator.get_usage()
            return {
                'character_count': usage.character.count,
                'character_limit': usage.character.limit,
                'character_usage_percent': (usage.character.count / usage.character.limit * 100) if usage.character.limit else 0
            }
        except Exception as e:
            logger.error(f"Помилка отримання інформації про використання DeepL: {e}")
            return None
    
    def get_supported_languages(self) -> Optional[List[Dict[str, str]]]:
        """
        Отримує список підтримуваних мов
        
        Returns:
            List мов або None при помилці
        """
        if not self.translator:
            return None
            
        try:
            source_langs = self.translator.get_source_languages()
            target_langs = self.translator.get_target_languages()
            
            return {
                'source': [{'code': lang.code, 'name': lang.name} for lang in source_langs],
                'target': [{'code': lang.code, 'name': lang.name} for lang in target_langs]
            }
        except Exception as e:
            logger.error(f"Помилка отримання підтримуваних мов DeepL: {e}")
            return None
    
    def translate_text(
        self, 
        text: str, 
        target_lang: str = "UK", 
        source_lang: Optional[str] = None,
        preserve_formatting: bool = True
    ) -> Optional[str]:
        """
        Перекладає текст за допомогою DeepL
        
        Args:
            text: Текст для перекладу
            target_lang: Цільова мова (код DeepL)
            source_lang: Вихідна мова (автовизначення якщо None)
            preserve_formatting: Зберігати форматування
            
        Returns:
            Перекладений текст або None при помилці
        """
        if not text.strip():
            return ""
            
        if not self.translator:
            logger.error("DeepL translator недоступний")
            return None
        
        try:
            kwargs = {
                "target_lang": target_lang,
                "preserve_formatting": preserve_formatting
            }
            
            if source_lang:
                # Конвертуємо коди мов у формат DeepL
                source_lang_map = {
                    "ru": "RU",
                    "en": "EN", 
                    "uk": "UK",
                    "ja": "JA",
                    "de": "DE",
                    "fr": "FR"
                }
                kwargs["source_lang"] = source_lang_map.get(source_lang.lower(), source_lang.upper())
            
            result = self.translator.translate_text(text, **kwargs)
            
            logger.debug(f"Переклад успішний: '{text[:50]}...' -> '{result.text[:50]}...'")
            return result.text
            
        except deepl.DeepLException as e:
            logger.error(f"Помилка DeepL API: {e}")
            return None
        except Exception as e:
            logger.error(f"Несподівана помилка при перекладі: {e}")
            return None
    
    def translate_batch(
        self, 
        texts: List[str], 
        target_lang: str = "UK", 
        source_lang: Optional[str] = None,
        preserve_formatting: bool = True
    ) -> List[Optional[str]]:
        """
        Перекладає список текстів
        
        Args:
            texts: Список текстів для перекладу
            target_lang: Цільова мова
            source_lang: Вихідна мова
            preserve_formatting: Зберігати форматування
            
        Returns:
            Список перекладених текстів
        """
        if not self.translator:
            logger.error("DeepL translator недоступний")
            return [None] * len(texts)
        
        # Фільтруємо порожні тексти
        non_empty_texts = [(i, text) for i, text in enumerate(texts) if text.strip()]
        
        if not non_empty_texts:
            return [""] * len(texts)
        
        try:
            kwargs = {
                "target_lang": target_lang,
                "preserve_formatting": preserve_formatting
            }
            
            if source_lang:
                source_lang_map = {
                    "ru": "RU",
                    "en": "EN", 
                    "uk": "UK",
                    "ja": "JA",
                    "de": "DE",
                    "fr": "FR"
                }
                kwargs["source_lang"] = source_lang_map.get(source_lang.lower(), source_lang.upper())
            
            # Перекладаємо тільки непорожні тексти
            batch_texts = [text for _, text in non_empty_texts]
            results = self.translator.translate_text(batch_texts, **kwargs)
            
            # Відновлюємо порядок результатів
            translated = [""] * len(texts)
            for (original_index, _), result in zip(non_empty_texts, results):
                translated[original_index] = result.text
            
            logger.info(f"Batch переклад завершено: {len(batch_texts)} текстів")
            return translated
            
        except deepl.DeepLException as e:
            logger.error(f"Помилка DeepL API при batch перекладі: {e}")
            return [None] * len(texts)
        except Exception as e:
            logger.error(f"Несподівана помилка при batch перекладі: {e}")
            return [None] * len(texts)
    
    def check_connection(self) -> bool:
        """
        Перевіряє з'єднання з DeepL API
        
        Returns:
            True якщо з'єднання працює
        """
        if not self.translator:
            return False
            
        try:
            # Простий тест перекладу
            result = self.translator.translate_text("test", target_lang="UK")
            return result is not None
        except Exception as e:
            logger.error(f"Помилка з'єднання з DeepL: {e}")
            return False


def create_deepl_api(api_key: Optional[str] = None) -> DeepLAPI:
    """
    Фабрична функція для створення DeepL API
    
    Args:
        api_key: Опціональний API ключ
        
    Returns:
        Екземпляр DeepLAPI
    """
    return DeepLAPI(api_key)


def test_deepl_connection(api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Тестує з'єднання з DeepL API
    
    Args:
        api_key: Опціональний API ключ для тестування
        
    Returns:
        Словник з результатами тестування
    """
    deepl_api = create_deepl_api(api_key)
    
    result = {
        'available': deepl_api.is_available(),
        'connection': False,
        'usage': None,
        'languages': None,
        'test_translation': None
    }
    
    if result['available']:
        result['connection'] = deepl_api.check_connection()
        result['usage'] = deepl_api.get_usage_info()
        result['languages'] = deepl_api.get_supported_languages()
        
        # Тестовий переклад
        test_text = deepl_api.translate_text("Привіт, світ!", target_lang="EN")
        result['test_translation'] = test_text
    
    return result