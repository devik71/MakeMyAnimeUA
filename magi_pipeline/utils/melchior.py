from magi_pipeline.translate.deepl_translate import deepl_translate

class Melchior:
    @staticmethod
    def translate(text, source_lang="ru", target_lang="uk"):
        if not text.strip():
            return ""
        translated = deepl_translate(text, source_lang=source_lang, target_lang=target_lang.upper())
        return translated 