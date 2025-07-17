import sys
import subprocess
import re
from pathlib import Path
import json
from langdetect import detect

# === Налаштування ===
input_dir = Path("input")
video_file = None
for ext in ("*.mkv", "*.mp4", "*.avi", "*.mov"):
    files = list(input_dir.glob(ext))
    if files:
        video_file = files[0]
        break
if video_file is None:
    print("Не знайдено відеофайл у папці input/")
    sys.exit(1)

# === Витягуємо список потоків через ffmpeg ===
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
    print("Не знайдено потоків сабів у відео!")
    sys.exit(1)

print("Знайдено потоки сабів:")
for s in subtitle_streams:
    print(f"  Stream #{s['id']}: lang={s['lang']} fmt={s['fmt']} title={s['title']} | {s['raw']}")

# === Вибір потоку ===
# Автоматично вибираємо перший ASS/SSA/SRT, або з title 'Полные субтитры', або за номером
chosen = None
for s in subtitle_streams:
    if 'Полные субтитры' in s['title']:
        chosen = s
        break
for s in subtitle_streams:
    if not chosen and s['fmt'].lower() in ('ass','ssa','srt'):
        chosen = s
        break
if not chosen:
    chosen = subtitle_streams[0]

print(f"\nВибрано потік #{chosen['id']} (lang={chosen['lang']} fmt={chosen['fmt']} title={chosen['title']})")

# === Витягуємо саби ===
output_path = input_dir / f"extracted_subs_{chosen['id']}.{chosen['fmt'].lower()}"
subprocess.run([
    "ffmpeg", "-y", "-i", str(video_file), "-map", f"0:{chosen['id']}", "-c", "copy", str(output_path)
], check=True)
print(f"Саби збережено у {output_path}")

# === Preview та визначення мови ===
def preview_and_lang(path, fmt):
    lines = []
    if fmt in ("ass", "ssa"):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('Dialogue:'):
                    parts = line.strip().split(',', 9)
                    if len(parts) >= 10:
                        text = parts[9].replace('\\N', ' ').replace('\n', ' ').strip()
                        lines.append(text)
                        if len(lines) >= 5:
                            break
    elif fmt == "srt":
        with open(path, 'r', encoding='utf-8') as f:
            block = []
            for l in f:
                if l.strip() == '':
                    if block:
                        lines.append(' '.join(block))
                        block = []
                        if len(lines) >= 5:
                            break
                elif not l.strip().isdigit() and '-->' not in l:
                    block.append(l.strip())
    else:
        print("Preview не підтримується для цього формату.")
        return
    print("\nПерші 5 реплік:")
    for i, t in enumerate(lines):
        print(f"  {i+1}. {t}")
    langs = []
    for t in lines:
        try:
            langs.append(detect(t))
        except:
            langs.append("unknown")
    from collections import Counter
    lang_counter = Counter(langs)
    main_lang = lang_counter.most_common(1)[0][0]
    if main_lang == "uk":
        print("⚠️  Детектор мови визначив 'uk', але ми ігноруємо це і вважаємо, що мова 'ru' (російська)!")
        main_lang = "ru"
    print(f"🌍 Визначена мова сабів: {main_lang}")

preview_and_lang(output_path, chosen['fmt'].lower()) 