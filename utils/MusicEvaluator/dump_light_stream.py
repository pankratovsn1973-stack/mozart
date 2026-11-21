# Полный путь: utils/MusicEvaluator/dump_light_stream.py
# -*- coding: utf-8 -*-
"""
Модуль компактного экспорта светового и звукового потока в текст по методу Панкратова.
Транслирует спектрограмму в 60 логарифмических нотных каналов поля Галуа
и кодирует амплитуду каждого кадра в один уникальный символ (1 символ = 1 кадр).
"""

import os
import numpy as np
import librosa

# Глобальный 64-значный алфавит Панкратова для кодирования уровней громкости (0-63)
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!/"
CHAR_SILENCE = "."  # Отдельный маркер для абсолютной тишины


class GaloisStreamDumper:
    def __init__(self, steps=60, sample_rate=22050, hop_length=512, n_fft=2048):
        """Инициализирует параметры частотно-временного квантования потока."""
        self.STEPS = steps
        self.SAMPLE_RATE = sample_rate
        self.HOP_LENGTH = hop_length
        self.N_FFT = n_fft

        # Задаем 60 границ логарифмических бинов: от До большой октавы (65.4 Гц) до До 4-й (2093.0 Гц)
        self.audio_bins = np.logspace(np.log10(65.4), np.log10(2093.0), self.STEPS + 1)
        self.notes_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def _val_to_char(self, val: float) -> str:
        """Внутренний метод: нелинейно кодирует нормированную амплитуду [0.0, 1.0] в 1 символ."""
        if val <= 0.005:  # Физический порог отсечения тишины
            return CHAR_SILENCE

        # Маппим вещественное число в индекс алфавита от 0 до 63
        idx = int(val * 63)
        idx = max(0, min(63, idx))
        return ALPHABET[idx]

    def generate_text_stream(self, audio_path: str, output_txt_path: str, duration: float = 30.0):
        """
        Загружает аудиофайл, производит FFT-анализ, логарифмическое сжатие
        и записывает компактный текстовый дамп каналов.
        """
        print(f"[START] Запуск компактного дампа светового потока для: {os.path.basename(audio_path)}")

        if not os.path.exists(audio_path):
            print(f"[ERROR] Исходный аудиофайл не найден по пути: {audio_path}")
            return

        try:
            # 1. Загрузка аудиопотока в память
            y, sr = librosa.load(audio_path, sr=self.SAMPLE_RATE, duration=duration)

            # 2. Быстрое преобразование Фурье (STFT) - извлекаем матрицу амплитуд
            stft_matrix = np.abs(librosa.stft(y, n_fft=self.N_FFT, hop_length=self.HOP_LENGTH))
            frequencies = librosa.fft_frequencies(sr=sr, n_fft=self.N_FFT)
            num_frames = stft_matrix.shape[1]

            # 3. Распределение энергии по 60 частотным каналам Галуа
            light_spectrogram = []
            for i in range(self.STEPS):
                # Ищем индексы частот, попавших в границы текущей ноты
                idx = np.where((frequencies >= self.audio_bins[i]) & (frequencies < self.audio_bins[i + 1]))[0]
                if len(idx) > 0:
                    light_spectrogram.append(np.mean(stft_matrix[idx, :], axis=0))
                else:
                    light_spectrogram.append(np.zeros(num_frames))

            light_spectrogram = np.array(light_spectrogram)

            # Нормализуем остов матрицы для корректного масштабирования символов громкости
            max_val = np.max(light_spectrogram) + 1e-6
            light_spectrogram = light_spectrogram / max_val

            # 4. Построчная запись закодированного светового потока в текстовый файл
            with open(output_txt_path, 'w', encoding='utf-8') as f:
                f.write("# MOZART Compressed Galois Stream\n")
                f.write(f"# Target File: {os.path.basename(audio_path)}\n")
                f.write(f"# Channels: {self.STEPS}, Frames: {num_frames}\n")
                f.write("# Dictionary: . = тишина, 0-9 = тихо, a-z = среднее, A-Z = громко, ! / = пик\n\n")

                for channel_idx in range(self.STEPS):
                    octave = channel_idx // 12
                    note_name = self.notes_names[channel_idx % 12]

                    row_values = light_spectrogram[channel_idx, :]
                    # Кодируем каждый временной кадр строки в один символ и склеиваем в сплошную ленту
                    row_chars = "".join([self._val_to_char(v) for v in row_values])

                    # Пишем в формате: Нота_Октава:СимвольнаяЛентаВремени
                    f.write(f"CH{channel_idx + 1:02d}_{note_name}{octave}:{row_chars}\n")

            print(f"[SUCCESS] Компактный дамп успешно сохранен в: {output_txt_path}")
            print(f"[STATS] Длина текстовой ленты одного канала: {num_frames} символов (кадров).")

        except Exception as e:
            print(f"[CRITICAL ERROR] Не удалось выполнить экспорт светового потока: {e}")


if __name__ == "__main__":
    # Координаты файлов на вашей машине
    input_audio = "/home/sergey/Documents/configurate/Ravel_Bolero.mp3"
    output_text = "/home/sergey/Documents/backups/Ravel_Bolero.txt"

    # Инициализируем и запускаем 30-секундный экспорт
    dumper = GaloisStreamDumper(steps=60)
    dumper.generate_text_stream(input_audio, output_text, duration=30.0)
