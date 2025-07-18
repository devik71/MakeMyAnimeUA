#!/usr/bin/env python3
"""
🎬 MakeMyAnimeUA — Головний веб-інтерфейс для перекладу субтитрів
"""

import os
import sys
import json
import hashlib
import subprocess
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import threading
import time

# Додаємо шлях до модулів
sys.path.append(str(Path(__file__).resolve().parent))
from magi_pipeline.utils.balthasar import Balthasar
from magi_pipeline.utils.melchior import Melchior
from magi_pipeline.utils.caspar import Caspar
from magi_pipeline.utils.external_subs import find_external_subtitles, get_subtitle_preview

app = Flask(__name__)
app.secret_key = 'magi_pipeline_secret_key_2024'

# Конфігурація
UPLOAD_FOLDER = Path("uploads")
OUTPUT_FOLDER = Path("output") 
TEMP_AUDIO_FOLDER = Path("temp_audio")
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mkv', 'avi', 'mov'}
ALLOWED_SUBTITLE_EXTENSIONS = {'srt', 'ass', 'ssa', 'vtt'}

# Створюємо необхідні папки
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, TEMP_AUDIO_FOLDER]:
    folder.mkdir(exist_ok=True)

# Глобальний словник для зберігання стану сесій
processing_sessions = {}

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def get_file_hash(path):
    """Генерує хеш файлу для ідентифікації"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def analyze_video(video_path):
    """Аналізує відео файл - аудіо доріжки та субтитри"""
    try:
        # Запускаємо ffprobe для аналізу
        probe = subprocess.run([
            "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(video_path)
        ], capture_output=True, text=True)
        
        if probe.returncode != 0:
            return {"error": "Не вдалося проаналізувати відео"}
        
        streams_data = json.loads(probe.stdout)
        audio_streams = []
        subtitle_streams = []
        
        for stream in streams_data.get("streams", []):
            if stream["codec_type"] == "audio":
                audio_streams.append({
                    "index": stream["index"],
                    "codec": stream.get("codec_name", "unknown"),
                    "channels": stream.get("channels", 0),
                    "language": stream.get("tags", {}).get("language", "unknown"),
                    "title": stream.get("tags", {}).get("title", "")
                })
            elif stream["codec_type"] == "subtitle":
                subtitle_streams.append({
                    "index": stream["index"],
                    "codec": stream.get("codec_name", "unknown"),
                    "language": stream.get("tags", {}).get("language", "unknown"),
                    "title": stream.get("tags", {}).get("title", "")
                })
        
        # Шукаємо зовнішні субтитри
        external_subs = find_external_subtitles(video_path, [video_path.parent])
        
        return {
            "audio_streams": audio_streams,
            "subtitle_streams": subtitle_streams,
            "external_subtitles": external_subs,
            "video_info": {
                "filename": video_path.name,
                "size": video_path.stat().st_size,
                "hash": get_file_hash(video_path)
            }
        }
    except Exception as e:
        return {"error": f"Помилка аналізу відео: {str(e)}"}

def get_available_whisper_models():
    """Повертає список доступних моделей Whisper"""
    import torch
    
    models = [
        {"name": "tiny", "size": "39 MB", "vram": "~1 GB", "quality": "Низька", "speed": "Дуже швидка"},
        {"name": "base", "size": "74 MB", "vram": "~1 GB", "quality": "Хороша", "speed": "Швидка"},
        {"name": "small", "size": "244 MB", "vram": "~2 GB", "quality": "Краща", "speed": "Середня"},
        {"name": "medium", "size": "769 MB", "vram": "~4 GB", "quality": "Відмінна", "speed": "Повільна"},
        {"name": "large", "size": "1550 MB", "vram": "~8 GB", "quality": "Найкраща", "speed": "Дуже повільна"}
    ]
    
    # Перевіряємо доступність GPU
    gpu_available = torch.cuda.is_available()
    if gpu_available:
        gpu_memory = torch.cuda.get_device_properties(0).total_memory // (1024**3)  # GB
        recommended = "large" if gpu_memory >= 8 else "medium" if gpu_memory >= 4 else "small" if gpu_memory >= 2 else "base"
    else:
        recommended = "base"
        gpu_memory = 0
    
    return {
        "models": models,
        "gpu_available": gpu_available,
        "gpu_memory": gpu_memory,
        "recommended": recommended
    }

def get_available_subtitle_styles():
    """Повертає список доступних стилів субтитрів"""
    styles_dir = Path("magi_pipeline/ass_generator_module/styles")
    styles = []
    
    if styles_dir.exists():
        for style_file in styles_dir.glob("*.ass"):
            styles.append({
                "filename": style_file.name,
                "name": style_file.stem,
                "path": str(style_file)
            })
    
    return styles

@app.route('/')
def index():
    """Головна сторінка"""
    return render_template('main_pipeline.html')

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """Завантаження відео файлу"""
    if 'video' not in request.files:
        return jsonify({"error": "Файл не вибрано"})
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "Файл не вибрано"})
    
    if file and allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
        # Створюємо унікальну сесію
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        # Зберігаємо файл
        filename = secure_filename(file.filename)
        video_path = UPLOAD_FOLDER / f"{session_id}_{filename}"
        file.save(video_path)
        
        # Аналізуємо відео
        analysis = analyze_video(video_path)
        
        # Зберігаємо інформацію про сесію
        processing_sessions[session_id] = {
            "video_path": str(video_path),
            "analysis": analysis,
            "created_at": datetime.now().isoformat(),
            "status": "analyzed"
        }
        
        return jsonify({
            "session_id": session_id,
            "analysis": analysis,
            "whisper_models": get_available_whisper_models(),
            "subtitle_styles": get_available_subtitle_styles()
        })
    else:
        return jsonify({"error": "Непідтримуваний формат файлу"})

@app.route('/start_processing', methods=['POST'])
def start_processing():
    """Запуск процесу обробки"""
    session_id = session.get('session_id')
    if not session_id or session_id not in processing_sessions:
        return jsonify({"error": "Сесія не знайдена"})
    
    config = request.get_json()
    session_data = processing_sessions[session_id]
    session_data['config'] = config
    session_data['status'] = 'processing'
    session_data['progress'] = {"step": "starting", "percent": 0, "message": "Ініціалізація..."}
    
    # Запускаємо обробку в окремому потоці
    thread = threading.Thread(target=process_video_async, args=(session_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started"})

def process_video_async(session_id):
    """Асинхронна обробка відео"""
    try:
        session_data = processing_sessions[session_id]
        config = session_data['config']
        video_path = Path(session_data['video_path'])
        
        # Крок 1: Витягування аудіо (якщо потрібно)
        session_data['progress'] = {"step": "audio_extraction", "percent": 10, "message": "Витягування аудіо..."}
        
        audio_path = TEMP_AUDIO_FOLDER / f"{session_id}_audio.wav"
        
        if config['source_type'] == 'transcribe':
            Balthasar.extract_audio(video_path, audio_path)
            session_data['progress'] = {"step": "audio_extraction", "percent": 20, "message": "Аудіо витягнуто"}
        
        # Крок 2: Отримання субтитрів
        if config['source_type'] == 'transcribe':
            session_data['progress'] = {"step": "transcription", "percent": 30, "message": "Транскрибація..."}
            
            result = Balthasar.transcribe(
                audio_path, 
                model_name=config.get('whisper_model', 'base'),
                language=config.get('source_language', 'ru'),
                device="cuda" if config.get('use_gpu', True) else "cpu"
            )
            
            session_data['progress'] = {"step": "transcription", "percent": 50, "message": "Транскрибація завершена"}
            
        elif config['source_type'] == 'embedded':
            session_data['progress'] = {"step": "subtitle_extraction", "percent": 30, "message": "Витягування субтитрів..."}
            
            # Витягуємо вбудовані субтитри
            stream_index = config['subtitle_stream_index']
            extracted_path = TEMP_AUDIO_FOLDER / f"{session_id}_subs.srt"
            
            subprocess.run([
                "ffmpeg", "-y", "-i", str(video_path), 
                "-map", f"0:{stream_index}", "-c", "copy", str(extracted_path)
            ], check=True)
            
            # Парсимо субтитри
            if extracted_path.suffix.lower() == '.srt':
                result = parse_srt(extracted_path)
            else:
                result = parse_ass(extracted_path)
                
            session_data['progress'] = {"step": "subtitle_extraction", "percent": 50, "message": "Субтитри витягнуто"}
            
        elif config['source_type'] == 'external':
            session_data['progress'] = {"step": "subtitle_loading", "percent": 30, "message": "Завантаження субтитрів..."}
            
            # Завантажуємо зовнішні субтитри
            external_path = config['external_subtitle_path']
            if external_path.endswith('.srt'):
                result = parse_srt(external_path)
            else:
                result = parse_ass(external_path)
                
            session_data['progress'] = {"step": "subtitle_loading", "percent": 50, "message": "Субтитри завантажено"}
        
        # Крок 3: Переклад
        session_data['progress'] = {"step": "translation", "percent": 60, "message": "Переклад..."}
        
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
            session_data['progress'] = {
                "step": "translation", 
                "percent": int(progress_percent), 
                "message": f"Переклад {i+1}/{total_segments}"
            }
        
        # Зберігаємо перекладені субтитри
        translation_data = {
            "meta": {
                "video_name": video_path.name,
                "video_hash": get_file_hash(video_path),
                "translation_config": config,
                "created_at": datetime.now().isoformat()
            },
            "segments": translated_segments
        }
        
        translation_path = OUTPUT_FOLDER / f"{session_id}_translation.json"
        with open(translation_path, 'w', encoding='utf-8') as f:
            json.dump(translation_data, f, ensure_ascii=False, indent=2)
        
        session_data['translation_path'] = str(translation_path)
        session_data['progress'] = {"step": "translation_complete", "percent": 90, "message": "Переклад завершено"}
        session_data['status'] = 'translation_ready'
        
    except Exception as e:
        session_data['progress'] = {"step": "error", "percent": 0, "message": f"Помилка: {str(e)}"}
        session_data['status'] = 'error'

def parse_srt(path):
    """Парсинг SRT файлу"""
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
    """Парсинг ASS файлу"""
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

@app.route('/get_progress')
def get_progress():
    """Отримання прогресу обробки"""
    session_id = session.get('session_id')
    if not session_id or session_id not in processing_sessions:
        return jsonify({"error": "Сесія не знайдена"})
    
    session_data = processing_sessions[session_id]
    return jsonify({
        "status": session_data.get('status', 'unknown'),
        "progress": session_data.get('progress', {})
    })

@app.route('/edit_translation')
def edit_translation():
    """Перехід до редактора перекладу"""
    session_id = session.get('session_id')
    if not session_id or session_id not in processing_sessions:
        return redirect(url_for('index'))
    
    session_data = processing_sessions[session_id]
    if session_data.get('status') != 'translation_ready':
        return redirect(url_for('index'))
    
    # Передаємо session_id редактору
    return redirect(f"/editor?session={session_id}")

@app.route('/continue_processing', methods=['POST'])
def continue_processing():
    """Продовження обробки після редагування (або без нього)"""
    session_id = session.get('session_id')
    if not session_id or session_id not in processing_sessions:
        return jsonify({"error": "Сесія не знайдена"})
    
    session_data = processing_sessions[session_id]
    config = session_data['config']
    
    # Запускаємо генерацію ASS в окремому потоці
    thread = threading.Thread(target=generate_final_subtitles_async, args=(session_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "generating"})

def generate_final_subtitles_async(session_id):
    """Асинхронна генерація фінальних субтитрів"""
    try:
        session_data = processing_sessions[session_id]
        config = session_data['config']
        
        session_data['progress'] = {"step": "ass_generation", "percent": 95, "message": "Генерація ASS..."}
        
        # Завантажуємо перекладені субтитри
        translation_path = session_data['translation_path']
        with open(translation_path, 'r', encoding='utf-8') as f:
            translation_data = json.load(f)
        
        # Підготовляємо дані для ASS генератора
        subs = []
        for segment in translation_data['segments']:
            subs.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["translated"]
            })
        
        # Генеруємо ASS файл
        video_name = Path(session_data['video_path']).stem
        output_path = OUTPUT_FOLDER / f"{video_name}.ass"
        
        style_path = config.get('subtitle_style', 'magi_pipeline/ass_generator_module/styles/Dialogue.ass')
        
        Caspar.generate_subtitles(
            subs=subs,
            output_path=str(output_path),
            style_path=style_path
        )
        
        session_data['final_ass_path'] = str(output_path)
        session_data['progress'] = {"step": "complete", "percent": 100, "message": "Готово!"}
        session_data['status'] = 'complete'
        
    except Exception as e:
        session_data['progress'] = {"step": "error", "percent": 0, "message": f"Помилка генерації: {str(e)}"}
        session_data['status'] = 'error'

@app.route('/download_subtitles')
def download_subtitles():
    """Завантаження готових субтитрів"""
    session_id = session.get('session_id')
    if not session_id or session_id not in processing_sessions:
        return "Сесія не знайдена", 404
    
    session_data = processing_sessions[session_id]
    if 'final_ass_path' not in session_data:
        return "Файл не готовий", 404
    
    return send_file(session_data['final_ass_path'], as_attachment=True)

if __name__ == '__main__':
    print("🚀 Запуск MakeMyAnimeUA - Головний пайплайн")
    print("📍 http://localhost:5001")
    app.run(debug=True, port=5001, host='0.0.0.0')