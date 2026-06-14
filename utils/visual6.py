# -*- coding: utf-8 -*-
# Путь: /home/sergey/Documents/configurate/mozart_import/tools/pankratov_hybrid_crypto.py
# Описание: Гибридный каскад Панкратова с тотальной модуляцией спектральной матрицы.

import os
import numpy as np
import scipy.io.wavfile as wavfile
import librosa

P = 257
E = 7
SECRET_TEXT = "Здравствуй мир. 123456"


def inverse_modulo(e, m):
    g, x, y = ext_gcd(e, m)
    return x % m


def ext_gcd(a, b):
    if a == 0: return b, 0, 1
    gcd, x1, y1 = ext_gcd(b % a, a)
    return gcd, y1 - (b // a) * x1, x1


D = inverse_modulo(E, P - 1)

print("=== Гибридный Конструктор Панкратова (Тотальная модуляция) ===")

AUDIO_PATH = 'Vivaldi_Summer_Storm.mp3'
OUTPUT_ANONYMOUS = 'vivaldi_anonymous_midi_like.wav'
OUTPUT_RESTORED = 'vivaldi_authentic_restored.wav'
OUTPUT_BROKEN = 'vivaldi_broken_key_error.wav'
SAMPLE_RATE = 22050
HOP_LENGTH = 512
N_FFT = 2048

if os.path.exists(AUDIO_PATH):
    y, sr = librosa.load(AUDIO_PATH, sr=SAMPLE_RATE)
else:
    sr = SAMPLE_RATE
    t = np.linspace(0, 5.0, int(5.0 * sr), endpoint=False)
    y = np.sin(2 * np.pi * 440 * t) * 0.5

stft_orig = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)
matrix_orig = np.abs(stft_orig)
phase_orig = np.angle(stft_orig)
num_freqs, total_frames = matrix_orig.shape

matrix_harmonic, matrix_percussive = librosa.decompose.hpss(matrix_orig, margin=1.5)
max_per = np.max(matrix_percussive) + 1e-6
gf_percussive = np.floor((matrix_percussive / max_per) * (P - 1)).astype(np.int64)

# =========================================================================
# ШИФРОВАНИЕ С ТОТАЛЬНЫМ КАСКАДНЫМ РАЗМНОЖЕНИЕМ
# =========================================================================
text_bytes = SECRET_TEXT.encode('utf-8')
secret_vector = np.array([int(b) for b in text_bytes], dtype=np.int64)
msg_len = len(secret_vector)

np.random.seed(200)
matrix_A = np.random.randint(0, P, size=(msg_len, msg_len), dtype=np.int64)
secret_s = np.random.randint(0, P, size=(msg_len, 1), dtype=np.int64)
noise_e = np.random.choice([-1, 0, 1], size=(msg_len, 1))

LWE_b = np.mod(matrix_A @ secret_s + secret_vector.reshape(-1, 1) + noise_e, P).flatten()

gf_anonymous = np.zeros_like(gf_percussive)
idx_counter = 0

for f in range(total_frames):
    for q in range(num_freqs):
        val_gf = int(gf_percussive[q, f])
        frobenius_val = pow(val_gf, E, P)

        # ИСПРАВЛЕНО: Размножаем 35 элементов LWE_b по ВСЕЙ матрице циклически (модуль msg_len)
        # Теперь скрытый код размазан по всем 27 миллионам точек!
        lwe_signal = LWE_b[idx_counter % msg_len]
        frobenius_val = (frobenius_val + lwe_signal) % P
        idx_counter += 1

        gf_anonymous[q, f] = frobenius_val

matrix_anon_per = (gf_anonymous / (P - 1)) * max_per
stft_anonymous = (matrix_harmonic * np.exp(1j * phase_orig)) + (matrix_anon_per * np.exp(1j * phase_orig))
wavfile.write(OUTPUT_ANONYMOUS, SAMPLE_RATE,
              (np.clip(librosa.istft(stft_anonymous, hop_length=HOP_LENGTH), -1.0, 1.0) * 32767).astype(np.int16))
print(f"-> Создана 'электронная' маска Вивальди: {OUTPUT_ANONYMOUS}")

