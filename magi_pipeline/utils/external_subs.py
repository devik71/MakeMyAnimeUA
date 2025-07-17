import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple


def find_external_subtitles(video_file: Path, search_dirs: List[Path] = None) -> List[Dict]:
    """
    Пошук зовнішніх файлів субтитрів для відеофайлу.
    
    Args:
        video_file: Шлях до відеофайлу
        search_dirs: Список директорій для пошуку (якщо не вказано, шукає в директорії відео)
    
    Returns:
        Список знайдених файлів субтитрів з метаданими
    """
    if search_dirs is None:
        search_dirs = [video_file.parent]
    
    video_name = video_file.stem.lower()
    subtitle_extensions = ['.srt', '.ass', '.ssa', '.vtt', '.sub', '.sbv']
    
    found_subtitles = []
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        # Пошук файлів з розширеннями субтитрів
        for ext in subtitle_extensions:
            pattern = f"*{ext}"
            for sub_file in search_dir.glob(pattern):
                sub_name = sub_file.stem.lower()
                
                # Перевіряємо чи назва субтитрів відповідає відео
                if is_subtitle_match(video_name, sub_name):
                    lang = extract_language_from_filename(sub_name)
                    
                    found_subtitles.append({
                        'path': sub_file,
                        'name': sub_file.name,
                        'language': lang,
                        'format': ext[1:],  # без крапки
                        'match_score': calculate_match_score(video_name, sub_name),
                        'size': sub_file.stat().st_size
                    })
    
    # Сортуємо за рейтингом відповідності
    found_subtitles.sort(key=lambda x: x['match_score'], reverse=True)
    
    return found_subtitles


def is_subtitle_match(video_name: str, subtitle_name: str) -> bool:
    """
    Перевіряє чи відповідає файл субтитрів відеофайлу.
    """
    # Видаляємо загальні суфікси
    video_clean = clean_filename(video_name)
    sub_clean = clean_filename(subtitle_name)
    
    # Точна відповідність
    if video_clean == sub_clean:
        return True
    
    # Субтитри містять назву відео
    if video_clean in sub_clean:
        return True
    
    # Відео містить назву субтитрів (коротші субтитри)
    if sub_clean in video_clean and len(sub_clean) > 3:
        return True
    
    # Схожість за словами
    video_words = set(re.findall(r'\w+', video_clean))
    sub_words = set(re.findall(r'\w+', sub_clean))
    
    if video_words and sub_words:
        common_words = video_words.intersection(sub_words)
        similarity = len(common_words) / max(len(video_words), len(sub_words))
        return similarity > 0.6
    
    return False


def clean_filename(filename: str) -> str:
    """
    Очищає назву файлу від загальних суфіксів та префіксів.
    """
    result = filename.lower()
    
    # Видаляємо розширення файлів
    result = re.sub(r'\.(mkv|mp4|avi|mov|srt|ass|ssa|vtt|sub|sbv)$', '', result)
    
    # Видаляємо загальні суфікси якості та кодування
    patterns_to_remove = [
        r'\.\d{4}',  # .2023, .2024
        r'\.(720p|1080p|4k|uhd)',
        r'\.(web-?dl|webrip|brrip|dvdrip|bluray)',
        r'\.(x264|x265|h264|h265)',
        r'\.(ukrainian|english|russian|french|german)',
        r'\.(ua|en|ru|uk|fr|de|es|it|pl|cz|sk)',
        r'-\w+$'  # Видаляємо кінцеві теги релізних груп
    ]
    
    for pattern in patterns_to_remove:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)
    
    # Заміняємо роздільники на пробіли
    result = re.sub(r'[._\-]+', ' ', result)
    
    # Видаляємо зайві пробіли
    result = re.sub(r'\s+', ' ', result).strip()
    
    return result


