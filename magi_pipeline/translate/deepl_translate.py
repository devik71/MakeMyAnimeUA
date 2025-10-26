"""
ЗАСТАРІЛИЙ МОДУЛЬ - використовуйте magi_pipeline.api.deepl_api
Цей файл залишено для зворотної сумісності
"""

import logging
import warnings
from typing import Optional

from ..api.deepl_api import create_deepl_api

logger = logging.getLogger(__name__)

# Попередження про застарілість
warnings.warn(
    "magi_pipeline.translate.deepl_translate застарів. "
    "Використовуйте magi_pipeline.api.deepl_api",
    DeprecationWarning,
    stacklevel=2
)


def deepl_translate(text: str, target_lang: str = "UK", source_lang: Optional[str] = None) -> str:
    """
    ЗАСТАРІЛА ФУНКЦІЯ - використовуйте DeepLAPI.translate_text()
    
    Args:
        text: Текст для перекладу
        target_lang: Цільова мова
        source_lang: Вихідна мова
        
    Returns:
        Перекладений текст
        
    Raises:
        ValueError: Якщо API недоступний
    """
    logger.warning("Використовується застаріла функція deepl_translate()")
    
    deepl_api = create_deepl_api()
    
    if not deepl_api.is_available():
        raise ValueError("DeepL API недоступний! Встановіть DEEPL_API_KEY у змінних середовища.")
    
    result = deepl_api.translate_text(
        text=text,
        target_lang=target_lang,
        source_lang=source_lang
    )
    
    if result is None:
        raise RuntimeError("Помилка перекладу DeepL")
    
    return result


# Для зворотної сумісності
DEEPL_API_KEY = None  # Більше не використовуєтьсяeturn result.text