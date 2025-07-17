"""
translate.py — модуль перекладу субтитрів з російської на українську.
Це частина системи MAGI Pipeline для автоматичної локалізації аніме.
"""

from transformers import MarianMTModel, MarianTokenizer
import torch

# ↓ 1. Завантаження моделі перекладу
# Ми використовуємо Helsinki-NLP — одну з найкращих моделей для російсько-українського перекладу
model_name = "Helsinki-NLP/opus-mt-ru-uk"

# Завантажуємо токенізатор (розбиває речення на токени для обробки)
tokenizer = MarianTokenizer.from_pretrained(model_name)

# Завантажуємо саму модель
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
