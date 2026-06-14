# -*- coding: utf-8 -*-
# Путь: /home/sergey/Documents/configurate/mozart_import/tools/dump_light_stream.py
# Описание: Скрипт компактного экспорта светового потока в текст (1 символ = 1 кадр).

import os
import numpy as np
import librosa

AUDIO_PATH = 'Vivaldi_Summer_Storm.mp3'
OUTPUT_TXT = 'vivaldi_compressed_stream.txt'
SAMPLE_RATE = 22050
HOP_LENGTH = 512
N_FFT = 2048
STEPS = 60

# Алфавит из 64 символов для кодирования уровней громкости (0-63)
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!/"
CHAR_SILENCE = "."  # Отдельный символ для абсолютной тишины


def val_to_char(val):
    """Кодирует float от 0.0 до 1.0 в один символ."""
    if val <= 0.005:  # Порог тишины
        return CHAR_SILENCE
    idx = int(val * 63)
    idx = max(0, min(63, idx))
    return ALPHABET[idx]


print("=== Запуск компактного дампа светового потока ===")

if os.path.exists(AUDIO_PATH):
    print(f"Анализ файла: {AUDIO_PATH}")
    y, sr = librosa.load(AUDIO_PATH, sr=SAMPLE_RATE)
else:
    print("Файл не найден. Генерируем 5 секунд симуляции...")
    duration = 5.0
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    y = np.sin(2 * np.pi * 55 * t) * 0.4 + np.sin(2 * np.pi * 880 * t) * 0.3
    sr = SAMPLE_RATE

# Спектральный анализ
stft = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH))
frequencies = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
num_frames = stft.shape[1]

audio_bins = np.logspace(np.log10(65.4), np.log10(2093.0), STEPS + 1)
light_spectrogram = []

for i in range(STEPS):
    idx = np.where((frequencies >= audio_bins[i]) & (frequencies < audio_bins[i + 1]))[0]
    if len(idx) > 0:
        light_spectrogram.append(np.mean(stft[idx, :], axis=0))
    else:
        light_spectrogram.append(np.zeros(num_frames))

light_spectrogram = np.array(light_spectrogram)
light_spectrogram = light_spectrogram / (np.max(light_spectrogram) + 1e-6)

print(f"Запись компактных данных в файл: {OUTPUT_TXT}...")
with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
    f.write("# MOZART Compressed Galois Stream\n")
    f.write(f"# Channels: {STEPS}, Frames: {num_frames}\n")
    f.write("# Dictionary: . = тишина, 0-9 = тихо, a-z = среднее, A-Z = громко, ! / = пик\n")

    for channel_idx in range(STEPS):
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octave = channel_idx // 12
        note_name = notes[channel_idx % 12]

        row_values = light_spectrogram[channel_idx, :]
        # Кодируем каждый кадр в один символ и склеиваем в сплошную строку
        row_chars = "".join([val_to_char(v) for v in row_values])

        f.write(f"CH{channel_idx + 1:02d}_{note_name}{octave}:{row_chars}\n")

print("=== Компактный дамп успешно завершен ===")
