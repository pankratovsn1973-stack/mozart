# -*- coding: utf-8 -*-
import os
import sys
import numpy as np
import librosa
import colorsys
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Отключаем звук pygame при импорте, чтобы не спамить в консоль
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


def get_galois_color(sound_step):
    """
    Маппинг звука (1-60) в RGB по циклической системе (модуль 12).
    Нота определяет Тон (Hue), а октава — Светлоту (Lightness) и Насыщенность (Saturation).
    """
    idx = sound_step - 1
    octave = idx // 12  # 0 до 4
    note = idx % 12  # 0 до 11

    # Тон крутится по кругу (нота До всегда в начале/красная)
    hue = note / 12.0

    # Управляем яркостью/насыщенностью в зависимости от октавы
    if octave == 0:  # Суб-бас (1-я октава шкалы)
        saturation = 1.0;
        lightness = 0.20  # Густой бордовый
    elif octave == 1:  # Бас
        saturation = 1.0;
        lightness = 0.40  # Насыщенный темный
    elif octave == 2:  # Середина
        saturation = 1.0;
        lightness = 0.55  # Чистый яркий спектр
    elif octave == 3:  # Верхняя середина
        saturation = 0.75;
        lightness = 0.70  # Пастельный (размытый белым)
    else:  # Самый верх (5-я октава шкалы)
        saturation = 0.40;
        lightness = 0.85  # Неоновый светящийся

    # Преобразуем HSL в RGB (0.0 - 1.0)
    return colorsys.hls_to_rgb(hue, lightness, saturation)


# --- 1. Константы и генерация сетки цветов ---
STEPS = 60
scale_colors = [get_galois_color(i + 1) for i in range(STEPS)]

AUDIO_PATH = 'Vivaldi_Summer_Storm.mp3'
SAMPLE_RATE = 22050
HOP_LENGTH = 512
N_FFT = 2048

print("=== Анализ и подготовка аудио ===")

# --- 2. Загрузка реального файла или генерация чистой симуляции ---
if os.path.exists(AUDIO_PATH):
    print(f"Файл {AUDIO_PATH} найден. Загрузка и анализ...")
    y, sr = librosa.load(AUDIO_PATH, sr=SAMPLE_RATE)
    # Сохраняем временный wav для pygame (mp3 может некорректно стримиться на Linux)
    PLAYBACK_FILE = 'temp_playback.wav'
    import scipy.io.wavfile as wavfile

    wavfile.write(PLAYBACK_FILE, SAMPLE_RATE, (y * 32767).astype(np.int16))
else:
    print(f"Файл '{AUDIO_PATH}' не найден. Генерируем аудио-симуляцию Грозы...")
    duration = 15.0  # 15 секунд демонстрации
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)

    # Моделируем "Грозу": раскаты грома (50-80 Гц) + скрипичные пассажи (600-1500 Гц)
    y = np.zeros_like(t)
    # Гром (периодические вспышки баса)
    y += np.sin(2 * np.pi * 55 * t) * 0.4 * (np.sin(2 * np.pi * 0.2 * t) ** 2)
    # Скрипки (быстрые волны частот)
    violin_freq = 880 + 400 * np.sin(2 * np.pi * 1.5 * t)
    y += np.sin(2 * np.pi * violin_freq * t) * 0.3

    sr = SAMPLE_RATE
    PLAYBACK_FILE = 'temp_simulation.wav'
    import scipy.io.wavfile as wavfile

    wavfile.write(PLAYBACK_FILE, SAMPLE_RATE, (y * 32767).astype(np.int16))

# --- 3. Быстрое преобразование Фурье (FFT) ---
stft = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH))
frequencies = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)

# Распределяем логарифмически 5 октав звука (от До большой октавы 65 Гц до До 4-й 2093 Гц)
audio_bins = np.logspace(np.log10(65.4), np.log10(2093.0), STEPS + 1)

