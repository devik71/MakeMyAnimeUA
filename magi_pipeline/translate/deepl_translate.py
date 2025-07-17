import deepl
import os

DEEPL_API_KEY = "427c0788-2c8d-494c-84b8-403e7c7baa08:fx"  # Зручно зберігати ключ у змінній середовища

def deepl_translate(text, target_lang="UK", source_lang=None):
    if not DEEPL_API_KEY:
        raise ValueError("DEEPL_API_KEY is not set in environment variables!")
    translator = deepl.Translator(DEEPL_API_KEY)
    kwargs = {"target_lang": target_lang}
    if source_lang:
        # DeepL очікує коди мов: 'RU' для російської, 'EN' для англійської
        if source_lang == "ru":
            kwargs["source_lang"] = "RU"
        elif source_lang == "en":
            kwargs["source_lang"] = "EN"
    result = translator.translate_text(text, **kwargs)
    return result.text