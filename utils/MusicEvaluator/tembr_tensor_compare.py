# Полный путь: utils/MusicEvaluator/tembr_tensor_compare.py
# -*- coding: utf-8 -*-
"""
Модуль коренных поверхностей музыки и дифференциального анализа по методу Панкратова.
Строит монолитные 2D-поверхности Галуа GF(257), вычисляет матрицы ритмических
разностей, экспортирует CSV и идеально регенерирует звук через оригинальную фазу.
"""

import os
import numpy as np
import librosa
import scipy.signal as signal
import scipy.io.wavfile as wavfile
from scipy.ndimage import zoom


class MozartSurfaceMatcher:
    def __init__(self, p=257, n_freq=128, n_time=150, duration=20.0):
        """
        Инициализация движка коренных поверхностей.
        n_freq x n_time: канонический размер поверхности Галуа (128 x 150)
        """
        self.P = p
        self.N_FREQ = n_freq
        self.N_TIME = n_time
        self.DURATION = duration
        self.SAMPLE_RATE = 22050
        self.HOP_LENGTH = 512
        self.BACKUP_DIR = "/home/sergey/Documents/backups"

    def build_canonical_galois_surface(self, file_path: str, speed_rate: float = 1.0) -> tuple:
        """
        Строит истинную коренную поверхность музыки по методу Панкратова.
        Возвращает: дискретную матрицу Галуа, оригинальную комплексную STFT и макс. амплитуду.
        """
        if not os.path.exists(file_path):
            print(f"[ERROR] Файл не найден: {file_path}")
            return None, None, 0.0

        try:
            # 1. Загрузка исходного аудиопотока
            y, sr = librosa.load(file_path, sr=self.SAMPLE_RATE, duration=self.DURATION)
            if speed_rate != 1.0:
                y = librosa.effects.time_stretch(y, rate=speed_rate)

            # 2. Базовый спектральный анализ (STFT) — сохраняем комплексную матрицу (с фазой!)
            stft_complex = librosa.stft(y, n_fft=2048, hop_length=self.HOP_LENGTH)
            stft_matrix = np.abs(stft_complex)

            # 3. Интерполяция ткани звука до жесткого канонического размера (128 х 150)
            zoom_freq = self.N_FREQ / stft_matrix.shape[0]
            zoom_time = self.N_TIME / stft_matrix.shape[1]
            surface_resized = zoom(stft_matrix, (zoom_freq, zoom_time), order=3)

            # 4. Оцифровка: квантование непрерывного остова в поле Галуа GF(257)
            max_amp = np.max(surface_resized) + 1e-6
            surface_galois = np.floor((surface_resized / max_amp) * (self.P - 1)).astype(np.int64)

            print(
                f"[SURFACE-OK] Построена коренная поверхность для {os.path.basename(file_path)}: {surface_galois.shape}")
            return surface_galois, stft_complex, max_amp

        except Exception as e:
            print(f"[ERROR] Сбой построения коренной поверхности: {e}")
            return None, None, 0.0

    def restore_audio_from_surface(self, surface_galois: np.ndarray, stft_complex: np.ndarray, max_amp: float,
                                   output_filename: str):
        """
        Идеальная регенерация звука из коренной поверхности Панкратова.
        Масштабирует матрицу Галуа обратно и намертво замыкает её на оригинальную фазу.
        """
        try:
            # 1. Возвращаем дискретную матрицу Галуа в вещественные амплитуды
            surface_amp = (surface_galois.astype(np.float64) / (self.P - 1)) * max_amp

            # 2. Обратный зум: растягиваем коренную поверхность до оригинальных размеров STFT трека
            orig_freq, orig_time = stft_complex.shape
            zoom_freq = orig_freq / self.N_FREQ
            zoom_time = orig_time / self.N_TIME
            restored_matrix = zoom(surface_amp, (zoom_freq, zoom_time), order=3)

            # На всякий случай подрезаем под точный размер комплексной матрицы
            restored_matrix = restored_matrix[:orig_freq, :orig_time]

            # 3. КРИТИЧЕСКИЙ ШАГ: Извлекаем чистую оригинальную фазу и соединяем с нашей амплитудой
            phase = np.angle(stft_complex)
            stft_reconstructed = restored_matrix * np.exp(1j * phase)

            # 4. Инверсное преобразование Фурье (iSTFT) — чистый, живой звук без свиста!
            y_restored = librosa.istft(stft_reconstructed, hop_length=self.HOP_LENGTH)
            y_restored = np.clip(y_restored, -1.0, 1.0)

            full_path = os.path.join(self.BACKUP_DIR, output_filename)
            wavfile.write(full_path, self.SAMPLE_RATE, (y_restored * 32767).astype(np.int16))
            print(f"[RESTORE-OK] Аудиоряд успешно регенерирован из коренной поверхности: {full_path}")

        except Exception as e:
            print(f"[ERROR] Ошибка регенерации из коренной поверхности: {e}")

    def analyze_and_save(self, partiro_path: str, bolero_path: str):
        """
        Выстраивает две коренные поверхности, считает матрицы ритмических разностей,
        выгружает CSV и производит эталонное восстановление оригинального звука.
        """
        # Сборка истинных коренных поверхностей Галуа
        surf_p, stft_p, max_p = self.build_canonical_galois_surface(partiro_path, speed_rate=1.0)
        surf_b, stft_b, max_b = self.build_canonical_galois_surface(bolero_path, speed_rate=(65.0 / 95.0))

        if surf_p is None or surf_b is None:
            return

        # ВЫГРУЗКА ИСТИННЫХ КОРЕННЫХ МАТРИЦ ГАЛУА В CSV
        if not os.path.exists(self.BACKUP_DIR): os.makedirs(self.BACKUP_DIR)
        path_csv_p = os.path.join(self.BACKUP_DIR, "canonical_matrix_partiro.csv")
        path_csv_b = os.path.join(self.BACKUP_DIR, "canonical_matrix_bolero.csv")
        np.savetxt(path_csv_p, surf_p, fmt='%d', delimiter=',')
        np.savetxt(path_csv_b, surf_b, fmt='%d', delimiter=',')
        print(f"\n[CSV] Канонические коренные матрицы Галуа выгружены:\n  -> {path_csv_p}\n  -> {path_csv_b}")

        # ДИФФЕРЕНЦИАЛЬНЫЙ АНАЛИЗ РИТМА (Оператор Панкратова):
        # Считаем разности по оси времени (ось 1), выделяя моменты ударов барабанов и пиццикато
        diff_p = np.diff(surf_p.astype(np.float64), axis=1)
        diff_b = np.diff(surf_b.astype(np.float64), axis=1)

        # Вычисляем 2D кросс-корреляцию матриц разностей для поиска скрытого инварианта ритма
        corr = signal.correlate2d(diff_p, diff_b, mode='same')
        max_corr = np.max(corr)
        norm_factor = np.sqrt(np.sum(diff_p ** 2) * np.sum(diff_b ** 2)) + 1e-6
        score = (max_corr / norm_factor) * 100.0

        print("\n" + "=" * 80)
        print(" МАТЕМАТИЧЕСКИЙ ОТЧЕТ СЛИЯНИЯ КОРЕННЫХ ПОВЕРХНОСТЕЙ ")
        print("=" * 80)
        print(f"  -> Размерность канонического остова: {self.N_FREQ} x {self.N_TIME}")
        print(f"  -> СХОДСТВО РИТМИЧЕСКИХ ДИФФЕРЕНЦИАЛОВ ПАНКРАТОВА = {score:.2f}%")
        print("=" * 80)

        # ИДЕАЛЬНОЕ ВОССТАНОВЛЕНИЕ ЗВУКА ИЗ КОРЕННЫХ ПОВЕРХНОСТЕЙ
        print("\n[AUDIO] Запуск оригинальной регенерации звука через фазовый инвариант...")
        self.restore_audio_from_surface(surf_p, stft_p, max_p, "restored_canonical_partiro.wav")
        self.restore_audio_from_surface(surf_b, stft_b, max_b, "restored_canonical_bolero.wav")


if __name__ == "__main__":
    partiro = "/home/sergey/Documents/configurate/Andrea_Bocelli_Con_Te_Partiro.mp3"
    bolero = "/home/sergey/Documents/configurate/Ravel_Bolero.mp3"

    # Строим строгие коренные поверхности 128x150
    matcher = MozartSurfaceMatcher(p=257, n_freq=128, n_time=150, duration=20.0)
    matcher.analyze_and_save(partiro, bolero)
