# -*- coding: utf-8 -*-
# Путь: /home/sergey/Documents/configurate/mozart_import/tools/frobenius_sound_generator.py

import os
import numpy as np
import scipy.io.wavfile as wavfile
import librosa

# --- Математический аппарат поля Галуа ---
P = 257  # Простой модуль поля GF(p)
E = 7  # Степень прямого кодирования Фробениуса


def inverse_modulo(e, m):
    g, x, y = ext_gcd(e, m)
    return x % m


def ext_gcd(a, b):
    if a == 0: return b, 0, 1
    gcd, x1, y1 = ext_gcd(b % a, a)
    return gcd, y1 - (b // a) * x1, x1


# Идеальный математический ключ
D_perfect = inverse_modulo(E, P - 1)

# Вносим нелинейную тензорную асимметрию: смещаем обратную степень на ~10%
# Это заставит решетку Галуа "искривиться" при обратном отображении в звук
D_shifted = int(D_perfect * 0.90)
if D_shifted % 2 == 0: D_shifted += 1  # Удерживаем нечетность для сохранения знака

print(f"=== Параметры нелинейного генератора ===")
print(f"Модуль поля GF(p): {P}")
print(f"Прямой автоморфизм (E): {E}")
print(f"Идеальный декодер (D): {D_perfect}")
print(f"Асимметричный декодер Панкратова (D_shifted): {D_shifted}\n")

AUDIO_PATH = 'Vivaldi_Summer_Storm.mp3'
OUTPUT_WAV = 'vivaldi_frobenius_deformed.wav'
SAMPLE_RATE = 22050
HOP_LENGTH = 512
N_FFT = 2048

# 1. Загрузка оригинального звука
if os.path.exists(AUDIO_PATH):
    print(f"Загрузка оригинала: {AUDIO_PATH}")
    y, sr = librosa.load(AUDIO_PATH, sr=SAMPLE_RATE)
else:
    print("Файл оригинала не найден. Генерируем 5 секунд оркестровой симуляции...")
    sr = SAMPLE_RATE
    t = np.linspace(0, 5.0, int(5.0 * sr), endpoint=False)
    y = np.sin(2 * np.pi * 65 * t) * 0.4 + np.sin(2 * np.pi * 880 * t) * 0.3

# STFT Анализ
stft = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)
stft_matrix = np.abs(stft)
stft_phase = np.angle(stft)

# Квантование вещественных амплитуд в дискретные элементы поля Галуа [0, P-1]
max_amp = np.max(stft_matrix) + 1e-6
gf_matrix = np.floor((stft_matrix / max_amp) * (P - 1)).astype(np.int64)

# =========================================================================
# МАТЕМАТИЧЕСКИЙ СДВИГ В ПОЛЕ ГАЛУА
# =========================================================================
print("Запуск сквозной тензорной деформации...")
gf_deformed = np.zeros_like(gf_matrix)

for i in range(gf_matrix.shape[0]):
    for j in range(gf_matrix.shape[1]):
        val = int(gf_matrix[i, j])

        # Шаг А: Прямой сдвиг Фробениуса (уходим в хаос решетки)
        encrypted_val = pow(val, E, P)

        # Шаг Б: Обратное декодирование СМЕЩЕННОЙ степенью
        # Математически: x -> (x^E)^D_shifted mod P = x^(E * D_shifted) mod P
        # Из-за нарушения теоремы Эйлера, близкие числа разойдутся нелинейно
        deformed_val = pow(encrypted_val, D_shifted, P)

        gf_deformed[i, j] = deformed_val

# =========================================================================
# СИНТЕЗ НОВОГО ЗВУКОВОГО РЯДА
# =========================================================================
print("Реконструкция измененной ткани в физический звук...")

# Перевод дискретной матрицы Галуа обратно в непрерывные амплитуды
stft_deformed_matrix = (gf_deformed / (P - 1)) * max_amp

# Замыкаем измененную амплитуду на оригинальную фазу
stft_final = stft_deformed_matrix * np.exp(1j * stft_phase)

# Инверсное преобразование Фурье (iSTFT)
y_new = librosa.istft(stft_final, hop_length=HOP_LENGTH)
y_new = np.clip(y_new, -1.0, 1.0)

# Запись нового звукового ряда
wavfile.write(OUTPUT_WAV, SAMPLE_RATE, (y_new * 32767).astype(np.int16))
print(f"\n=== Новый звуковой ряд успешно создан: {OUTPUT_WAV} ===")
