"""
Модуль конфігурації для MakeMyAnimeUA
Управління API ключами та налаштуваннями
"""

import os
import secrets
from typing import Optional, Dict, Any
from pathlib import Path


class Config:
    """Клас для управління конфігурацією додатку"""
    
    def __init__(self):
        self._load_env_file()
    
    def _load_env_file(self):
        """Завантажує змінні з .env файлу якщо він існує"""
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
            except Exception as e:
                print(f"⚠️ Помилка завантаження .env файлу: {e}")
    
    @property
    def flask_secret_key(self) -> str:
        """Отримує або генерує Flask secret key"""
        key = os.getenv('FLASK_SECRET_KEY')
        if not key:
            # Генеруємо безпечний ключ
            key = secrets.token_hex(32)
            print("⚠️ FLASK_SECRET_KEY не встановлено. Використовується тимчасовий ключ.")
            print(f"💡 Додайте до .env файлу: FLASK_SECRET_KEY={key}")
        return key
    
    @property
    def deepl_api_key(self) -> Optional[str]:
        """Отримує DeepL API ключ"""
        return os.getenv('DEEPL_API_KEY')
    
    @property
    def huggingface_token(self) -> Optional[str]:
        """Отримує HuggingFace токен"""
        return os.getenv('HUGGINGFACE_TOKEN')
    
    @property
    def debug_mode(self) -> bool:
        """Режим налагодження"""
        return os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
    
    @property
    def host(self) -> str:
        """Хост для веб-сервера"""
        return os.getenv('HOST', '127.0.0.1')
    
    @property
    def port(self) -> int:
        """Порт для веб-сервера"""
        return int(os.getenv('PORT', '5001'))
    
    @property
    def max_file_size(self) -> int:
        """Максимальний розмір файлу в байтах (за замовчуванням 2GB)"""
        return int(os.getenv('MAX_FILE_SIZE', str(2 * 1024 * 1024 * 1024)))
    
    @property
    def upload_folder(self) -> str:
        """Папка для завантажених файлів"""
        return os.getenv('UPLOAD_FOLDER', 'uploads')
    
    @property
    def output_folder(self) -> str:
        """Папка для вихідних файлів"""
        return os.getenv('OUTPUT_FOLDER', 'output')
    
    @property
    def temp_audio_folder(self) -> str:
        """Папка для тимчасових аудіо файлів"""
        return os.getenv('TEMP_AUDIO_FOLDER', 'temp_audio')
    
    def get_whisper_config(self) -> Dict[str, Any]:
        """Конфігурація для Whisper"""
        return {
            'default_model': os.getenv('WHISPER_DEFAULT_MODEL', 'base'),
            'use_gpu': os.getenv('WHISPER_USE_GPU', 'True').lower() in ('true', '1', 'yes'),
            'device': os.getenv('WHISPER_DEVICE', 'auto'),  # auto, cpu, cuda
        }
    
    def get_translation_config(self) -> Dict[str, Any]:
        """Конфігурація для перекладу"""
        return {
            'default_engine': os.getenv('TRANSLATION_ENGINE', 'helsinki'),
            'source_language': os.getenv('SOURCE_LANGUAGE', 'ru'),
            'target_language': os.getenv('TARGET_LANGUAGE', 'uk'),
            'batch_size': int(os.getenv('TRANSLATION_BATCH_SIZE', '10')),
        }
    
    def validate_config(self) -> Dict[str, str]:
        """Перевіряє конфігурацію та повертає попередження"""
        warnings = {}
        
        if not self.deepl_api_key:
            warnings['deepl'] = "DeepL API ключ не встановлено. Буде використовуватись тільки Helsinki-NLP."
        
        if self.debug_mode:
            warnings['debug'] = "Режим налагодження увімкнено. Вимкніть у продакшені!"
        
        if self.host == '0.0.0.0' and not self.debug_mode:
            warnings['host'] = "Сервер доступний ззовні. Переконайтесь у безпеці!"
        
        return warnings


# Глобальний екземпляр конфігурації
config = Config()


def get_config() -> Config:
    """Отримує глобальний екземпляр конфігурації"""
    return config


def validate_api_key(api_key: str, service: str) -> bool:
    """
    Валідує API ключ для конкретного сервісу
    
    Args:
        api_key: API ключ для перевірки
        service: Назва сервісу ('deepl', 'huggingface')
    
    Returns:
        bool: True якщо ключ валідний
    """
    if not api_key:
        return False
    
    if service == 'deepl':
        # DeepL ключі мають формат: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx
        import re
        pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}:fx$'
        return bool(re.match(pattern, api_key))
    
    elif service == 'huggingface':
        # HuggingFace токени починаються з 'hf_'
        return api_key.startswith('hf_') and len(api_key) > 10
    
    return True  # Для інших сервісів базова перевірка


def setup_logging():
    """Налаштовує логування для додатку"""
    import logging
    from datetime import datetime
    
    # Створюємо папку для логів
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Налаштовуємо формат логування
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Файл для логів
    log_file = log_dir / f"magi_pipeline_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO if not config.debug_mode else logging.DEBUG,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Також виводимо в консоль
        ]
    )
    
    return logging.getLogger('magi_pipeline')