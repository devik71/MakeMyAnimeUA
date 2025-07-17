# GPU Setup для Whisper Транскрибації

## Перевірка GPU підтримки

Спочатку запустіть скрипт перевірки:

```bash
python scripts/check_gpu.py
```

## Встановлення PyTorch з CUDA підтримкою

### Для Windows:

1. **Перевірте версію CUDA** (якщо встановлена):
   ```bash
   nvidia-smi
   ```

2. **Встановіть PyTorch з CUDA**:
   ```bash
   # Для CUDA 11.8
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
   
   # Для CUDA 12.1
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

### Для Linux:

```bash
# Для CUDA 11.8
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Для CUDA 12.1  
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## Перевірка встановлення

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
```

## Моделі Whisper та GPU пам'ять

| Модель | Розмір | GPU пам'ять | Якість | Швидкість |
|--------|--------|-------------|--------|-----------|
| tiny   | 39 MB  | 1 GB        | Низька | Дуже швидка |
| base   | 74 MB  | 1 GB        | Хороша | Швидка |
| small  | 244 MB | 2 GB        | Краща | Середня |
| medium | 769 MB | 4 GB        | Найкраща | Повільна |
| large  | 1550 MB| 8 GB        | Найвища | Дуже повільна |

## Автоматичний вибір моделі

Програма автоматично вибирає оптимальну модель залежно від доступної GPU пам'яті:

- **≥8 GB**: large модель
- **≥4 GB**: medium модель  
- **≥2 GB**: small модель
- **<2 GB**: base модель
- **CPU**: base модель

## Вирішення проблем

### Помилка "CUDA out of memory"

1. Зменшіть розмір моделі
2. Закрийте інші програми, що використовують GPU
3. Використовуйте CPU режим

### Помилка "CUDA not available"

1. Перевірте встановлення CUDA драйверів
2. Перевстановіть PyTorch з CUDA підтримкою
3. Перезавантажте систему

### Повільна транскрибація

1. Використовуйте GPU замість CPU
2. Виберіть меншу модель (tiny/base)
3. Перевірте, чи не завантажена GPU іншими програмами

## Оптимізація продуктивності

1. **Використовуйте fp16** (автоматично на GPU)
2. **Закрийте інші програми** під час транскрибації
3. **Використовуйте SSD** для швидкого доступу до файлів
4. **Достатня RAM** (рекомендується 8+ GB)

## Приклади команд

```bash
# Перевірка GPU
python scripts/check_gpu.py

# Запуск з автоматичним вибором моделі
python scripts/run_pipeline.py

# Примусове використання CPU (якщо є проблеми з GPU)
CUDA_VISIBLE_DEVICES="" python scripts/run_pipeline.py
``` 