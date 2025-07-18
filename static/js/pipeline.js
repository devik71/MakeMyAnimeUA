/**
 * 🎬 MakeMyAnimeUA — JavaScript для головного пайплайну
 */

// Глобальні змінні
let currentSessionId = null;
let isProcessing = false;
let statusCheckInterval = null;

// DOM елементи
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const stepUpload = document.getElementById('stepUpload');
const stepAnalysis = document.getElementById('stepAnalysis');
const stepConfig = document.getElementById('stepConfig');
const stepProcess = document.getElementById('stepProcess');
const stepComplete = document.getElementById('stepComplete');

// Ініціалізація
document.addEventListener('DOMContentLoaded', function() {
    initializeUploadArea();
    initializeFormHandlers();
});

/**
 * Ініціалізація drag & drop для завантаження файлів
 */
function initializeUploadArea() {
    if (!uploadArea || !fileInput) return;

    // Drag & drop events
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('dragenter', handleDragEnter);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    
    // Click to upload
    uploadArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
}

function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
}

function handleDragEnter(e) {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    if (!uploadArea.contains(e.relatedTarget)) {
        uploadArea.classList.remove('drag-over');
    }
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processFileUpload(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        processFileUpload(files[0]);
    }
}

/**
 * Обробка завантаження файлу
 */
async function processFileUpload(file) {
    if (!validateFile(file)) return;
    
    showSpinner('Завантаження файлу...');
    
    const formData = new FormData();
    formData.append('video', file);
    
    try {
        console.log('📤 Початок завантаження файлу:', file.name, 'Розмір:', file.size);
        
        const response = await fetch('/upload_video', {
            method: 'POST',
            body: formData
        });
        
        console.log('📡 Отримано відповідь від сервера:', response.status, response.statusText);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ Помилка сервера:', errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        console.log('📋 Content-Type:', contentType);
        
        if (!contentType || !contentType.includes('application/json')) {
            const textResponse = await response.text();
            console.error('❌ Сервер повернув не JSON:', textResponse.substring(0, 500));
            throw new Error('Сервер повернув не JSON відповідь');
        }
        
        const result = await response.json();
        console.log('✅ Отримано JSON:', result);
        
        if (result.error) {
            console.log('❌ Знайдено помилку в result:', result.error);
            showError(result.error);
            return;
        }
        
        // Успішне завантаження
        console.log('🚀 Починаємо обробку успішного завантаження...');
        console.log('📋 Session ID:', result.session_id);
        
        currentSessionId = result.session_id;
        
        console.log('📋 Викликаємо showStep(2)...');
        showStep('2');  // step2 - аналіз
        
        console.log('📊 Викликаємо populateAnalysisData...');
        populateAnalysisData(result);
    } catch (error) {
        console.error('❌ Детальна помилка завантаження:', error);
        console.error('❌ Stack trace:', error.stack);
        showError('Помилка завантаження: ' + error.message);
    } finally {
        hideSpinner();
    }
}

/**
 * Заповнення даних аналізу
 */
function populateAnalysisData(data) {
    console.log('📊 Заповнюємо дані аналізу:', data);
    
    // Показуємо контент аналізу
    const analysisContent = document.getElementById('analysisContent');
    if (analysisContent) {
        analysisContent.classList.remove('hidden');
        console.log('✅ Показано analysisContent');
    }
    
    // Заповнюємо інформацію про відео
    const videoInfo = document.getElementById('videoInfo');
    if (videoInfo && data.analysis && data.analysis.video_info) {
        const info = data.analysis.video_info;
        const sizeInMB = info.size ? (info.size / 1024 / 1024).toFixed(2) + ' MB' : 'Невідомо';
        videoInfo.innerHTML = `
            <p><strong>📁 Файл:</strong> ${info.filename || 'Невідомо'}</p>
            <p><strong>📊 Розмір:</strong> ${sizeInMB}</p>
        `;
    }
    
    // Заповнюємо аудіо дорожки
    const audioStreams = document.getElementById('audioStreams');
    if (audioStreams && data.analysis && data.analysis.audio_streams) {
        audioStreams.innerHTML = '';
        data.analysis.audio_streams.forEach((stream, index) => {
            const label = document.createElement('label');
            label.className = 'radio-item';
            label.innerHTML = `
                <input type="radio" name="audioSource" value="audio_${index}" ${index === 0 ? 'checked' : ''}>
                <span>🎵 Дорожка ${index + 1}: ${stream.language || 'невідома мова'} (${stream.codec || 'невідомий кодек'})</span>
            `;
            audioStreams.appendChild(label);
        });
    }
    
    // Заповнюємо доступні моделі Whisper
    if (data.whisper_models && data.whisper_models.models) {
        const whisperSelect = document.getElementById('whisperModel');
        if (whisperSelect) {
            whisperSelect.innerHTML = '';
            data.whisper_models.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = `${model.name} (${model.size})`;
                if (model.name === data.whisper_models.recommended) option.selected = true;
                whisperSelect.appendChild(option);
            });
        }
    }
    
    // Заповнюємо стилі субтитрів
    if (data.subtitle_styles) {
        const stylesContainer = document.getElementById('subtitleStyles');
        if (stylesContainer) {
            stylesContainer.innerHTML = '';
            data.subtitle_styles.forEach((style, index) => {
                const label = document.createElement('label');
                label.className = 'radio-item';
                label.innerHTML = `
                    <input type="radio" name="subtitleStyle" value="${style.name}" ${index === 0 ? 'checked' : ''}>
                    <span>${style.name}</span>
                `;
                stylesContainer.appendChild(label);
            });
        }
    }
}