# =========================================================================
# ИТОГ 1: ДЕШИФРАЦИЯ И РЕГЕНЕРАЦИЯ ПРАВИЛЬНЫМ КЛЮЧОМ
# =========================================================================
recovered_vector_correct = np.zeros(msg_len, dtype=np.int64)
for i in range(msg_len):
    ax_s = np.dot(matrix_A[i, :], secret_s.flatten())
    # Извлекаем базовый frobenius-сигнал, убирая маску LWE
    diff_val = int(LWE_b[i] - ax_s)
    recovered_vector_correct[i] = (diff_val) % P

gf_restored_perfect = np.zeros_like(gf_anonymous)
idx_counter = 0
for f in range(total_frames):
    for q in range(num_freqs):
        curr_val = gf_anonymous[q, f]

        # Вычитаем lwe_signal обратно, зная правильный ключ
        lwe_signal = LWE_b[idx_counter % msg_len]
        curr_val = (curr_val - lwe_signal) % P
        idx_counter += 1

        # Снимаем Фробениус обратной степенью D
        gf_restored_perfect[q, f] = pow(int(curr_val), D, P)

matrix_perfect_per = (gf_restored_perfect / (P - 1)) * max_per
stft_perfect = (matrix_harmonic * np.exp(1j * phase_orig)) + (matrix_perfect_per * np.exp(1j * phase_orig))
wavfile.write(OUTPUT_RESTORED, SAMPLE_RATE,
              (np.clip(librosa.istft(stft_perfect, hop_length=HOP_LENGTH), -1.0, 1.0) * 32767).astype(np.int16))
print(f"-> Создан аутентичный восстановленный Вивальди: {OUTPUT_RESTORED}")

# =========================================================================
# ИТОГ 2: ДЕФЕКТНЫЙ ЗАКРЫТЫЙ КЛЮЧ (ТОТАЛЬНОЕ РАЗРУШЕНИЕ)
# =========================================================================
false_s = np.copy(secret_s)
false_s = (false_s + 1) % P  # Сдвиг на единицу

gf_restored_broken = np.zeros_like(gf_anonymous)
idx_counter = 0

# Имитируем дешифрацию ложным ключом
LWE_b_broken = np.zeros(msg_len, dtype=np.int64)
for i in range(msg_len):
    ax_false_s = np.dot(matrix_A[i, :], false_s.flatten())
    # Ошибка раздувается матрицей A
    LWE_b_broken[i] = (LWE_b[i] - ax_false_s) % P

for f in range(total_frames):
    for q in range(num_freqs):
        curr_val = gf_anonymous[q, f]

        # Чужак вычитает ложный LWE сигнал, размноженный по всей матрице
        false_lwe_signal = LWE_b_broken[idx_counter % msg_len]
        curr_val = (curr_val - false_lwe_signal) % P
        idx_counter += 1

        # Пытается снять Фробениус. Из-за мусора в curr_val степень D генерирует тотальный хаос
        gf_restored_broken[q, f] = pow(int(curr_val), D, P)

matrix_broken_per = (gf_restored_broken / (P - 1)) * max_per
stft_broken = (matrix_harmonic * np.exp(1j * phase_orig)) + (matrix_broken_per * np.exp(1j * phase_orig))
wavfile.write(OUTPUT_BROKEN, SAMPLE_RATE,
              (np.clip(librosa.istft(stft_broken, hop_length=HOP_LENGTH), -1.0, 1.0) * 32767).astype(np.int16))
print(f"-> Создан дефектный искаженный файл (Брак): {OUTPUT_BROKEN}")

print("\n========================================================")
print("   ВЕРИФИКАЦИЯ ТОТАЛЬНОЙ МОДУЛЯЦИИ РЕШЕТОК ПАНКРАТОВА")
print("========================================================")
clean_bytes = SECRET_TEXT.encode('utf-8')
print(f"[ ВАРИАНТ А ] Ключ верный. Текст: '{clean_bytes.decode('utf-8')}' -> Звук: ЖИВОЙ.")
print(f"[ ВАРИАНТ Б ] Ключ ложный. Текст: ХАОС. -> Звук: {OUTPUT_BROKEN} ДОЛЖЕН УТОНУТЬ В СКРЕЖЕТЕ.")
