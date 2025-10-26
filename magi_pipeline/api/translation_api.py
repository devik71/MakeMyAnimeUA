"""
Загальний API модуль для перекладу
Об'єднує різні движки перекладу
"""

import logging
from typing import Optional, List, Dict, Any, Union
from enum import Enum

from .deepl_api import DeepLAPI
from ..config import get_config

logger = logging.getLogger(__name__)


class TranslationEngine(Enum):
    """Доступні движки перекладу"""
    DEEPL = "deepl"
    HELSINKI = "helsinki"
    AUTO = "auto"  # Автоматичний вибір


class TranslationAPI:
    """Головний клас для роботи з перекладом"""
    
    def __init__(self):
        self.config = get_config()
        self._deepl_api = None
        self._helsinki_model = None
        self._helsinki_tokenizer = None
    
    @property
    def deepl_api(self) -> Optional[DeepLAPI]:
        """Ліниво ініціалізує DeepL API"""
        if self._deepl_api is None and self.config.deepl_api_key:
            self._deepl_api = DeepLAPI()
        return self._deepl_api
    
    def _init_helsinki_model(self):
        """Ініціалізує Helsinki-NLP модель"""
        if self._helsinki_model is None:
            try:
                from transformers import MarianMTModel, MarianTokenizer
                import torch
                
                model_name = "Helsinki-NLP/opus-mt-ru-uk"
                
                logger.info(f"Завантаження Helsinki-NLP моделі: {model_name}")
                self._helsinki_tokenizer = MarianTokenizer.from_pretrained(model_name)
                self._helsinki_model = MarianMTModel.from_pretrained(model_name)
                
                # Автоматичний вибір пристрою
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                self._helsinki_model.to(device)
                
                logger.info(f"Helsinki-NLP модель завантажена на {device}")
                
            except ImportError as e:
                logger.error(f"Не вдалося імпортувати transformers: {e}")
                raise ImportError("Для Helsinki-NLP потрібно встановити transformers: pip install transformers")
            except Exception as e:
                logger.error(f"Помилка завантаження Helsinki-NLP моделі: {e}")
                raise
    
    def get_available_engines(self) -> List[str]:
        """
        Повертає список доступних движків перекладу
        
        Returns:
            Список назв движків
        """
        engines = []
        
        # Перевіряємо DeepL
        if self.deepl_api and self.deepl_api.is_available():
            engines.append(TranslationEngine.DEEPL.value)
        
        # Перевіряємо Helsinki-NLP
        try:
            import transformers
            engines.append(TranslationEngine.HELSINKI.value)
        except ImportError:
            pass
        
        return engines
    
    def choose_best_engine(self, text_length: int = 0) -> TranslationEngine:
        """
        Автоматично вибирає найкращий движок для перекладу
        
        Args:
            text_length: Довжина тексту для перекладу
            
        Returns:
            Рекомендований движок
        """
        available = self.get_available_engines()
        
        # Якщо доступний DeepL і текст не дуже великий
        if (TranslationEngine.DEEPL.value in available and 
            text_length < 10000):  # DeepL має ліміти
            return TranslationEngine.DEEPL
        
        # Інакше використовуємо Helsinki-NLP
        if TranslationEngine.HELSINKI.value in available:
            return TranslationEngine.HELSINKI
        
        # Якщо нічого не доступно
        raise RuntimeError("Жоден движок перекладу недоступний")
    
    def translate_with_helsinki(
        self, 
        text: str, 
        source_lang: str = "ru", 
        target_lang: str = "uk"
    ) -> Optional[str]:
        """
        Перекладає текст за допомогою Helsinki-NLP
        
        Args:
            text: Текст для перекладу
            source_lang: Вихідна мова
            target_lang: Цільова мова
            
        Returns:
            Перекладений текст або None при помилці
        """
        if not text.strip():
            return ""
        
        try:
            # Ініціалізуємо модель якщо потрібно
            if self._helsinki_model is None:
                self._init_helsinki_model()
            
            import torch
            device = next(self._helsinki_model.parameters()).device
            
            # Токенізуємо текст
            inputs = self._helsinki_tokenizer(
                text, 
                return_tensors="pt", 
                padding=True, 
                truncation=True,
                max_length=512
            ).to(device)
            
            # Генеруємо переклад
            with torch.no_grad():
                translated = self._helsinki_model.generate(**inputs, max_length=512)
            
            # Декодуємо результат
            output = self._helsinki_tokenizer.decode(translated[0], skip_special_tokens=True)
            
            logger.debug(f"Helsinki переклад: '{text[:50]}...' -> '{output[:50]}...'")
            return output
            
        except Exception as e:
            logger.error(f"Помилка Helsinki перекладу: {e}")
            return None
    
    def translate_text(
        self, 
        text: str, 
        engine: Union[str, TranslationEngine] = TranslationEngine.AUTO,
        source_lang: str = "ru",
        target_lang: str = "uk",
        **kwargs
    ) -> Optional[str]:
        """
        Перекладає текст використовуючи вказаний движок
        
        Args:
            text: Текст для перекладу
            engine: Движок перекладу
            source_lang: Вихідна мова
            target_lang: Цільова мова
            **kwargs: Додаткові параметри
            
        Returns:
            Перекладений текст або None при помилці
        """
        if not text.strip():
            return ""
        
        # Конвертуємо рядок в enum
        if isinstance(engine, str):
            try:
                engine = TranslationEngine(engine)
            except ValueError:
                logger.warning(f"Невідомий движок '{engine}', використовується AUTO")
                engine = TranslationEngine.AUTO
        
        # Автоматичний вибір движка
        if engine == TranslationEngine.AUTO:
            engine = self.choose_best_engine(len(text))
        
        # Перекладаємо відповідним движком
        if engine == TranslationEngine.DEEPL:
            if self.deepl_api and self.deepl_api.is_available():
                # Конвертуємо коди мов для DeepL
                deepl_target = target_lang.upper()
                deepl_source = source_lang.lower() if source_lang else None
                
                return self.deepl_api.translate_text(
                    text, 
                    target_lang=deepl_target,
                    source_lang=deepl_source,
                    **kwargs
                )
            else:
                logger.warning("DeepL недоступний, переключаюсь на Helsinki")
                engine = TranslationEngine.HELSINKI
        
        if engine == TranslationEngine.HELSINKI:
            return self.translate_with_helsinki(text, source_lang, target_lang)
        
        logger.error(f"Не вдалося перекласти текст движком {engine}")
        return None
    
    def translate_batch(
        self, 
        texts: List[str], 
        engine: Union[str, TranslationEngine] = TranslationEngine.AUTO,
        source_lang: str = "ru",
        target_lang: str = "uk",
        batch_size: int = 10,
        **kwargs
    ) -> List[Optional[str]]:
        """
        Перекладає список текстів
        
        Args:
            texts: Список текстів
            engine: Движок перекладу
            source_lang: Вихідна мова
            target_lang: Цільова мова
            batch_size: Розмір батчу
            **kwargs: Додаткові параметри
            
        Returns:
            Список перекладених текстів
        """
        if not texts:
            return []
        
        # Конвертуємо рядок в enum
        if isinstance(engine, str):
            try:
                engine = TranslationEngine(engine)
            except ValueError:
                engine = TranslationEngine.AUTO
        
        # Автоматичний вибір движка
        if engine == TranslationEngine.AUTO:
            total_length = sum(len(text) for text in texts)
            engine = self.choose_best_engine(total_length)
        
        # Batch переклад для DeepL
        if engine == TranslationEngine.DEEPL and self.deepl_api and self.deepl_api.is_available():
            deepl_target = target_lang.upper()
            deepl_source = source_lang.lower() if source_lang else None
            
            return self.deepl_api.translate_batch(
                texts,
                target_lang=deepl_target,
                source_lang=deepl_source,
                **kwargs
            )
        
        # Послідовний переклад для Helsinki або якщо DeepL недоступний
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = []
            
            for text in batch:
                result = self.translate_text(
                    text, 
                    engine=engine,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    **kwargs
                )
                batch_results.append(result)
            
            results.extend(batch_results)
            
            # Логування прогресу
            if len(texts) > batch_size:
                progress = min(i + batch_size, len(texts))
                logger.info(f"Переклад прогрес: {progress}/{len(texts)}")
        
        return results
    
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Повертає інформацію про доступні движки
        
        Returns:
            Словник з інформацією про движки
        """
        info = {
            'available_engines': self.get_available_engines(),
            'deepl': {
                'available': False,
                'usage': None
            },
            'helsinki': {
                'available': False,
                'model_loaded': self._helsinki_model is not None
            }
        }
        
        # Інформація про DeepL
        if self.deepl_api and self.deepl_api.is_available():
            info['deepl']['available'] = True
            info['deepl']['usage'] = self.deepl_api.get_usage_info()
        
        # Інформація про Helsinki
        try:
            import transformers
            info['helsinki']['available'] = True
        except ImportError:
            pass
        
        return info


def create_translation_api() -> TranslationAPI:
    """
    Фабрична функція для створення Translation API
    
    Returns:
        Екземпляр TranslationAPI
    """
    return TranslationAPI()


def test_translation_engines() -> Dict[str, Any]:
    """
    Тестує всі доступні движки перекладу
    
    Returns:
        Результати тестування
    """
    api = create_translation_api()
    test_text = "Привіт, світ!"
    
    results = {
        'engines_info': api.get_engine_info(),
        'test_results': {}
    }
    
    # Тестуємо кожен доступний движок
    for engine in api.get_available_engines():
        try:
            translated = api.translate_text(test_text, engine=engine)
            results['test_results'][engine] = {
                'success': translated is not None,
                'result': translated,
                'error': None
            }
        except Exception as e:
            results['test_results'][engine] = {
                'success': False,
                'result': None,
                'error': str(e)
            }
    
    return results