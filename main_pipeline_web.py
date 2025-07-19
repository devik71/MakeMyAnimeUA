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
    """Перевіряє чи дозволено розширення файлу"""
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in extensions

def is_valid_video_file(file_path):
    """Додаткова перевірка чи файл є валідним відео"""
    try:
        # Швидка перевірка через ffprobe
        probe = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0", 
            "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(file_path)
        ], capture_output=True, text=True, timeout=10)
        
        return probe.returncode == 0 and "video" in probe.stdout
    except Exception:
        return False

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
        # Перевіряємо чи файл існує
        if not video_path.exists():
            return {"error": "Файл не знайдено"}
            
        # Запускаємо ffprobe для аналізу
        probe = subprocess.run([
            "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(video_path)
        ], capture_output=True, text=True)
        
        if probe.returncode != 0:
            # Детальніша інформація про помилку
            error_msg = probe.stderr if probe.stderr else "Невалідний відео файл"
            return {"error": f"Помилка ffprobe: {error_msg}"}
        
        if not probe.stdout.strip():
            return {"error": "ffprobe не повернув даних - можливо файл пошкоджений"}
            
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
    import time
    session_id = request.args.get('session')
    
    # Якщо передано session_id, відновлюємо сесію
    if session_id and session_id in processing_sessions:
        session['session_id'] = session_id
    
    return render_template('main_pipeline.html', 
                         timestamp=int(time.time()),
                         session_id=session_id)

