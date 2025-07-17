import re
from pathlib import Path
from typing import Dict, List, Any


def parse_srt(srt_file: Path) -> Dict[str, Any]:
    """
    Парсить SRT файл та конвертує його в JSON формат аналогічно до ASS парсера.
    
    Args:
        srt_file: Шлях до SRT файлу
        
    Returns:
        Словник з структурою аналогічною до parse_ass
    """
    
    try:
        with open(srt_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Спробуємо інші кодування
        for encoding in ['cp1251', 'latin1', 'cp1252']:
            try:
                with open(srt_file, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            raise Exception("Не вдалося прочитати SRT файл")
    
    dialogue_entries = []
    
    # Розділяємо на блоки (кожен блок розділений подвійним переносом рядка)
    blocks = re.split(r'\n\s*\n', content.strip())
    
    for block in blocks:
        if not block.strip():
            continue
            
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # Перший рядок - номер субтитру
        try:
            subtitle_number = int(lines[0].strip())
        except ValueError:
            continue
            
        # Другий рядок - тайм-коди
        timeline = lines[1].strip()
        time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', timeline)
        
        if not time_match:
            continue
            
        start_time = time_match.group(1)
        end_time = time_match.group(2)
        
        # Решта рядків - текст субтитру
        text_lines = lines[2:]
        text = ' '.join(line.strip() for line in text_lines if line.strip())
        
        # Видаляємо HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        
        # Конвертуємо SRT час у ASS формат (h:mm:ss.cc)
        start_ass = srt_time_to_ass_time(start_time)
        end_ass = srt_time_to_ass_time(end_time)
        
        if text.strip():
            dialogue_entries.append({
                "start": start_ass,
                "end": end_ass,
                "text": text.strip()
            })
    
    return {
        "dialogue": dialogue_entries,
        "meta": {
            "source_format": "srt",
            "subtitle_count": len(dialogue_entries)
        }
    }


def srt_time_to_ass_time(srt_time: str) -> str:
    """
    Конвертує час з SRT формату (hh:mm:ss,mmm) в ASS формат (h:mm:ss.cc).
    
    Args:
        srt_time: Час в SRT форматі (наприклад, "00:01:23,456")
        
    Returns:
        Час в ASS форматі (наприклад, "0:01:23.46")
    """
    # SRT: 00:01:23,456
    # ASS: 0:01:23.46
    
    match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', srt_time)
    if not match:
        return "0:00:00.00"
    
    hours = int(match.group(1))
    minutes = match.group(2)
    seconds = match.group(3)
    milliseconds = match.group(4)
    
    # Конвертуємо мілісекунди в сотні секунди (ASS використовує 2 цифри)
    centiseconds = str(int(milliseconds) // 10).zfill(2)
    
    return f"{hours}:{minutes}:{seconds}.{centiseconds}"


def ass_time_to_srt_time(ass_time: str) -> str:
    """
    Конвертує час з ASS формату (h:mm:ss.cc) в SRT формат (hh:mm:ss,mmm).
    
    Args:
        ass_time: Час в ASS форматі (наприклад, "0:01:23.46")
        
    Returns:
        Час в SRT форматі (наприклад, "00:01:23,460")
    """
    # ASS: 0:01:23.46  
    # SRT: 00:01:23,460
    
    match = re.match(r'(\d+):(\d{2}):(\d{2})\.(\d{2})', ass_time)
    if not match:
        return "00:00:00,000"
    
    hours = int(match.group(1))
    minutes = match.group(2)
    seconds = match.group(3)
    centiseconds = match.group(4)
    
    # Конвертуємо сотні секунди в мілісекунди
    milliseconds = str(int(centiseconds) * 10).zfill(3)
    
    return f"{hours:02d}:{minutes}:{seconds},{milliseconds}"


def convert_dialogue_to_srt(dialogue_entries: List[Dict], output_file: Path = None) -> str:
    """
    Конвертує список dialogue entries назад в SRT формат.
    
    Args:
        dialogue_entries: Список dialogue записів з ASS парсера
        output_file: Опціональний шлях для збереження файлу
        
    Returns:
        SRT контент як рядок
    """
    srt_content = []
    
    for i, entry in enumerate(dialogue_entries, 1):
        start_srt = ass_time_to_srt_time(entry['start'])
        end_srt = ass_time_to_srt_time(entry['end'])
        text = entry['text']
        
        srt_block = f"{i}\n{start_srt} --> {end_srt}\n{text}\n"
        srt_content.append(srt_block)
    
    result = '\n'.join(srt_content)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Використання: python srt_parser.py input.srt")
        sys.exit(1)
    
    srt_file = Path(sys.argv[1])
    if not srt_file.exists():
        print(f"Файл {srt_file} не знайдено")
        sys.exit(1)
    
    result = parse_srt(srt_file)
    print(f"Парсинг завершено. Знайдено {len(result['dialogue'])} записів субтитрів.")
    
    # Приклад конвертації назад
    output_srt = srt_file.parent / f"{srt_file.stem}_converted.srt"
    convert_dialogue_to_srt(result['dialogue'], output_srt)
    print(f"Конвертований SRT збережено: {output_srt}")