/**
 * Валідація файлу
 */
function validateFile(file) {
    const allowedTypes = ['video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska'];
    const maxSize = 2 * 1024 * 1024 * 1024; // 2GB
    
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov|mkv)$/i)) {
        showError('Підтримуються тільки відео файли: MP4, AVI, MOV, MKV');
        return false;
    }
    
    if (file.size > maxSize) {
        showError('Файл занадто великий. Максимальний розмір: 2GB');
        return false;
    }
    
    return true;
}

/**
 * Аналіз відео
 */
async function analyzeVideo(sessionId) {
    showSpinner('Аналіз відео файлу...');
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayAnalysisResults(result.analysis);
            showStep('config');
        } else {
            showError(result.error || 'Помилка аналізу відео');
        }
    } catch (error) {
        showError('Помилка аналізу: ' + error.message);
    } finally {
        hideSpinner();
    }
}

/**
 * Відображення результатів аналізу
 */
function displayAnalysisResults(analysis) {
    const container = document.getElementById('analysisResults');
    if (!container) return;
    
    let html = '<div class="analysis-card">';
    html += '<h4>📹 Інформація про відео</h4>';
    html += `<p><strong>Тривалість:</strong> ${analysis.duration || 'Невідомо'}</p>`;
    html += `<p><strong>Роздільність:</strong> ${analysis.resolution || 'Невідомо'}</p>`;
    html += `<p><strong>Розмір файлу:</strong> ${analysis.file_size || 'Невідомо'}</p>`;
    
    // Аудіо дорожки
    if (analysis.audio_tracks && analysis.audio_tracks.length > 0) {
        html += '<h5>🎵 Аудіо дорожки:</h5>';
        html += '<ul>';
        analysis.audio_tracks.forEach((track, index) => {
            html += `<li>Дорожка ${index + 1}: ${track.language || 'Невідомо'} (${track.codec || 'Невідомо'})</li>`;
        });
        html += '</ul>';
    }
    
    // Субтитри
    if (analysis.subtitle_tracks && analysis.subtitle_tracks.length > 0) {
        html += '<h5>📝 Вбудовані субтитри:</h5>';
        html += '<ul>';
        analysis.subtitle_tracks.forEach((sub, index) => {
            html += `<li>Субтитри ${index + 1}: ${sub.language || 'Невідомо'} (${sub.format || 'Невідомо'})</li>`;
        });
        html += '</ul>';
    }
    
    // Зовнішні субтитри
    if (analysis.external_subtitles && analysis.external_subtitles.length > 0) {
        html += '<h5>📄 Зовнішні субтитри:</h5>';
        html += '<ul>';
        analysis.external_subtitles.forEach(sub => {
            html += `<li>${sub.filename} (${sub.language || 'Невідомо'})</li>`;
        });
        html += '</ul>';
    }
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Ініціалізація обробників форм
 */
function initializeFormHandlers() {
    const configForm = document.getElementById('configForm');
    if (configForm) {
        configForm.addEventListener('submit', handleConfigSubmit);
    }
    
    // Вибір движка перекладу
    const translationEngine = document.querySelector('input[name="translation_engine"]');
    if (translationEngine) {
        document.querySelectorAll('input[name="translation_engine"]').forEach(radio => {
            radio.addEventListener('change', handleEngineChange);
        });
    }
}

function handleEngineChange(e) {
    const deeplSection = document.getElementById('deeplSection');
    if (deeplSection) {
        if (e.target.value === 'deepl') {
            deeplSection.style.display = 'block';
        } else {
            deeplSection.style.display = 'none';
        }
    }
}

/**
 * Обробка відправки конфігурації
 */
async function handleConfigSubmit(e) {
    e.preventDefault();
    
    if (!currentSessionId) {
        showError('Сесія втрачена. Перезавантажте файл.');
        return;
    }
    
    const formData = new FormData(e.target);
    const config = Object.fromEntries(formData.entries());
    config.session_id = currentSessionId;
    
    showSpinner('Запуск обробки...');
    showStep('process');
    
    try {
        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (result.success) {
            isProcessing = true;
            startStatusChecking();
        } else {
            showError(result.error || 'Помилка запуску обробки');
        }
    } catch (error) {
        showError('Помилка запуску: ' + error.message);
    } finally {
        hideSpinner();
    }
}

/**
 * Перевірка статусу обробки
 */
function startStatusChecking() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(async () => {
        if (!isProcessing || !currentSessionId) {
            clearInterval(statusCheckInterval);
            return;
        }
        
        try {
            const response = await fetch(`/status/${currentSessionId}`);
            const result = await response.json();
            
            updateProgress(result);
            
            if (result.status === 'completed') {
                isProcessing = false;
                clearInterval(statusCheckInterval);
                showStep('complete');
                displayResults(result);
            } else if (result.status === 'error') {
                isProcessing = false;
                clearInterval(statusCheckInterval);
                showError(result.error || 'Помилка обробки');
            }
        } catch (error) {
            console.error('Помилка перевірки статусу:', error);
        }
    }, 2000);
}

