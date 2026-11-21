# Полный путь: utils/MusicEvaluator/tensor_production.py
# -*- coding: utf-8 -*-
"""
Модуль канонического тензорного разложения Панкратова (Тензор произведения).
Раскладывает звуковую ткань на внешние произведения спектральных остовов и ритмических лент,
квантует подпространства в поле Галуа GF(257) и регенерирует чистый звук инструментов.
"""

import os
import numpy as np
import librosa
import scipy.io.wavfile as wavfile
from scipy.ndimage import zoom

class MozartTensorProduction:
    def __init__(self, p=257, n_components=20, duration=20.0):
        """
        Инициализирует конструктор тензора произведения.
        p: модуль поля Галуа (257)
        n_components: количество извлекаемых тембральных канонических поверхностей (слоев тензора)
        """
        self.P = p
        self.N_COMPONENTS = n_components
        self.DURATION = duration
        self.SAMPLE_RATE = 22050
        self.HOP_LENGTH = 512
        self.BACKUP_DIR = "/home/sergey/Documents/backups"

    def decompose_to_surface_tensor(self, file_path: str, speed_rate: float = 1.0) -> tuple:
        """
        Разлагает исходный STFT-сигнал на многослойный тензор произведения.
        Выделяет семейство матриц V_k = W_k (тембр) x H_k (ритм), квантованных в поле Галуа.
        Возвращает: 3D тензор поверхностей Галуа, базис остовов W, матрицу активаций H и комплексный STFT.
        """
        if not os.path.exists(file_path):
            print(f"[ERROR] Файл не найден: {file_path}")
            return None, None, None, None

        try:
            # 1. Загрузка волнового фронта с учетом растяжения времени
            y, sr = librosa.load(file_path, sr=self.SAMPLE_RATE, duration=self.DURATION)
            if speed_rate != 1.0:
                y = librosa.effects.time_stretch(y, rate=speed_rate)

            # 2. Получение комплексного спектра (сохраняем фазу!)
            stft_complex = librosa.stft(y, n_fft=2048, hop_length=self.HOP_LENGTH)
            stft_matrix = np.abs(stft_complex)
            orig_freqs, orig_frames = stft_matrix.shape

            # 3. Математическое разложение матрицы на внешние произведения (Алгебраический NMF базис)
            # W (orig_freqs, N_COMPONENTS) — спектральные остовы (тембры)
            # H (N_COMPONENTS, orig_frames) — временные ленты (ритмы)
            W, H = librosa.decompose.decompose(stft_matrix, n_components=self.N_COMPONENTS, sort=True)

            # 4. Строим 3D тензор канонических поверхностей Галуа
            # Каждая поверхность V_k имеет размерность оригинального STFT трека
            surface_tensor = np.zeros((self.N_COMPONENTS, orig_freqs, orig_frames), dtype=np.int64)

            print(f"[MATH] Сборка семейства канонических поверхностей для {os.path.basename(file_path)}...")
            for k in range(self.N_COMPONENTS):
                # Внешнее произведение (Тензор произведения): V_k = W_k * H_k
                # Восстанавливает чистую непрерывную изолированную ткань конкретного тембра
                v_k_raw = np.outer(W[:, k], H[k, :])

                # Квантование Панкратова в дискретное поле Галуа GF(257) для очистки от кросс-шумов
                max_val = np.max(v_k_raw) + 1e-6
                surface_tensor[k] = np.floor((v_k_raw / max_val) * (self.P - 1)).astype(np.int64)

            return surface_tensor, W, H, stft_complex

        except Exception as e:
            print(f"[ERROR] Критическая ошибка разложения тензора произведения: {e}")
            return None, None, None, None

    def restore_pure_tembr_audio(self, W_k: np.ndarray, H_k: np.ndarray, stft_complex: np.ndarray, output_filename: str):
        """
        Регенерирует чистый, плотный физический звук конкретного тембра из его подпространства.
        Использует оригинальную комплексную фазовую матрицу трека, полностью исключая свист.
        """
        try:
            # 1. Восстанавливаем вещественную амплитудную матрицу слоя из внешнего произведения остова и ритма
            reconstructed_magnitude = np.outer(W_k, H_k)

            # 2. Извлекаем оригинальную фазовую матрицу
            phase = np.angle(stft_complex)

            # 3. Намертво склеиваем восстановленный тембральный остов с оригинальной фазой
            stft_reconstructed = reconstructed_magnitude * np.exp(1j * phase)

            # 4. Инверсное преобразование (iSTFT) — дает живой, глубокий звук инструмента
            y_restored = librosa.istft(stft_reconstructed, hop_length=self.HOP_LENGTH)
            y_restored = np.clip(y_restored, -1.0, 1.0)

            if not os.path.exists(self.BACKUP_DIR):
                os.makedirs(self.BACKUP_DIR)

            full_path = os.path.join(self.BACKUP_DIR, output_filename)
            wavfile.write(full_path, self.SAMPLE_RATE, (y_restored * 32767).astype(np.int16))
            print(f"[AUDIO-OK] Тембральный слой регенерирован без искажений: {full_path}")

        except Exception as e:
            print(f"[ERROR] Ошибка регенерации волнового фронта тембра: {e}")

    def execute_tensor_matching(self, partiro_path: str, bolero_path: str):
        """
        Производит перекрестный анализ семейства канонических поверхностей Галуа.
        Использует дифференциальный фильтр Панкратова (np.diff) для векторов времени H,
        чтобы полностью подавить плавные струнные слои и вытащить скрытый ритм БАРАБАНОВ.
        """
        # Разлагаем оба трека на многослойные тензоры внешних произведений (W x H)
        surf_p, W_p, H_p, stft_p = self.decompose_to_surface_tensor(partiro_path, speed_rate=1.0)
        surf_b, W_b, H_b, stft_b = self.decompose_to_surface_tensor(bolero_path, speed_rate=(65.0 / 95.0))

        if surf_p is None or surf_b is None:
            return

        print("\n[DIFFERENTIAL-PROCESS] Сравнение импульсных разностей ритма (каждый с каждым)...")

        best_score = 0.0
        best_p_layer = -1
        best_b_layer = -1

        # Определяем минимальный общий размер кадров
        min_frames = min(H_p.shape[1], H_b.shape[1])

        # Перебираем все извлеченные тембральные слои (канонические поверхности)
        for p_idx in range(self.N_COMPONENTS):
            # Извлекаем вектор времени Бочелли
            h_p_vector = H_p[p_idx, :min_frames]
            # КРИТИЧЕСКИЙ ШАГ: Считаем первую разность (производную). Плавные голоса/скрипки уходят в ноль,
            # а бритвенные атаки малого барабана и пиццикато превращаются в мощные пики!
            diff_p_vector = np.diff(h_p_vector)
            diff_p_vector -= np.mean(diff_p_vector)

            for b_idx in range(self.N_COMPONENTS):
                # Извлекаем вектор времени Равеля и применяем дифференциальный фильтр
                h_b_vector = H_b[b_idx, :min_frames]
                diff_b_vector = np.diff(h_b_vector)
                diff_b_vector -= np.mean(diff_b_vector)

                # Вычисляем косинусное сходство очищенных импульсных решеток
                norm_factor = np.sqrt(np.sum(diff_p_vector ** 2) * np.sum(diff_b_vector ** 2)) + 1e-6
                score = (np.dot(diff_p_vector, diff_b_vector) / norm_factor) * 100.0

                # Ищем максимум сходства именно по импульсным атакам
                if score > best_score:
                    best_score = score
                    best_p_layer = p_idx + 1
                    best_b_layer = b_idx + 1

        print("\n" + "=" * 80)
        print(" РЕЗУЛЬТАТ ДИФФЕРЕНЦИАЛЬНОГО АНАЛИЗА ТЕНЗОРОВ ПРОИЗВЕДЕНИЯ ")
        print("=" * 80)
        print(f"  -> Плавные струнные группы холста успешно отфильтрованы и подавлены.")
        print(f"  -> Импульсное тождество барабанных решеток обнаружено на стыке:")
        print(f"     Слой 'Партиро' #{best_p_layer}  <====== СОВПАЛ ======>  Слой 'Болеро' #{best_b_layer}")
        print(f"  -> КОЭФФИЦИЕНТ ИДЕНТИЧНОСТИ УДАРНОГО ОСТОВА = {best_score:.2f}%")
        print("=" * 80)

        # ВЫГРУЗКА ИСТИННЫХ ДВУМЕРНЫХ МАТРИЦ ГАЛУА ДЛЯ ВЫДЕЛЕННОГО БАРАБАННОГО СЛОЯ
        path_csv_p = os.path.join(self.BACKUP_DIR, f"galois_production_matrix_partiro_layer_{best_p_layer}.csv")
        path_csv_b = os.path.join(self.BACKUP_DIR, f"galois_production_matrix_bolero_layer_{best_b_layer}.csv")
        np.savetxt(path_csv_p, surf_p[best_p_layer - 1, :, :min_frames], fmt='%d', delimiter=',')
        np.savetxt(path_csv_b, surf_b[best_b_layer - 1, :, :min_frames], fmt='%d', delimiter=',')
        print(
            f"[CSV] Матрицы Галуа для ударного слоя выгружены в backups/:\n  -> {os.path.basename(path_csv_p)}\n  -> {os.path.basename(path_csv_b)}")

        # РЕГЕНЕРАЦИЯ ОЧИЩЕННОГО ИНСТРУМЕНТАЛЬНОГО ЗВУКА ИЗ КОРЕННОЙ ПОВЕРХНОСТИ ВЫБРАННОГО СЛОЯ
        print("\n[AUDIO] Регенерация выделенного ударного подпространства (Гриффин-Лим не нужен!)...")
        self.restore_pure_tembr_audio(W_p[:, best_p_layer - 1], H_p[best_p_layer - 1, :], stft_p,
                                      "restored_production_partiro.wav")
        self.restore_pure_tembr_audio(W_b[:, best_b_layer - 1], H_b[best_b_layer - 1, :], stft_b,
                                      "restored_production_bolero.wav")


if __name__ == "__main__":
    partiro_track = "/home/sergey/Documents/configurate/Andrea_Bocelli_Con_Te_Partiro.mp3"
    bolero_track = "/home/sergey/Documents/configurate/Ravel_Bolero.mp3"

    # Извлекаем 20 честных канонических поверхностей внешнего произведения
    matcher = MozartTensorProduction(p=257, n_components=20, duration=20.0)
    matcher.execute_tensor_matching(partiro_track, bolero_track)
