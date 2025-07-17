# 🎨 Стилі Субтитрів

## Доступні Стилі

### 1. Retro Yellow (За замовчуванням)
**Файл**: `magi_pipeline/ass_generator_module/styles/Dialogue.ass`
- **Колір**: Яскраво-жовтий текст
- **Обводка**: Чорна, товщина 4px
- **Тінь**: Чорна, товщина 2px
- **Шрифт**: Arial, 48px
- **Стиль**: Класичний ретро вигляд

### 2. Retro Classic
**Файл**: `magi_pipeline/ass_generator_module/styles/Retro_Classic.ass`
- **Колір**: Яскраво-жовтий текст
- **Обводка**: Чорна, товщина 6px (більш товста)
- **Тінь**: Чорна, товщина 3px
- **Шрифт**: Arial, 50px (більший)
- **Стиль**: Більш виразний, як у старих фільмах

### 3. Retro Vintage
**Файл**: `magi_pipeline/ass_generator_module/styles/Retro_Vintage.ass`
- **Колір**: Яскраво-жовтий текст
- **Обводка**: Чорна, товщина 5px
- **Тінь**: Чорна, товщина 2px
- **Шрифт**: Times New Roman, 52px
- **Стиль**: Вінтажний, елегантний вигляд

## Кольори в ASS форматі

### Основні кольори:
- **Жовтий**: `&H0000FFFF` (BGR формат)
- **Чорний**: `&H00000000`
- **Білий**: `&H00FFFFFF`

### Параметри стилів:
- **PrimaryColour**: Основний колір тексту
- **SecondaryColour**: Допоміжний колір
- **OutlineColour**: Колір обводки
- **BackColour**: Колір фону (з прозорістю)

## Структура стилю

```
Style: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
```

### Параметри:
- **Outline**: Товщина обводки (px)
- **Shadow**: Товщина тіні (px)
- **Alignment**: Позиція (2 = знизу по центру)
- **Bold**: -1 = жирний, 0 = звичайний

## Як використовувати

При запуску пайплайну ви побачите меню вибору стилю:

```
🎨 Available subtitle styles:
1. Retro Yellow (default) - Classic yellow with black outline
2. Retro Classic - Bold yellow with thick black outline
3. Retro Vintage - Times New Roman with classic look
4. Custom style path
```

## Створення власного стилю

1. Створіть файл `.ass` з вашим стилем
2. Використовуйте опцію 4 (Custom style path)
3. Вкажіть шлях до вашого файлу

### Приклад власного стилю:

```ass
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,10,10,10,1
```

## Поради

- **Для темного відео**: Використовуйте жовтий з чорною обводкою
- **Для світлого відео**: Можна змінити на білий з чорною обводкою
- **Для кращої читабельності**: Збільште товщину обводки (Outline)
- **Для ретро вигляду**: Використовуйте Times New Roman або Impact 