/**
 * Оновлення прогресу
 */
function updateProgress(status) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const processingLog = document.getElementById('processingLog');
    
    if (progressBar && status.progress !== undefined) {
        progressBar.style.width = `${status.progress}%`;
    }
    
    if (progressText && status.stage) {
        progressText.textContent = status.stage;
    }
    
    if (processingLog && status.log) {
        processingLog.innerHTML = status.log.map(entry => 
            `<div class="log-entry ${entry.level}">[${entry.timestamp}] ${entry.message}</div>`
        ).join('');
        processingLog.scrollTop = processingLog.scrollHeight;
    }
}

/**
 * Відображення результатів
 */
function displayResults(result) {
    const container = document.getElementById('results');
    if (!container) return;
    
    let html = '<div class="results-card">';
    html += '<h4>✅ Обробка завершена!</h4>';
    
    if (result.output_files) {
        html += '<h5>📁 Створені файли:</h5>';
        html += '<ul>';
        result.output_files.forEach(file => {
            html += `<li><a href="/download/${file.id}" target="_blank">${file.name}</a></li>`;
        });
        html += '</ul>';
    }
    
    if (result.edit_session_id) {
        html += '<div class="edit-section">';
        html += '<h5>✏️ Редагування перекладу</h5>';
        html += '<p>Хочете відредагувати переклад перед фінальним рендерингом?</p>';
        html += `<button onclick="openEditor('${result.edit_session_id}')" class="btn btn-secondary">📝 Відкрити редактор</button>`;
        html += '</div>';
    }
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Відкриття редактора перекладу
 */
function openEditor(editSessionId) {
    const editorUrl = `/editor?session=${editSessionId}&return_to=main_pipeline`;
    window.open(editorUrl, '_blank');
}

/**
 * Управління кроками
 */
function showStep(stepNumber) {
    console.log('📋 Показуємо крок:', stepNumber);
    
    // Сховати всі кроки
    for (let i = 1; i <= 5; i++) {
        const step = document.getElementById(`step${i}`);
        if (step) {
            step.style.display = 'none';
            step.classList.remove('active');
            step.classList.add('disabled');
        }
    }
    
    // Показати потрібний крок
    const targetStepId = `step${stepNumber}`;
    console.log('🔍 Шукаємо елемент з ID:', targetStepId);
    
    const targetStep = document.getElementById(targetStepId);
    if (targetStep) {
        console.log('✅ Елемент знайдено, показуємо крок');
        targetStep.style.display = 'block';
        targetStep.classList.remove('disabled');
        targetStep.classList.add('active');
        targetStep.scrollIntoView({ behavior: 'smooth' });
    } else {
        console.error('❌ Елемент не знайдено:', targetStepId);
    }
}

/**
 * Утиліти
 */
function showSpinner(message = 'Обробка...') {
    const spinner = document.getElementById('spinner');
    const spinnerText = document.getElementById('spinnerText');
    
    if (spinner) {
        spinner.style.display = 'flex';
        if (spinnerText) spinnerText.textContent = message;
    }
}

function hideSpinner() {
    const spinner = document.getElementById('spinner');
    if (spinner) {
        spinner.style.display = 'none';
    }
}

function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    if (errorContainer) {
        errorContainer.innerHTML = `
            <div class="alert alert-error">
                <span class="alert-icon">❌</span>
                <span class="alert-message">${message}</span>
                <button class="alert-close" onclick="this.parentElement.style.display='none'">×</button>
            </div>
        `;
        errorContainer.style.display = 'block';
    } else {
        alert(message);
    }
}

function showSuccess(message) {
    const errorContainer = document.getElementById('errorContainer');
    if (errorContainer) {
        errorContainer.innerHTML = `
            <div class="alert alert-success">
                <span class="alert-icon">✅</span>
                <span class="alert-message">${message}</span>
                <button class="alert-close" onclick="this.parentElement.style.display='none'">×</button>
            </div>
        `;
        errorContainer.style.display = 'block';
    }
}console.log('🕐 JavaScript файл завантажено:', new Date().toISOString());