def extract_language_from_filename(filename: str) -> str:
    """
    Витягує мову з назви файлу субтитрів.
    """
    filename_lower = filename.lower()
    
    # Словник мов
    languages = {
        'ua': 'ukrainian',
        'uk': 'ukrainian', 
        'ukr': 'ukrainian',
        'ukrainian': 'ukrainian',
        'en': 'english',
        'eng': 'english',
        'english': 'english',
        'ru': 'russian',
        'rus': 'russian',
        'russian': 'russian',
        'fr': 'french',
        'de': 'german',
        'es': 'spanish',
        'it': 'italian',
        'pl': 'polish',
        'cz': 'czech',
        'sk': 'slovak'
    }
    
    # Шукаємо мову в назві файлу
    for code, lang in languages.items():
        patterns = [
            rf'\.{code}$',          # film.ua
            rf'\.{code}\.',         # film.ua.srt
            rf'_{code}_',           # film_ua_HD
            rf'_{code}$',           # film_ua
            rf'_{code}\.',          # film_ua.srt
            rf'-{code}-',           # film-ua-HD
            rf'-{code}$',           # film-ua  
            rf'-{code}\.',          # film-ua.srt
            rf'\b{code}\b'          # загальний випадок
        ]
        
        for pattern in patterns:
            if re.search(pattern, filename_lower):
                return lang
    
    return 'unknown'


def calculate_match_score(video_name: str, subtitle_name: str) -> float:
    """
    Розраховує рейтинг відповідності субтитрів до відео (0-100).
    """
    video_clean = clean_filename(video_name)
    sub_clean = clean_filename(subtitle_name)
    
    # Точна відповідність
    if video_clean == sub_clean:
        return 100.0
    
    # Один файл містить інший
    if video_clean in sub_clean:
        return 90.0
    if sub_clean in video_clean and len(sub_clean) > 3:
        return 85.0
    
    # Схожість за словами
    video_words = set(re.findall(r'\w+', video_clean))
    sub_words = set(re.findall(r'\w+', sub_clean))
    
    if video_words and sub_words:
        common_words = video_words.intersection(sub_words)
        word_similarity = len(common_words) / max(len(video_words), len(sub_words))
        return word_similarity * 80
    
    return 0.0


def get_subtitle_preview(subtitle_file: Path, max_lines: int = 20) -> List[str]:
    """
    Отримує превʼю перших рядків субтитрів для перевірки.
    """
    lines = []
    
    try:
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Спробуємо інші кодування
        for encoding in ['cp1251', 'latin1', 'cp1252']:
            try:
                with open(subtitle_file, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            return ["Помилка читання файлу"]
    
    ext = subtitle_file.suffix.lower()
    
    if ext == '.srt':
        lines = extract_srt_preview(content, max_lines)
    elif ext in ['.ass', '.ssa']:
        lines = extract_ass_preview(content, max_lines)
    elif ext == '.vtt':
        lines = extract_vtt_preview(content, max_lines)
    else:
        # Для інших форматів просто беремо перші рядки
        lines = content.splitlines()[:max_lines]
    
    return [line.strip() for line in lines if line.strip()][:max_lines]


def extract_srt_preview(content: str, max_lines: int) -> List[str]:
    """Витягує превʼю з SRT субтитрів"""
    lines = []
    current_block = []
    
    for line in content.splitlines():
        line = line.strip()
        
        if line == '':
            if current_block:
                # Додаємо текст (пропускаємо номер та час)
                text_lines = current_block[2:] if len(current_block) > 2 else current_block
                for text_line in text_lines:
                    clean_text = re.sub(r'<[^>]+>', '', text_line).strip()
                    if clean_text:
                        lines.append(clean_text)
                        if len(lines) >= max_lines:
                            return lines
                current_block = []
        else:
            current_block.append(line)
    
    return lines


def extract_ass_preview(content: str, max_lines: int) -> List[str]:
    """Витягує превʼю з ASS/SSA субтитрів"""
    lines = []
    
    for line in content.splitlines():
        if line.startswith('Dialogue:'):
            parts = line.split(',', 9)
            if len(parts) >= 10:
                text = parts[9].replace('\\N', ' ').replace('\\n', ' ')
                # Видаляємо теги форматування
                text = re.sub(r'\{[^}]*\}', '', text).strip()
                if text and len(text) > 3:
                    lines.append(text)
                    if len(lines) >= max_lines:
                        break
    
    return lines


def extract_vtt_preview(content: str, max_lines: int) -> List[str]:
    """Витягує превʼю з VTT субтитрів"""
    lines = []
    in_cue = False
    
    for line in content.splitlines():
        line = line.strip()
        
        if '-->' in line:
            in_cue = True
            continue
        
        if in_cue:
            if line == '':
                in_cue = False
            else:
                # Видаляємо теги VTT
                clean_text = re.sub(r'<[^>]+>', '', line).strip()
                if clean_text:
                    lines.append(clean_text)
                    if len(lines) >= max_lines:
                        break
    
    return lines