light_spectrogram = []
for i in range(STEPS):
    idx = np.where((frequencies >= audio_bins[i]) & (frequencies < audio_bins[i + 1]))[0]
    if len(idx) > 0:
        light_spectrogram.append(np.mean(stft[idx, :], axis=0))
    else:
        light_spectrogram.append(np.zeros(stft.shape[1]))

light_spectrogram = np.array(light_spectrogram)
# Нормализуем данные для корректного отображения яркости
light_spectrogram = light_spectrogram / (np.max(light_spectrogram) + 1e-6)

# --- 4. Настройка интерфейса воспроизведения (Pygame) ---
pygame.mixer.init(frequency=sr, size=-16, channels=1)
pygame.mixer.music.load(PLAYBACK_FILE)

# --- 5. Построение окон визуализации (Matplotlib) ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), gridspec_kw={'width_ratios': [1, 3]})
fig.suptitle("Световая шкала Галуа (Цикл 12 нот) — Визуализация 'Грозы'", fontsize=14)

# Левая панель: Эквалайзер нот
bars = ax1.barh(range(STEPS), np.zeros(STEPS), color=scale_colors, edgecolor='none')
ax1.set_xlim(0, 1)
ax1.set_title("Спектр нот (Текущий кадр)")
ax1.set_ylabel("5 октав (60 шагов) -> Каждые 12 шагов цвет зацикливается")
ax1.set_xticks([])

# Правая панель: Поток времени
DISPLAY_FRAMES = 80
canvas = np.zeros((STEPS, DISPLAY_FRAMES, 3))
img_plot = ax2.imshow(canvas, aspect='auto', origin='lower')
ax2.set_title("Световой поток времени")
ax2.set_xlabel("<- История  |  Текущий момент ->")
ax2.set_yticks([])

# Флаг для синхронного старта трека
music_started = False


def update_frame(frame):
    global music_started, canvas

    # Запускаем трек ровно в момент отрисовки первого кадра
    if not music_started:
        pygame.mixer.music.play()
        music_started = True

    # Синхронизация: привязываем кадр анимации к реальной позиции аудио трека
    pos_ms = pygame.mixer.music.get_pos()
    if pos_ms < 0:
        return [img_plot]

    # Вычисляем индекс кадра на основе времени воспроизведения
    current_frame = int((pos_ms / 1000.0) * sr / HOP_LENGTH)
    if current_frame >= light_spectrogram.shape[1]:
        return [img_plot]

    current_data = light_spectrogram[:, current_frame]

    # 1. Обновляем левый вертикальный эквалайзер
    for i, bar in enumerate(bars):
        bar.set_width(current_data[i])

    # 2. Обновляем правый таймлайн (сдвиг истории влево)
    canvas = np.roll(canvas, -1, axis=1)

    # Записываем новые цвета в правый край матрицы экрана
    for i in range(STEPS):
        amplitude = current_data[i]
        # Применяем нелинейную яркость, чтобы слабые звуки тоже были видны
        intensity = np.tanh(amplitude * 2.5)

        canvas[i, -1, 0] = scale_colors[i][0] * intensity  # R
        canvas[i, -1, 1] = scale_colors[i][1] * intensity  # G
        canvas[i, -1, 2] = scale_colors[i][2] * intensity  # B

    img_plot.set_data(canvas)
    return [img_plot]


# Вычисляем интервал между кадрами в миллисекундах для анимации
frame_interval = int((HOP_LENGTH / float(sr)) * 1000)

ani = animation.FuncAnimation(
    fig, update_frame, frames=light_spectrogram.shape[1],
    interval=frame_interval, blit=False, repeat=False
)

plt.tight_layout()


# Перед показом окон убеждаемся, что при закрытии графики звук выключится
def on_close(event):
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    # Удаляем временные файлы
    if os.path.exists('temp_playback.wav'): os.remove('temp_playback.wav')
    if os.path.exists('temp_simulation.wav'): os.remove('temp_simulation.wav')


fig.canvas.mpl_connect('close_event', on_close)

plt.show()
