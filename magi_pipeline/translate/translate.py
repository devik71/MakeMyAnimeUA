"""
translate.py — модуль перекладу субтитрів з російської на українську.
Це частина системи MAGI Pipeline для автоматичної локалізації аніме.
"""

from transformers import MarianMTModel, MarianTokenizer
import torch
import os
import sys

# ↓ 1. Завантаження моделі перекладу
# Ми використовуємо Helsinki-NLP — одну з найкращих моделей для російсько-українського перекладу
model_name = "Helsinki-NLP/opus-mt-ru-uk"

def _download_model_if_needed():
    try:
        MarianTokenizer.from_pretrained(model_name)
        MarianMTModel.from_pretrained(model_name)
    except Exception as e:
        print(f"[Helsinki-NLP] Завантаження моделі... ({model_name})")
        MarianTokenizer.from_pretrained(model_name, force_download=True)
        MarianMTModel.from_pretrained(model_name, force_download=True)
        print(f"[Helsinki-NLP] Модель завантажено!")

# Спроба завантажити модель, якщо її ще немає
try:
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
except (OSError, ValueError):
    print(f"[Helsinki-NLP] Модель не знайдена у кеші. Спроба завантажити...")
    _download_model_if_needed()
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)

# Автоматичний вибір CPU чи GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def translate_line(text: str) -> str:
    """
    Перекладає окремий рядок тексту з російської на українську.
    
    Parameters:
        text (str): Вхідний російський рядок
    Returns:
        str: Перекладений рядок українською
    """
    # Якщо текст порожній — одразу повертаємо порожній
    if not text.strip():
        return ""

    # Токенізуємо текст (розбиваємо на інструкції, готуємо для моделі)
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(device)

    # Генеруємо переклад за допомогою моделі
    translated = model.generate(**inputs)

    # Декодуємо вихід у текст (з токенів — у зрозумілий рядок)
    output = tokenizer.decode(translated[0], skip_special_tokens=True)

    return output
