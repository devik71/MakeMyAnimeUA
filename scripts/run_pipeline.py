import os
import sys
import subprocess
import json
import argparse
import time
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from magi_pipeline.translate.deepl_translate import deepl_translate
from magi_pipeline.ass_generator_module.ass_builder import generate_ass
import re
from collections import Counter
from magi_pipeline.utils.balthasar import Balthasar
from magi_pipeline.utils.melchior import Melchior
from magi_pipeline.utils.caspar import Caspar
from magi_pipeline.utils.external_subs import find_external_subtitles, get_subtitle_preview
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None
    print("⚠️  tqdm не встановлено. Прогрес-бар не буде показано.")
import hashlib

def get_file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def update_status(status_path, status_data):
    """Оновлення статус-файлу для веб-інтерфейсу"""
    try:
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Помилка запису статусу: {e}")

def main():
    parser = argparse.ArgumentParser(description='MakeMyAnimeUA Pipeline')
    parser.add_argument('--config', help='Шлях до конфіг-файлу')
    parser.add_argument('--session', help='ID сесії')
    parser.add_argument('--log', help='Шлях до лог-файлу')
    parser.add_argument('--status', help='Шлях до статус-файлу')
    
    args = parser.parse_args()
    
    # Якщо передано конфіг - використовуємо його
    if args.config and Path(args.config).exists():
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Встановлюємо змінні з конфігу
        video_file = Path(config['video_path'])
        output_dir = Path(config['output_dir'])
        temp_dir = Path(config['temp_dir'])
        session_id = config.get('session_id', args.session)
        status_path = Path(args.status) if args.status else None
        
        # Створюємо директорії
        output_dir.mkdir(exist_ok=True)
        temp_dir.mkdir(exist_ok=True)
        
        print(f"🎬 Запуск пайплайну для сесії: {session_id}")
        print(f"📹 Відео: {video_file}")
        
        # Оновлюємо статус
        if status_path:
            update_status(status_path, {
                "status": "starting",
                "progress": {"step": "starting", "percent": 5, "message": "Запуск пайплайну..."}
            })
        
        # Запускаємо обробку з конфігом
        run_pipeline_with_config(config, video_file, output_dir, temp_dir, session_id, status_path)
        
    else:
        # Класичний режим (без конфігу)
        run_classic_pipeline()

