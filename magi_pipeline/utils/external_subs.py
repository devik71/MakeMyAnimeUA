"""
external_subs.py — пошук та аналіз зовнішніх субтитрів
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional

def find_external_subtitles(video_path: Path, search_dirs: List[Path]) -> List[Dict]:
    """
    Знаходить зовнішні файли субтитрів для відеофайлу
    
    Args:
        video_path: Шлях до відеофайлу
        search_dirs: Директорії для пошуку
    
    Returns:
        Список знайдених субтитрів з метаданими
    """
    video_name = video_path.stem
    subtitle_extensions = ['.srt', '.ass', '.ssa', '.vtt', '.sub']
    found_subtitles = []
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        # Шукаємо файли субтитрів
        for sub_file in search_dir.rglob("*"):
            if sub_file.suffix.lower() in subtitle_extensions:
                match_score = calculate_name_similarity(video_name, sub_file.stem)
                
                if match_score > 0.3:  # Мінімальний поріг схожості
                    language = detect_subtitle_language(sub_file)
                    
                    found_subtitles.append({
                        'path': str(sub_file),
                        'name': sub_file.name,
                        'format': sub_file.suffix[1:].upper(),
                        'language': language,
                        'match_score': match_score,
                        'size': sub_file.stat().st_size
                    })
    
    # Сортуємо за рейтингом відповідності
    found_subtitles.sort(key=lambda x: x['match_score'], reverse=True)
    
    return found_subtitles

def calculate_name_similarity(video_name: str, subtitle_name: str) -> float:
    """
    Обчислює схожість назв відеофайлу та субтитрів
    
    Args:
        video_name: Назва відеофайлу (без розширення)
        subtitle_name: Назва файлу субтитрів (без розширення)
    
    Returns:
        Оцінка схожості від 0 до 1
    """
    # Нормалізуємо назви
    video_clean = normalize_filename(video_name)
    subtitle_clean = normalize_filename(subtitle_name)
    
    # Точне співпадіння
    if video_clean == subtitle_clean:
        return 1.0
    
    # Субтитри містять назву відео
    if video_clean in subtitle_clean:
        return 0.9
    
    # Відео містить назву субтитрів
    if subtitle_clean in video_clean:
        return 0.8
    
    # Порівняння слів
    video_words = set(video_clean.split())
    subtitle_words = set(subtitle_clean.split())
    
    if video_words and subtitle_words:
        common_words = video_words.intersection(subtitle_words)
        total_words = video_words.union(subtitle_words)
        similarity = len(common_words) / len(total_words)
        
        # Бонус за довгі спільні послідовності
        if similarity > 0.5:
            return min(0.85, similarity + 0.2)
        return similarity
    
    return 0.0

def normalize_filename(filename: str) -> str:
    """
    Нормалізує назву файлу для порівняння
    """
    # Видаляємо розширення та зайві символи
    filename = re.sub(r'\[.*?\]', '', filename)  # [1080p], [rus], etc.
    filename = re.sub(r'\(.*?\)', '', filename)  # (2023), (HDTV), etc.
    filename = re.sub(r'[._-]+', ' ', filename)  # Замінюємо роздільники на пробіли
    filename = re.sub(r'\s+', ' ', filename)     # Множинні пробіли на одинарні
    
    return filename.lower().strip()

def detect_subtitle_language(subtitle_path: Path) -> str:
    """
    Визначає мову субтитрів на основі назви файлу та вмісту
    
    Args:
        subtitle_path: Шлях до файлу субтитрів
    
    Returns:
        Код мови або 'unknown'
    """
    filename = subtitle_path.name.lower()
    
    # Коди мов у назві файлу
    language_patterns = {
        'ru': [r'\bru\b', r'\brussian\b', r'\bрус\b'],
        'en': [r'\ben\b', r'\benglish\b', r'\beng\b'],
        'uk': [r'\bukr\b', r'\bukrainian\b', r'\bukr\b'],
        'ja': [r'\bjap\b', r'\bjapanese\b', r'\bjpn\b'],
        'de': [r'\bger\b', r'\bgerman\b', r'\bde\b'],
        'fr': [r'\bfra\b', r'\bfrench\b', r'\bfr\b'],
        'es': [r'\besp\b', r'\bspanish\b', r'\bes\b'],
    }
    
    for lang_code, patterns in language_patterns.items():
        for pattern in patterns:
            if re.search(pattern, filename):
                return lang_code
    
    # Аналіз вмісту (перші кілька рядків)
    try:
        detected_lang = detect_language_from_content(subtitle_path)
        if detected_lang:
            return detected_lang
    except:
        pass
    
    return 'unknown'

def detect_language_from_content(subtitle_path: Path) -> Optional[str]:
    """
    Визначає мову на основі вмісту субтитрів
    """
    try:
        # Читаємо перші 1000 символів
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            content = f.read(1000)
    except UnicodeDecodeError:
        # Пробуємо інші кодування
        for encoding in ['cp1251', 'latin1', 'cp1252']:
            try:
                with open(subtitle_path, 'r', encoding=encoding) as f:
                    content = f.read(1000)
                break
            except UnicodeDecodeError:
                continue
        else:
            return None
    
    # Простий аналіз на основі характерних символів
    cyrillic_count = len(re.findall(r'[а-яё]', content, re.IGNORECASE))
    latin_count = len(re.findall(r'[a-z]', content, re.IGNORECASE))
    ukrainian_chars = len(re.findall(r'[ґєіїє]', content, re.IGNORECASE))
    
    total_chars = cyrillic_count + latin_count
    
    if total_chars == 0:
        return None
    
    cyrillic_ratio = cyrillic_count / total_chars
    
    if cyrillic_ratio > 0.7:
        # Кирилиця переважає
        if ukrainian_chars > 0 and ukrainian_chars / cyrillic_count > 0.1:
            return 'uk'  # Українська
        else:
            return 'ru'  # Російська
    elif cyrillic_ratio < 0.3:
        return 'en'  # Англійська (або інша латинська)
    
    return 'unknown'

def get_subtitle_preview(subtitle_path: Path, max_lines: int = 3) -> List[str]:
    """
    Отримує превʼю перших рядків субтитрів
    
    Args:
        subtitle_path: Шлях до файлу субтитрів
        max_lines: Максимальна кількість рядків для превʼю
    
    Returns:
        Список текстових рядків
    """
    try:
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Пробуємо інші кодування
        for encoding in ['cp1251', 'latin1', 'cp1252']:
            try:
                with open(subtitle_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            return ["Не вдалося прочитати файл"]
    
    lines = []
    
    if subtitle_path.suffix.lower() == '.srt':
        # Парсинг SRT
        pattern = re.compile(r'(\d+)\s+([\d:,]+)\s+-->\s+([\d:,]+)\s+([\s\S]*?)(?=\n\d+\n|\Z)', re.MULTILINE)
        matches = list(pattern.finditer(content))
        
        for match in matches[:max_lines]:
            text = match.group(4).replace('\n', ' ').strip()
            text = re.sub(r'\s+', ' ', text)  # Множинні пробіли
            if text and len(text) > 5:
                lines.append(text[:100] + ('...' if len(text) > 100 else ''))
                
    elif subtitle_path.suffix.lower() in ['.ass', '.ssa']:
        # Парсинг ASS
        for line in content.split('\n'):
            if line.startswith('Dialogue:'):
                parts = line.split(',', 9)
                if len(parts) >= 10:
                    text = parts[9].replace('\\N', ' ').strip()
                    text = re.sub(r'\{.*?\}', '', text)  # Видаляємо теги
                    text = re.sub(r'\s+', ' ', text)
                    if text and len(text) > 5:
                        lines.append(text[:100] + ('...' if len(text) > 100 else ''))
                        if len(lines) >= max_lines:
                            break
    
    return lines[:max_lines] if lines else ["Не вдалося отримати превʼю"]