@app.route('/test')
def test_upload():
    """Тестова сторінка для діагностики завантаження"""
    with open('test_upload.html', 'r') as f:
        return f.read()

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """Завантаження відео файлу"""
    try:
        # Перевіряємо наявність файлу
        if 'video' not in request.files:
            return jsonify({"error": "Файл не вибрано"}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({"error": "Файл не вибрано"}), 400
        
        # Перевіряємо розмір файлу (max 2GB)
        if hasattr(file, 'content_length') and file.content_length > 2 * 1024 * 1024 * 1024:
            return jsonify({"error": "Файл занадто великий (максимум 2GB)"}), 400
        
        # Перевіряємо формат файлу
        if not file or not allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
            return jsonify({"error": f"Непідтримуваний формат файлу. Підтримувані: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"}), 400
        
        # Створюємо унікальну сесію
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        # Створюємо папку uploads якщо її немає
        UPLOAD_FOLDER.mkdir(exist_ok=True)
        
        # Зберігаємо файл
        filename = secure_filename(file.filename)
        video_path = UPLOAD_FOLDER / f"{session_id}_{filename}"
        
        print(f"Зберігаємо файл: {video_path}")
        file.save(video_path)
        
        # Перевіряємо що файл збережено
        if not video_path.exists():
            return jsonify({"error": "Помилка збереження файлу"}), 500
        
        print(f"Файл збережено успішно. Розмір: {video_path.stat().st_size} байт")
        
        # Додаткова перевірка чи файл є валідним відео
        print("Перевіряємо валідність відео файлу...")
        if not is_valid_video_file(video_path):
            # Видаляємо невалідний файл
            video_path.unlink(missing_ok=True)
            return jsonify({"error": "Завантажений файл не є валідним відео файлом. Перевірте формат та цілісність файлу."}), 400
        
        # Аналізуємо відео
        print("Починаємо аналіз відео...")
        analysis = analyze_video(video_path)
        print(f"Аналіз завершено: {analysis}")
        
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
        
    except Exception as e:
        print(f"Помилка завантаження файлу: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Внутрішня помилка сервера: {str(e)}"}), 500

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
    """Асинхронна обробка відео через термінальний пайплайн"""
    try:
        session_data = processing_sessions[session_id]
        config = session_data['config']
        video_path = Path(session_data['video_path'])
        
        # Створюємо конфіг-файл для термінального пайплайну
        config_path = TEMP_AUDIO_FOLDER / f"{session_id}_config.json"
        
        pipeline_config = {
            "session_id": session_id,
            "video_path": str(video_path),
            "output_dir": str(OUTPUT_FOLDER),
            "temp_dir": str(TEMP_AUDIO_FOLDER),
            "translation_engine": config.get('translation_engine', 'helsinki'),
            "source_language": config.get('source_language', 'ru'),
            "target_language": config.get('target_language', 'uk'),
            "whisper_model": config.get('whisper_model', 'base'),
            "use_gpu": config.get('use_gpu', True),
            "subtitle_style": config.get('subtitle_style', 'magi_pipeline/ass_generator_module/styles/Dialogue.ass'),
            "deepl_api_key": config.get('deepl_api_key'),
            "source_type": config.get('source_type', 'transcribe'),
            "subtitle_stream_index": config.get('subtitle_stream_index'),
            "external_subtitle_path": config.get('external_subtitle_path'),
            "web_interface": True
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(pipeline_config, f, ensure_ascii=False, indent=2)
        
        # Створюємо лог-файл для моніторингу
        log_path = TEMP_AUDIO_FOLDER / f"{session_id}_pipeline.log"
        status_path = TEMP_AUDIO_FOLDER / f"{session_id}_status.json"
        
        # Запускаємо термінальний пайплайн
        session_data['progress'] = {"step": "starting_pipeline", "percent": 5, "message": "Запуск пайплайну..."}
        
        # Запускаємо пайплайн у фоновому режимі
        import subprocess
        import sys
        
        cmd = [
            sys.executable, 
            "scripts/run_pipeline.py",
            "--config", str(config_path),
            "--session", session_id,
            "--log", str(log_path),
            "--status", str(status_path)
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        session_data['pipeline_process'] = process
        session_data['log_path'] = str(log_path)
        session_data['status_path'] = str(status_path)
        
        # Запускаємо моніторинг прогресу
        thread = threading.Thread(target=monitor_pipeline_progress, args=(session_id,))
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        session_data['progress'] = {"step": "error", "percent": 0, "message": f"Помилка запуску: {str(e)}"}
        session_data['status'] = 'error'

def monitor_pipeline_progress(session_id):
    """Моніторинг прогресу термінального пайплайну"""
    try:
        session_data = processing_sessions[session_id]
        status_path = Path(session_data['status_path'])
        log_path = Path(session_data['log_path'])
        
        while True:
            # Перевіряємо статус-файл
            if status_path.exists():
                try:
                    with open(status_path, 'r', encoding='utf-8') as f:
                        status_data = json.load(f)
                    
                    session_data['progress'] = status_data.get('progress', session_data['progress'])
                    session_data['status'] = status_data.get('status', session_data['status'])
                    
                    # Якщо пайплайн завершився
                    if status_data.get('status') in ['complete', 'error', 'translation_ready']:
                        if status_data.get('status') == 'translation_ready':
                            session_data['translation_path'] = status_data.get('translation_path')
                        elif status_data.get('status') == 'complete':
                            session_data['final_ass_path'] = status_data.get('final_ass_path')
                        break
                        
                except Exception as e:
                    print(f"Помилка читання статусу: {e}")
            
            # Перевіряємо чи процес ще працює
            process = session_data.get('pipeline_process')
            if process and process.poll() is not None:
                # Процес завершився
                if process.returncode == 0:
                    session_data['progress'] = {"step": "complete", "percent": 100, "message": "Пайплайн завершено"}
                    session_data['status'] = 'complete'
                else:
                    stdout, stderr = process.communicate()
                    error_msg = stderr if stderr else "Невідома помилка"
                    session_data['progress'] = {"step": "error", "percent": 0, "message": f"Помилка пайплайну: {error_msg}"}
                    session_data['status'] = 'error'
                break
            
            time.sleep(2)  # Перевіряємо кожні 2 секунди
            
    except Exception as e:
        session_data['progress'] = {"step": "error", "percent": 0, "message": f"Помилка моніторингу: {str(e)}"}
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

@app.route('/editor')
def translation_editor():
    """Редактор перекладу"""
    import time
    session_id = request.args.get('session')
    
    if not session_id or session_id not in processing_sessions:
        return redirect(url_for('index'))
    
    session_data = processing_sessions[session_id]
    translation_path = session_data.get('translation_path')
    
    if not translation_path or not Path(translation_path).exists():
        return redirect(url_for('index'))
    
    return render_template('translation_editor.html', 
                         session_id=session_id, 
                         timestamp=int(time.time()))

@app.route('/api/translation/<session_id>')
def get_translation_data(session_id):
    """API для отримання даних перекладу"""
    if session_id not in processing_sessions:
        return jsonify({"error": "Сесія не знайдена"}), 404
    
    session_data = processing_sessions[session_id]
    translation_path = session_data.get('translation_path')
    
    if not translation_path or not Path(translation_path).exists():
        return jsonify({"error": "Файл перекладу не знайдено"}), 404
    
    try:
        with open(translation_path, 'r', encoding='utf-8') as f:
            translation_data = json.load(f)
        return jsonify(translation_data)
    except Exception as e:
        return jsonify({"error": f"Помилка читання файлу: {str(e)}"}), 500

@app.route('/api/translation/<session_id>', methods=['POST'])
def save_translation_data(session_id):
    """API для збереження змін перекладу"""
    if session_id not in processing_sessions:
        return jsonify({"error": "Сесія не знайдена"}), 404
    
    session_data = processing_sessions[session_id]
    translation_path = session_data.get('translation_path')
    
    if not translation_path:
        return jsonify({"error": "Файл перекладу не знайдено"}), 404
    
    try:
        data = request.get_json()
        if not data or 'segments' not in data:
            return jsonify({"error": "Невірний формат даних"}), 400
        
        # Оновлюємо timestamp
        data['meta']['updated_at'] = datetime.now().isoformat()
        
        with open(translation_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": "Переклад збережено"})
    except Exception as e:
        return jsonify({"error": f"Помилка збереження: {str(e)}"}), 500

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