def run_pipeline_with_config(config, video_file, output_dir, temp_dir, session_id, status_path):
    """Запуск пайплайну з конфігурацією від веб-інтерфейсу"""
    
    def parse_srt(path):
        subs = []
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = re.compile(r'(\d+)\s+([\d:,]+)\s+-->\s+([\d:,]+)\s+([\s\S]*?)(?=\n\d+\n|\Z)', re.MULTILINE)
        for match in pattern.finditer(content):
            start = match.group(2).replace(',', '.')
            end = match.group(3).replace(',', '.')
            text = match.group(4).replace('\n', ' ').strip()
            
            def to_seconds(t):
                h, m, s = t.split(':')
                s, ms = s.split('.') if '.' in s else (s, '0')
                return int(h)*3600 + int(m)*60 + int(s) + int(ms.ljust(3, '0')[:3])/1000
            
            subs.append({
                'start': to_seconds(start),
                'end': to_seconds(end),
                'text': text
            })
        return {'segments': subs}

    def parse_ass(path):
        subs = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('Dialogue:'):
                    parts = line.strip().split(',', 9)
                    if len(parts) >= 10:
                        start = parts[1]
                        end = parts[2]
                        text = parts[9].replace('\\N', ' ').replace('\n', ' ').strip()
                        
                        def ass_time_to_seconds(t):
                            h, m, s = t.split(':')
                            s, cs = s.split('.') if '.' in s else (s, '0')
                            return int(h)*3600 + int(m)*60 + int(s) + int(cs)/100
                        
                        subs.append({
                            'start': ass_time_to_seconds(start),
                            'end': ass_time_to_seconds(end),
                            'text': text
                        })
        return {'segments': subs}
    
    try:
        # Крок 1: Витягування аудіо (якщо потрібно)
        if status_path:
            update_status(status_path, {
                "status": "processing",
                "progress": {"step": "audio_extraction", "percent": 10, "message": "Витягування аудіо..."}
            })
        
        audio_path = temp_dir / f"{session_id}_audio.wav"
        
        if config['source_type'] == 'transcribe':
            Balthasar.extract_audio(video_file, audio_path)
            print("✅ Аудіо витягнуто")
        
        # Крок 2: Отримання субтитрів
        if config['source_type'] == 'transcribe':
            if status_path:
                update_status(status_path, {
                    "status": "processing",
                    "progress": {"step": "transcription", "percent": 30, "message": "Транскрибація..."}
                })
            
            result = Balthasar.transcribe(
                audio_path, 
                model_name=config.get('whisper_model', 'base'),
                language=config.get('source_language', 'ru'),
                device="cuda" if config.get('use_gpu', True) else "cpu"
            )
            
            print("✅ Транскрибація завершена")
            
        elif config['source_type'] == 'embedded':
            if status_path:
                update_status(status_path, {
                    "status": "processing",
                    "progress": {"step": "subtitle_extraction", "percent": 30, "message": "Витягування субтитрів..."}
                })
            
            # Витягуємо вбудовані субтитри
            stream_index = config['subtitle_stream_index']
            extracted_path = temp_dir / f"{session_id}_subs.srt"
            
            subprocess.run([
                "ffmpeg", "-y", "-i", str(video_file), 
                "-map", f"0:{stream_index}", "-c", "copy", str(extracted_path)
            ], check=True)
            
            # Парсимо субтитри
            if extracted_path.suffix.lower() == '.srt':
                result = parse_srt(extracted_path)
            else:
                result = parse_ass(extracted_path)
                
            print("✅ Субтитри витягнуто")
            
        elif config['source_type'] == 'external':
            if status_path:
                update_status(status_path, {
                    "status": "processing",
                    "progress": {"step": "subtitle_loading", "percent": 30, "message": "Завантаження субтитрів..."}
                })
            
            # Завантажуємо зовнішні субтитри
            external_path = config['external_subtitle_path']
            if external_path.endswith('.srt'):
                result = parse_srt(external_path)
            else:
                result = parse_ass(external_path)
                
            print("✅ Субтитри завантажено")
        
        # Крок 3: Переклад
        if status_path:
            update_status(status_path, {
                "status": "processing",
                "progress": {"step": "translation", "percent": 60, "message": "Переклад..."}
            })
        
        translated_segments = []
        total_segments = len(result["segments"])
        
        for i, segment in enumerate(result["segments"]):
            translated_text = Melchior.translate(
                segment["text"],
                engine=config.get('translation_engine', 'helsinki'),
                api_key=config.get('deepl_api_key'),
                source_lang=config.get('source_language', 'ru'),
                target_lang=config.get('target_language', 'uk')
            )
            
            translated_segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "original": segment["text"],
                "translated": translated_text
            })
            
            # Оновлюємо прогрес
            progress_percent = 60 + (30 * i / total_segments)
            if status_path:
                update_status(status_path, {
                    "status": "processing",
                    "progress": {
                        "step": "translation", 
                        "percent": int(progress_percent), 
                        "message": f"Переклад {i+1}/{total_segments}"
                    }
                })
        
        # Зберігаємо перекладені субтитри
        translation_data = {
            "meta": {
                "video_name": video_file.name,
                "video_hash": get_file_hash(video_file),
                "translation_config": config,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "segments": translated_segments
        }
        
        translation_path = output_dir / f"{session_id}_translation.json"
        with open(translation_path, 'w', encoding='utf-8') as f:
            json.dump(translation_data, f, ensure_ascii=False, indent=2)
        
        print("✅ Переклад завершено")
        
        # Оновлюємо статус
        if status_path:
            update_status(status_path, {
                "status": "translation_ready",
                "progress": {"step": "translation_complete", "percent": 90, "message": "Переклад завершено"},
                "translation_path": str(translation_path)
            })
        
        print(f"🎉 Пайплайн завершено! Файл перекладу: {translation_path}")
        
    except Exception as e:
        error_msg = f"Помилка пайплайну: {str(e)}"
        print(f"❌ {error_msg}")
        
        if status_path:
            update_status(status_path, {
                "status": "error",
                "progress": {"step": "error", "percent": 0, "message": error_msg}
            })

def run_classic_pipeline():
    """Класичний режим роботи пайплайну (без веб-інтерфейсу)"""
    main_lang = 'ru'

    def parse_srt(path):
        subs = []
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = re.compile(r'(\d+)\s+([\d:,]+)\s+-->\s+([\d:,]+)\s+([\s\S]*?)(?=\n\d+\n|\Z)', re.MULTILINE)
        for match in pattern.finditer(content):
            start = match.group(2).replace(',', '.')
            end = match.group(3).replace(',', '.')
            text = match.group(4).replace('\n', ' ')
            def to_seconds(t):
                h, m, s = t.split(':')
                s, ms = s.split('.') if '.' in s else (s, '0')
                return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
            subs.append({
                'start': to_seconds(start),
                'end': to_seconds(end),
                'text': text
            })
        return {'segments': subs}

    def parse_ass(path):
        subs = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('Dialogue:'):
                    parts = line.strip().split(',', 9)
                    if len(parts) >= 10:
                        start = parts[1]
                        end = parts[2]
                        text = parts[9].replace('\\N', ' ').replace('\n', ' ').strip()
                        
                        def ass_time_to_seconds(t):
                            h, m, s = t.split(':')
                            s, cs = s.split('.') if '.' in s else (s, '0')
                            return int(h)*3600 + int(m)*60 + int(s) + int(cs)/100
                        
                        subs.append({
                            'start': ass_time_to_seconds(start),
                            'end': ass_time_to_seconds(end),
                            'text': text
                        })
        return {'segments': subs}

    def clean_text(text):
        text = re.sub(r'\{.*?\}', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    input_dir = Path("input")
    output_dir = Path("output")
    audio_dir = Path("temp_audio")
    audio_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    video_file = None
    for ext in ("*.mkv", "*.mp4", "*.avi", "*.mov"):
        files = list(input_dir.glob(ext))
        if files:
            video_file = files[0]
            break
    if video_file is None:
        raise FileNotFoundError("Не знайдено відеофайл у папці input/")

    subs_file = None

    # Спочатку шукаємо зовнішні субтитри
    print("🔍 Пошук зовнішніх субтитрів...")
    # Шукаємо в кількох місцях: input директорія, підпапки Subs, Subtitles тощо
    search_dirs = [input_dir]

    # Додаємо популярні підпапки для субтитрів
    for subdir_name in ['Subs', 'Subtitles', 'Sub', 'subs', 'subtitles', 'sub']:
        subdir = input_dir / subdir_name
        if subdir.exists() and subdir.is_dir():
            search_dirs.append(subdir)

    # Також шукаємо в директорії відеофайлу, якщо вона відрізняється від input
    video_dir = video_file.parent
    if video_dir != input_dir:
        search_dirs.append(video_dir)

    external_subs = find_external_subtitles(video_file, search_dirs)

    if external_subs:
        print(f"✅ Знайдено {len(external_subs)} зовнішніх файлів субтитрів:")
        for idx, sub in enumerate(external_subs):
            print(f"  [{idx}] {sub['name']} (мова: {sub['language']}, формат: {sub['format']}, рейтинг: {sub['match_score']:.1f})")
            
            # Показуємо превʼю
            preview = get_subtitle_preview(sub['path'], 3)
            if preview:
                print(f"      Превʼю: {' | '.join(preview[:2])}")
            print()
        
        # Запитуємо користувача чи використовувати зовнішні субтитри
        use_external = input("Використати зовнішні субтитри? (y/n, за замовчуванням y): ").strip().lower()
        
        if use_external in ('', 'y', 'yes', 'так', 'т'):
            if len(external_subs) == 1:
                chosen_external = external_subs[0]
                print(f"🎯 Автоматично вибрано: {chosen_external['name']}")
            else:
                chosen_idx = None
                while chosen_idx is None or not (0 <= chosen_idx < len(external_subs)):
                    try:
                        chosen_idx = int(input(f"Введіть номер файлу субтитрів (0-{len(external_subs)-1}): ").strip())
                    except ValueError:
                        chosen_idx = None
                chosen_external = external_subs[chosen_idx]
            
            print(f"✅ Вибрано зовнішні субтитри: {chosen_external['name']}")
            subs_file = chosen_external['path']
            
            # Для зовнішніх субтитрів створюємо JSON з метаданими
            if chosen_external['format'].lower() in ('srt', 'vtt', 'sub'):
                # Для SRT та інших текстових форматів створюємо простий JSON
                video_hash = get_file_hash(video_file)
                sub_data = {
                    "meta": {
                        "video_name": str(video_file),
                        "video_hash": video_hash,
                        "subtitle_file": str(subs_file),
                        "subtitle_format": chosen_external['format'],
                        "subtitle_language": chosen_external['language']
                    },
                    "dialogue": []
                }
                
                # Читаємо весь текст субтитрів для подальшої обробки
                try:
                    with open(subs_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Спробуємо інші кодування
                    for encoding in ['cp1251', 'latin1', 'cp1252']:
                        try:
                            with open(subs_file, 'r', encoding=encoding) as f:
                                content = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        raise Exception("Не вдалося прочитати файл субтитрів")
                
                         # Парсимо різні формати субтитрів
                 if chosen_external['format'].lower() == 'srt':
                     from magi_pipeline.utils.srt_parser import parse_srt
                     sub_data = parse_srt(subs_file)
                     sub_data["meta"] = {
                         "video_name": str(video_file),
                         "video_hash": video_hash,
                         "subtitle_file": str(subs_file),
                         "subtitle_format": "srt",
                         "subtitle_language": chosen_external['language']
                     }
                 elif chosen_external['format'].lower() == 'vtt':
                     from magi_pipeline.utils.vtt_parser import parse_vtt
                     sub_data = parse_vtt(subs_file)
                     sub_data["meta"] = {
                         "video_name": str(video_file),
                         "video_hash": video_hash,
                         "subtitle_file": str(subs_file),
                         "subtitle_format": "vtt",
                         "subtitle_language": chosen_external['language']
                     }
                
                with open(output_dir / "subs_source.json", "w", encoding="utf-8") as f:
                    json.dump(sub_data, f, ensure_ascii=False, indent=2)
                    
            elif chosen_external['format'].lower() in ('ass', 'ssa'):
                # Для ASS файлів використовуємо існуючий парсер
                result = parse_ass(subs_file)
                video_hash = get_file_hash(video_file)
                if isinstance(result, dict):
                    result["meta"] = {
                        "video_name": str(video_file), 
                        "video_hash": video_hash,
                        "subtitle_file": str(subs_file),
                        "subtitle_format": chosen_external['format'],
                        "subtitle_language": chosen_external['language']
                    }
                with open(output_dir / "subs_source.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

    if subs_file is None:
        # Якщо зовнішні субтитри не використовуються, шукаємо всередині відео
        print("🔍 Пошук субтитрів всередині відеофайлу...")
        probe = subprocess.run([
            "ffmpeg", "-i", str(video_file)
        ], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        subtitle_streams = []
        for line in probe.stderr.splitlines():
            if "Subtitle:" in line:
                m = re.search(r'Stream #0:(\d+)(\((\w+)\))?: Subtitle: (\w+)( \((.*?)\))?', line)
                if m:
                    stream_id = m.group(1)
                    lang = m.group(3) or "unknown"
                    fmt = m.group(4)
                    title = m.group(6) or ""
                    subtitle_streams.append({
                        "id": stream_id,
                        "lang": lang,
                        "fmt": fmt,
                        "title": title,
                        "raw": line.strip()
                    })
        if not subtitle_streams:
            print("⚠️  Не знайдено потік сабів у відео!")
            print("🔄 Переходимо до транскрибації аудіо...")
            subs_file = None
        else:
            print("Знайдено потоки сабів:")
            for idx, s in enumerate(subtitle_streams):
                print(f"  [{idx}] Stream #{s['id']}: lang={s['lang']} fmt={s['fmt']} title={s['title']} | {s['raw']}")
            chosen_idx = None
            while chosen_idx is None or not (0 <= chosen_idx < len(subtitle_streams)):
                try:
                    chosen_idx = int(input(f"Введіть номер потоку сабів для витягання (0-{len(subtitle_streams)-1}): ").strip())
                except ValueError:
                    chosen_idx = None
            chosen = subtitle_streams[chosen_idx]
            print(f"\nВибрано потік #{chosen['id']} (lang={chosen['lang']} fmt={chosen['fmt']} title={chosen['title']})")
            extracted_path = input_dir / f"extracted_subs_{chosen['id']}.{chosen['fmt'].lower()}"
            subprocess.run([
                "ffmpeg", "-y", "-i", str(video_file), "-map", f"0:{chosen['id']}", "-c", "copy", str(extracted_path)
            ], check=True)
            print(f"Саби збережено у {extracted_path}")
            subs_file = extracted_path
            def clean_text(text):
                return re.sub(r'\{.*?\}', '', text).strip()
            lines = []
            if chosen['fmt'].lower() in ("ass", "ssa"):
                with open(extracted_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('Dialogue:'):
                            parts = line.strip().split(',', 9)
                            if len(parts) >= 10:
                                text = parts[9].replace('\\N', ' ').replace('\n', ' ')
                                text = clean_text(text)
                                if len(text) > 10:
                                    lines.append(text)
                                if len(lines) >= 20:
                                    break
                result = parse_ass(extracted_path)
                video_hash = get_file_hash(video_file)
                if isinstance(result, dict):
                    result["meta"] = {"video_name": str(video_file), "video_hash": video_hash}
                with open(output_dir / "subs_source.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            elif chosen['fmt'].lower() == "srt":
                with open(extracted_path, 'r', encoding='utf-8') as f:
                    block = []
                    for l in f:
                        if l.strip() == '':
                            if block:
                                text = ' '.join(block)
                                text = clean_text(text)
                                if len(text) > 10:
                                    lines.append(text)
                                block = []
                                if len(lines) >= 20:
                                    break
                        elif not l.strip().isdigit() and '-->' not in l:
                            block.append(l.strip())
                result = parse_srt(extracted_path)
                video_hash = get_file_hash(video_file)
                if isinstance(result, dict):
                    result["meta"] = {"video_name": str(video_file), "video_hash": video_hash}
                with open(output_dir / "subs_source.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            print("\nПерші 5 реплік:")
            for i, t in enumerate(lines[:5]):
                print(f"  {i+1}. {t}")
            main_lang = 'ru'

    print("🎙️  Extracting audio...")
    audio_path = audio_dir / "extracted.wav"
    Balthasar.extract_audio(video_file, audio_path)

    source_path = output_dir / "subs_source.json"
    transcript_path = output_dir / "subs_original.json"
    need_extract_subs = True
    if source_path.exists():
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                subs_json = json.load(f)
            meta = subs_json.get("meta", {})
            video_hash = get_file_hash(video_file)
            if meta.get("video_name") == str(video_file) and meta.get("video_hash") == video_hash:
                print(f"✅ subs_source.json відповідає поточному відеофайлу: {video_file}")
                need_extract_subs = False
            else:
                print(f"⚠️ subs_source.json не відповідає відеофайлу або відсутні метадані. Буде оновлено.")
        except Exception as e:
            print(f"⚠️ Не вдалося прочитати subs_source.json: {e}")
            need_extract_subs = True
    if need_extract_subs:
        print("🧠  Transcribing...")
        model_name = "base"
        transcribe_lang = "ru"
        result = Balthasar.transcribe(audio_path, model_name=model_name, language=transcribe_lang)
        with open(source_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    print("🌐  Translating to Ukrainian...")
    subs_path = output_dir / "subs_uk.json"
    if subs_path.exists():
        with open(subs_path, "r", encoding="utf-8") as f:
            subs = json.load(f)
    else:
        subs = []
        with open(source_path, "r", encoding="utf-8") as f:
            source_data = json.load(f)
        if 'main_lang' not in locals():
            main_lang = 'ru'
        all_texts = [segment["text"] for segment in source_data["segments"]]
        if tqdm:
            translated_texts = []
            for t in tqdm(all_texts, desc="Translating", unit="line"):
                translated_texts.append(Melchior.translate(t, source_lang=main_lang, target_lang="uk"))
        else:
            translated_texts = [Melchior.translate(t, source_lang=main_lang, target_lang="uk") for t in all_texts]
        for segment, translated in zip(source_data["segments"], translated_texts):
            subs.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": translated
            })
        with open(subs_path, "w", encoding="utf-8") as f:
            json.dump(subs, f, ensure_ascii=False, indent=2)

    print("🧾  Generating styled ASS subtitles...")
    style_path = "magi_pipeline/ass_generator_module/styles/Dialogue.ass"
    print("✅ Використовується дефолтний стиль: Retro Yellow (Dialogue.ass)")
    Caspar.generate_subtitles(
        subs=subs,
        output_path=str(output_dir / f"{video_file.stem}.ass"),
        style_path=style_path
    )
    print("✅ Готово! Файл субтитрів збережено в output/")

    # --- Додаємо копіювання .ass у input/ ---
    import shutil
    ass_file = output_dir / f"{video_file.stem}.ass"
    if ass_file.exists():
        dest = input_dir / ass_file.name
        shutil.copy(ass_file, dest)
        print(f"✅ Субтитри також скопійовано в input/: {dest}")

if __name__ == "__main__":
    main()
