from magi_pipeline.translate.deepl_translate import deepl_translate

class Melchior:
    @staticmethod
    def translate(text, engine="helsinki", api_key=None, source_lang="ru", target_lang="uk"):
        """
        Переклад тексту з вибором движка
        
        Args:
            text (str): Текст для перекладу
            engine (str): "helsinki" (безкоштовно) або "deepl" (API ключ)
            api_key (str): API ключ для DeepL (якщо потрібен)
            source_lang (str): Вихідна мова
            target_lang (str): Цільова мова
        
        Returns:
            str: Перекладений текст
        """
        if not text.strip():
            return ""
            
        if engine == "helsinki":
            try:
                from magi_pipeline.translate.translate import translate_line
                return translate_line(text)
            except ImportError:
                raise Exception("Helsinki-NLP модель не встановлена! Встановіть transformers та завантажте модель.")
        
        elif engine == "deepl":
            if api_key:
                # Тимчасово встановлюємо API ключ
                import magi_pipeline.translate.deepl_translate as deepl_module
                original_key = deepl_module.DEEPL_API_KEY
                deepl_module.DEEPL_API_KEY = api_key
                try:
                    translated = deepl_translate(text, source_lang=source_lang, target_lang=target_lang.upper())
                    return translated
                finally:
                    # Повертаємо оригінальний ключ
                    deepl_module.DEEPL_API_KEY = original_key
            else:
                translated = deepl_translate(text, source_lang=source_lang, target_lang=target_lang.upper())
                return translated
        
        else:
            raise ValueError(f"Непідтримуваний движок перекладу: {engine}. Використовуйте 'helsinki' або 'deepl'.") 