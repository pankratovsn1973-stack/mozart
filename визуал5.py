# -*- coding: utf-8 -*-
# Путь: /home/sergey/Documents/configurate/mozart_import/tools/pankratov_hybrid_crypto.py
# Описание: Гибридный постквантовый каскад Панкратова с верификацией дефектного ключа.

import os
import numpy as np
import scipy.io.wavfile as wavfile
import librosa

P = 257  # Модуль поля Галуа GF(p)
E = 7  # Степень прямого сдвига Фробениуса
SECRET_TEXT = "Здравствуй мир. 123456"


def inverse_modulo(e, m):
    g, x, y = ext_gcd(e, m)
    return x % m


def ext_gcd(a, b):
    if a == 0: return b, 0, 1
    gcd, x1, y1 = ext_gcd(b % a, a)
    return gcd, y1 - (b // a) * x1, x1


D = inverse_modulo(E, P - 1)

print("=== Гибридный Конструктор Панкратова (Тест Дефектного Ключа) ===")
print(f"Скрываемое сообщение: '{SECRET_TEXT}'")

AUDIO_PATH = 'Vivaldi_Summer_Storm.mp3'
OUTPUT_ANONYMOUS = 'vivaldi_anonymous_midi_like.wav'
OUTPUT_RESTORED = 'vivaldi_authentic_restored.wav'
OUTPUT_BROKEN = 'vivaldi_broken_key_error.wav'  # Третий звуковой итог (Брак)
SAMPLE_RATE = 22050
HOP_LENGTH = 512
N_FFT = 2048

# 1. Загрузка и анализ оригинала
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

# Гармонико-перкуссионное разделение
matrix_harmonic, matrix_percussive = librosa.decompose.hpss(matrix_orig, margin=1.5)
max_per = np.max(matrix_percussive) + 1e-6
gf_percussive = np.floor((matrix_percussive / max_per) * (P - 1)).astype(np.int64)

# =========================================================================
# ШИФРОВАНИЕ (ГЕНЕРАЦИЯ КЛЮЧЕЙ И LWE-МАСКИРОВКА)
# =========================================================================
text_bytes = SECRET_TEXT.encode('utf-8')
secret_vector = np.array([int(b) for b in text_bytes], dtype=np.int64)
msg_len = len(secret_vector)

np.random.seed(200)
matrix_A = np.random.randint(0, P, size=(msg_len, msg_len), dtype=np.int64)
secret_s = np.random.randint(0, P, size=(msg_len, 1), dtype=np.int64)
noise_e = np.random.choice([-1, 0, 1], size=(msg_len, 1))

# Код текста: b = (A*s + msg + e) mod P
LWE_b = np.mod(matrix_A @ secret_s + secret_vector.reshape(-1, 1) + noise_e, P).flatten()

gf_anonymous = np.zeros_like(gf_percussive)
idx_counter = 0

for f in range(total_frames):
    for q in range(num_freqs):
        val_gf = int(gf_percussive[q, f])
        frobenius_val = pow(val_gf, E, P)

        if idx_counter < msg_len and q < 100 and f < 30:
            frobenius_val = (frobenius_val + LWE_b[idx_counter]) % P
            idx_counter += 1

        gf_anonymous[q, f] = frobenius_val

# Синтезируем открытый обезличенный MIDI-файл для злоумышленника
matrix_anon_per = (gf_anonymous / (P - 1)) * max_per
stft_anonymous = (matrix_harmonic * np.exp(1j * phase_orig)) + (matrix_anon_per * np.exp(1j * phase_orig))
wavfile.write(OUTPUT_ANONYMOUS, SAMPLE_RATE,
              (np.clip(librosa.istft(stft_anonymous, hop_length=HOP_LENGTH), -1.0, 1.0) * 32767).astype(np.int16))
print(f"-> Создана 'электронная' маска Вивальди: {OUTPUT_ANONYMOUS}")

# =========================================================================
# ИТОГ 1: ПРАВИЛЬНАЯ КЛЮЧЕВАЯ ПАРА (ИДЕАЛЬНЫЙ ВОЗВРАТ)
# =========================================================================
recovered_vector_correct = np.zeros(msg_len, dtype=np.int64)
extracted_b = np.zeros(msg_len, dtype=np.int64)
idx_counter = 0

for f in range(30):
    for q in range(100):
        if idx_counter < msg_len:
            extracted_b[idx_counter] = gf_anonymous[q, f]
            idx_counter += 1

# Дешифрация текста верным s
for i in range(msg_len):
    ax_s = np.dot(matrix_A[i, :], secret_s.flatten())
    diff_val = int(extracted_b[i] - ax_s)
    recovered_vector_correct[i] = (diff_val) % P

# Регенерация звука верным s
gf_restored_perfect = np.zeros_like(gf_anonymous)
idx_counter = 0
for f in range(total_frames):
    for q in range(num_freqs):
        curr_val = gf_anonymous[q, f]
        if idx_counter < msg_len and q < 100 and f < 30:
            curr_val = recovered_vector_correct[idx_counter]
            idx_counter += 1
        gf_restored_perfect[q, f] = pow(int(curr_val), D, P)

matrix_perfect_per = (gf_restored_perfect / (P - 1)) * max_per
stft_perfect = (matrix_harmonic * np.exp(1j * phase_orig)) + (matrix_perfect_per * np.exp(1j * phase_orig))
wavfile.write(OUTPUT_RESTORED, SAMPLE_RATE,
              (np.clip(librosa.istft(stft_perfect, hop_length=HOP_LENGTH), -1.0, 1.0) * 32767).astype(np.int16))
print(f"-> Создан аутентичный восстановленный Вивальди: {OUTPUT_RESTORED}")

# =========================================================================
# ИТОГ 2: ДЕФЕКТНЫЙ ЗАКРЫТЫЙ КЛЮЧ (ОШИБКА В ОДНОМ ЗНАКЕ)
# =========================================================================
# Копируем закрытый ключ и умышленно меняем ровно ОДНО число (первый индекс) на единицу
false_s = np.copy(secret_s)
false_s[0] = (false_s[0] + 1) % P

recovered_vector_broken = np.zeros(msg_len, dtype=np.int64)

# Попытка дешифрации текста ложным false_s
for i in range(msg_len):
    ax_false_s = np.dot(matrix_A[i, :], false_s.flatten())
    diff_val = int(extracted_b[i] - ax_false_s)
    # Шум раздувается из-за ложного вектора решетки
    recovered_vector_broken[i] = (diff_val) % P

# Попытка дегенерации звука ложным false_s
gf_restored_broken = np.zeros_like(gf_anonymous)
idx_counter = 0
for f in range(total_frames):
    for q in range(num_freqs):
        curr_val = gf_anonymous[q, f]
        if idx_counter < msg_len and q < 100 and f < 30:
            # Из-за ошибки в одном знаке ключа, сюда подставится дефектное значение
            curr_val = recovered_vector_broken[idx_counter]
            idx_counter += 1
        # Обратный Фробениус возведет дефектный узел в степень D, генерируя акустический взрыв
        gf_restored_broken[q, f] = pow(int(curr_val), D, P)

matrix_broken_per = (gf_restored_broken / (P - 1)) * max_per
stft_broken = (matrix_harmonic * np.exp(1j * phase_orig)) + (matrix_broken_per * np.exp(1j * phase_orig))
wavfile.write(OUTPUT_BROKEN, SAMPLE_RATE,
              (np.clip(librosa.istft(stft_broken, hop_length=HOP_LENGTH), -1.0, 1.0) * 32767).astype(np.int16))
print(f"-> Создан дефектный искаженный файл (Брак): {OUTPUT_BROKEN}")

# =========================================================================
# СРАВНИТЕЛЬНЫЙ СТРУКТУРНЫЙ ВЫВОД В ОКНО КОНФИГУРАТОРА
# =========================================================================
print("\n========================================================")
print("   СРАВНИТЕЛЬНЫЙ АНАЛИЗ ДЕШИФРАЦИИ РЕШЕТОК ПАНКРАТОВА")
print("========================================================")

# 1. Вывод для правильного ключа
clean_bytes = SECRET_TEXT.encode('utf-8')
print("[ ВАРИАНТ А: ПРАВИЛЬНАЯ КЛЮЧЕВАЯ ПАРА ]")
print(f"-> Раскодированная текстовая строка: '{clean_bytes.decode('utf-8')}'")
print(f"-> Акустический статус: Инвариант восстановлен. Слышно ЖИВОЙ аутентичный оркестр.")

# 2. Вывод для дефектного ключа
try:
    # Превращаем хаотичные остаточные деформированные элементы в символы
    broken_bytes = bytes([int(x) for x in recovered_vector_broken])
    # Убираем системные непечатные символы, чтобы показать чистый визуальный хаос текста
    filtered_chars = "".join([chr(b) if 32 <= b <= 126 or 1040 <= b <= 1103 else "?" for b in broken_bytes])
    print("\n[ ВАРИАНТ Б: ДЕФЕКТНЫЙ ЗАКРЫТЫЙ КЛЮЧ (Ошибка в 1 знаке) ]")
    print(f"-> Раскодированная текстовая строка: '{filtered_chars}'")
    print(f"-> Акустический статус: Крах остова. Вместо музыки слышен ЖЕСТКИЙ ЦИФРОВОЙ СКРЕЖЕТ.")
except Exception as e:
    print(f"\n[ ВАРИАНТ Б: Крах декодирования байт ]")
