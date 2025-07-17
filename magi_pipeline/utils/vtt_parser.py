import re
from pathlib import Path
from typing import Dict, List, Any


def parse_vtt(vtt_file: Path) -> Dict[str, Any]:
    """
    Парсить VTT файл та конвертує його в JSON формат аналогічно до ASS парсера.
    
    Args:
        vtt_file: Шлях до VTT файлу
        
    Returns:
        Словник з структурою аналогічною до parse_ass
    """
    
    try:
        with open(vtt_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Спробуємо інші кодування
        for encoding in ['cp1251', 'latin1', 'cp1252']:
            try:
                with open(vtt_file, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            raise Exception("Не вдалося прочитати VTT файл")
    
    dialogue_entries = []
    lines = content.splitlines()
    
    i = 0
    # Пропускаємо заголовок WEBVTT
    while i < len(lines) and not lines[i].startswith('WEBVTT'):
        i += 1
    if i < len(lines):
        i += 1  # Пропускаємо рядок з WEBVTT
    
    while i < len(lines):
        # Пропускаємо порожні рядки
        while i < len(lines) and not lines[i].strip():
            i += 1
        
        if i >= len(lines):
            break
        
        # Це може бути ідентифікатор cue або безпосередньо тайм-код
        current_line = lines[i].strip()
        
        # Перевіряємо, чи це тайм-код
        if '-->' in current_line:
            timeline = current_line
        else:
            # Це ідентифікатор cue, наступний рядок повинен бути тайм-кодом
            i += 1
            if i >= len(lines):
                break
            timeline = lines[i].strip()
        
        # Парсимо тайм-коди
        time_match = re.match(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})', timeline)
        if not time_match:
            i += 1
            continue
        
        start_time = time_match.group(1)
        end_time = time_match.group(2)
        
        # Збираємо текст субтитру до наступного порожнього рядка
        i += 1
        text_lines = []
        while i < len(lines) and lines[i].strip():
            text_lines.append(lines[i].strip())
            i += 1
        
        if text_lines:
            text = ' '.join(text_lines)
            # Видаляємо VTT теги (наприклад, <c.classname>text</c>)
            text = re.sub(r'<[^>]+>', '', text)
            
            # Конвертуємо VTT час у ASS формат
            start_ass = vtt_time_to_ass_time(start_time)
            end_ass = vtt_time_to_ass_time(end_time)
            
            if text.strip():
                dialogue_entries.append({
                    "start": start_ass,
                    "end": end_ass,
                    "text": text.strip()
                })
    
    return {
        "dialogue": dialogue_entries,
        "meta": {
            "source_format": "vtt",
            "subtitle_count": len(dialogue_entries)
        }
    }


def vtt_time_to_ass_time(vtt_time: str) -> str:
    """
    Конвертує час з VTT формату (hh:mm:ss.mmm) в ASS формат (h:mm:ss.cc).
    
    Args:
        vtt_time: Час в VTT форматі (наприклад, "00:01:23.456")
        
    Returns:
        Час в ASS форматі (наприклад, "0:01:23.46")
    """
    # VTT: 00:01:23.456
    # ASS: 0:01:23.46
    
    match = re.match(r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})', vtt_time)
    if not match:
        return "0:00:00.00"
    
    hours = int(match.group(1))
    minutes = match.group(2)
    seconds = match.group(3)
    milliseconds = match.group(4)
    
    # Конвертуємо мілісекунди в сотні секунди (ASS використовує 2 цифри)
    centiseconds = str(int(milliseconds) // 10).zfill(2)
    
    return f"{hours}:{minutes}:{seconds}.{centiseconds}"


def ass_time_to_vtt_time(ass_time: str) -> str:
    """
    Конвертує час з ASS формату (h:mm:ss.cc) в VTT формат (hh:mm:ss.mmm).
    
    Args:
        ass_time: Час в ASS форматі (наприклад, "0:01:23.46")
        
    Returns:
        Час в VTT форматі (наприклад, "00:01:23.460")
    """
    # ASS: 0:01:23.46  
    # VTT: 00:01:23.460
    
    match = re.match(r'(\d+):(\d{2}):(\d{2})\.(\d{2})', ass_time)
    if not match:
        return "00:00:00.000"
    
    hours = int(match.group(1))
    minutes = match.group(2)
    seconds = match.group(3)
    centiseconds = match.group(4)
    
    # Конвертуємо сотні секунди в мілісекунди
    milliseconds = str(int(centiseconds) * 10).zfill(3)
    
    return f"{hours:02d}:{minutes}:{seconds}.{milliseconds}"


def convert_dialogue_to_vtt(dialogue_entries: List[Dict], output_file: Path = None) -> str:
    """
    Конвертує список dialogue entries назад в VTT формат.
    
    Args:
        dialogue_entries: Список dialogue записів з ASS парсера
        output_file: Опціональний шлях для збереження файлу
        
    Returns:
        VTT контент як рядок
    """
    vtt_content = ["WEBVTT", ""]
    
    for i, entry in enumerate(dialogue_entries, 1):
        start_vtt = ass_time_to_vtt_time(entry['start'])
        end_vtt = ass_time_to_vtt_time(entry['end'])
        text = entry['text']
        
        vtt_content.append(f"{start_vtt} --> {end_vtt}")
        vtt_content.append(text)
        vtt_content.append("")  # Порожній рядок між cues
    
    result = '\n'.join(vtt_content)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Використання: python vtt_parser.py input.vtt")
        sys.exit(1)
    
    vtt_file = Path(sys.argv[1])
    if not vtt_file.exists():
        print(f"Файл {vtt_file} не знайдено")
        sys.exit(1)
    
    result = parse_vtt(vtt_file)
    print(f"Парсинг завершено. Знайдено {len(result['dialogue'])} записів субтитрів.")
    
    # Приклад конвертації назад
    output_vtt = vtt_file.parent / f"{vtt_file.stem}_converted.vtt"
    convert_dialogue_to_vtt(result['dialogue'], output_vtt)
    print(f"Конвертований VTT збережено: {output_vtt}")