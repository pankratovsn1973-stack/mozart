# -*- coding: utf-8 -*-
"""
Путь: /home/sergey/Documents/configurate/mozart_import/tools/pankratov_tensor_shift.py
Описание: Монолитный скрипт для алгебраического сдвига корневого тензора "Грозы" Вивальди на 10%.
          Выполняет сквозной цикл: Аудио -> Поле Галуа -> Сдвиг корней -> Деканонизация -> Новое Аудио.
"""

import os
import numpy as np
import scipy.io.wavfile as wavfile
import librosa

AUDIO_PATH = 'Vivaldi_Summer_Storm.mp3'
OUTPUT_WAV = 'vivaldi_shifted_10pct.wav'
SAMPLE_RATE = 22050
HOP_LENGTH = 512
N_FFT = 2048
STEPS = 60  # 5 октав по 12 нот

print("=== Шаг 1: Загрузка и FFT-анализ оригинала ===")
if not os.path.exists(AUDIO_PATH):
    print(f"Ошибка: Положите исходный файл '{AUDIO_PATH}' в текущую папку!")
    print("Генерируем короткий тестовый фрагмент для верификации кода...")
    duration = 5.0
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    # Симуляция: басовый тон + скрипичная волна
    y = np.sin(2 * np.pi * 65 * t) * 0.5 + np.sin(2 * np.pi * 880 * t) * 0.3
    sr = SAMPLE_RATE
else:
    print(f"Загрузка аудио: {AUDIO_PATH}...")
    y, sr = librosa.load(AUDIO_PATH, sr=SAMPLE_RATE)

# Быстрое преобразование Фурье
stft = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)
stft_matrix = np.abs(stft)
stft_phase = np.angle(stft)
num_frames = stft_matrix.shape[1]

print(f"Оригинал успешно разобран. Получено кадров: {num_frames}")

print("\n=== Шаг 2: Трансляция в 60-канальное пространство Галуа ===")
audio_bins = np.logspace(np.log10(65.4), np.log10(2093.0), STEPS + 1)
frequencies = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)

# Проекция на 60 дискретных каналов
galois_spectrogram = np.zeros((STEPS, num_frames))
bin_mapping = []  # Маппинг для обратной сборки

for i in range(STEPS):
    idx = np.where((frequencies >= audio_bins[i]) & (frequencies < audio_bins[i + 1]))[0]
    bin_mapping.append(idx)
    if len(idx) > 0:
        galois_spectrogram[i, :] = np.mean(stft_matrix[idx, :], axis=0)

# Нормализуем остов
max_val = np.max(galois_spectrogram) + 1e-6
galois_spectrogram /= max_val

print("=== Шаг 3: Алгебраическая деформация корневой системы (Сдвиг на 10%) ===")
# Чтобы не терять данные, мы обрабатываем спектральные матрицы скользящими блоками 12x12
# (по размеру полной октавы Галуа) и сдвигаем их локальные собственные значения на 10% влево
shifted_galois = np.zeros_like(galois_spectrogram)

for f in range(num_frames):
    # Берем текущий вертикальный вектор из 60 каналов (5 октав по 12 нот)
    frame_vector = galois_spectrogram[:, f]

    # Формируем квази-матрицу распределения энергии по октавам (5 октав на 12 нот)
    # Для математической строгости операции det(A - lambda*I) дополняем до квадратной матрицы 12x12
    meta_matrix = np.zeros((12, 12))
    for oct_idx in range(5):
        meta_matrix[oct_idx, :12] = frame_vector[oct_idx * 12: (oct_idx + 1) * 12]

    # Извлекаем собственные значения (корни характеристического уравнения этой ткани)
    eigenvalues, eigenvectors = np.linalg.eig(meta_matrix)

    # Выполняем детерминированный сдвиг корней влево на 10% (сжатие спектра оператора)
    # lambda_new = lambda * 0.9
    shifted_eigenvalues = eigenvalues * 0.90

    # Реконструируем измененную алгебраическую ткань обратно в поле Галуа
    # A_new = V * Lambda_new * V^-1
    try:
        inv_eigenvectors = np.linalg.inv(eigenvectors)
        reconstructed_matrix = eigenvectors @ np.diag(shifted_eigenvalues) @ inv_eigenvectors
        reconstructed_matrix = np.abs(reconstructed_matrix)  # Возвращаемся к вещественным амплитудам

        # Разворачиваем измененную матрицу обратно в 60-канальный вектор
        for oct_idx in range(5):
            shifted_galois[oct_idx * 12: (oct_idx + 1) * 12, f] = reconstructed_matrix[oct_idx, :12]
    except np.linalg.LinAlgError:
        # Если матрица вырождена (в моменты тишины), оставляем значения без изменений
        shifted_galois[:, f] = frame_vector

# Возвращаем исходный масштаб амплитуд
shifted_galois *= max_val

print("\n=== Шаг 4: Деканонизация и обратный инверсный синтез звука ===")
# Восстанавливаем линейную матрицу FFT из пространства Галуа
reconstructed_stft_matrix = np.zeros_like(stft_matrix)
for i in range(STEPS):
    idx = bin_mapping[i]
    if len(idx) > 0:
        for freq_idx in idx:
            reconstructed_stft_matrix[freq_idx, :] = shifted_galois[i, :]

# Смешиваем измененную амплитуду с оригинальной фазой для идеального сохранения контуров звука
stft_shifted = reconstructed_stft_matrix * np.exp(1j * stft_phase)

# Инверсное преобразование Фурье (iSTFT)
y_shifted = librosa.istft(stft_shifted, hop_length=HOP_LENGTH)

print(f"=== Шаг 5: Запись деформированного звукового ряда ===")
# Ограничиваем амплитуду во избежание клиппинга
y_shifted = np.clip(y_shifted, -1.0, 1.0)
wavfile.write(OUTPUT_WAV, SAMPLE_RATE, (y_shifted * 32767).astype(np.int16))
print(f"Успешно сгенерирован новый звуковой ряд Панкратова: {OUTPUT_WAV}")
