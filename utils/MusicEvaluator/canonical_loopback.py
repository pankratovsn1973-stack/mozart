# Полный путь: utils/MusicEvaluator/canonical_loopback.py
# -*- coding: utf-8 -*-
"""
Графическая утилита декомпозиции коренных поверхностей Галуа по методу Панкратова.
Обеспечивает интерактивный выбор двух аудиофайлов, расчет ритмической и мелодической корреляции,
выгрузку CSV-матриц и регенерацию раздельных аудиодорожек.
"""

import os
import sys
import numpy as np
import librosa
import scipy.io.wavfile as wavfile
import scipy.ndimage as ndimage
from scipy.ndimage import zoom
from datetime import datetime

from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QFormLayout, QLineEdit, QPushButton,
                               QLabel, QTextEdit, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class MozartAudioAnalyzerWindow(QDialog):
    def __init__(self, parent=None):
        """Инициализирует графический интерфейс декомпозитора Панкратова."""
        super().__init__(parent)
        self.setWindowTitle("Тензорный анализатор скрытых инвариантов MOZART ERP")
        self.resize(750, 650)

        # Канонические параметры ядра СУБД
        self.P = 257
        self.N_FREQ = 128
        self.DURATION = 20.0
        self.SAMPLE_RATE = 22050
        self.HOP_LENGTH = 512
        self.BACKUP_DIR = "/home/sergey/Documents/backups"

        # Строим интерфейс
        self.setup_ui()

    def setup_ui(self):
        """Создает элементы управления, поля выбора файлов и окно вывода логов."""
        main_layout = QVBoxLayout(self)

        # 1. Блок выбора исследуемых файлов
        files_group = QGroupBox("Выбор объектов для тензорного анализа")
        files_layout = QFormLayout(files_group)

        self.track_a_edit = QLineEdit("")
        self.btn_browse_a = QPushButton("Обзор...")
        self.btn_browse_a.clicked.connect(lambda: self.browse_file(self.track_a_edit))
        layout_a = QHBoxLayout()
        layout_a.addWidget(self.track_a_edit)
        layout_a.addWidget(self.btn_browse_a)

        self.track_b_edit = QLineEdit("")
        self.btn_browse_b = QPushButton("Обзор...")
        self.btn_browse_b.clicked.connect(lambda: self.browse_file(self.track_b_edit))
        layout_b = QHBoxLayout()
        layout_b.addWidget(self.track_b_edit)
        layout_b.addWidget(self.btn_browse_b)

        files_layout.addRow("Объект А (Сигнал-источник):", layout_a)
        files_layout.addRow("Объект Б (Искомый инвариант):", layout_b)
        main_layout.addWidget(files_group)

        # 2. Окно лога выполнения реального времени
        main_layout.addWidget(QLabel("Лог выполнения декомпозиции и вердикт системы:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        # Задаем моноширинный шрифт для красивого вывода таблиц тайминга
        mono_font = QFont("Courier New", 9)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self.log_output.setFont(mono_font)
        main_layout.addWidget(self.log_output)

        # 3. Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("Запустить сепарацию рядов")
        self.btn_start.setStyleSheet("font-weight: bold; background-color: #0066cc; color: white; padding: 6px;")
        self.btn_start.clicked.connect(self.execute_analysis)

        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_close)
        main_layout.addLayout(btn_layout)

    def browse_file(self, line_edit: QLineEdit):
        """Вызывает стандартный QFileDialog для интерактивного выбора mp3/wav."""
        start_dir = line_edit.text().strip() if line_edit.text().strip() else os.path.expanduser("~")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите аудиофайл для анализа", start_dir, "Audio Files (*.mp3 *.wav *.ogg *.flac)"
        )
        if file_path:
            line_edit.setText(file_path)

    def execute_analysis(self):
        """Метод-координатор: собирает файлы из UI и запускает сквозной цикл сепарации рядов."""
        self.log_output.clear()
        path_a = self.track_a_edit.text().strip()
        path_b = self.track_b_edit.text().strip()

        if not os.path.exists(path_a) or not os.path.exists(path_b):
            QMessageBox.critical(self, "Ошибка", "Один или оба указанных аудиофайла не найдены на диске!")
            return

        self.log_output.append(f"[{datetime.now().strftime('%H:%M:%S')}] Старт сепарации коренных поверхностей...")
        QApplication.processEvents()

        try:
            # =========================================================================
            # ШАГ 1: Сборка коренной поверхности для Объекта А
            # =========================================================================
            self.log_output.append(f"\n[INFO] Загрузка и анализ Объекта А: {os.path.basename(path_a)}")
            y_p, sr_p = librosa.load(path_a, sr=self.SAMPLE_RATE, duration=self.DURATION)
            stft_complex_p = librosa.stft(y_p, n_fft=2048, hop_length=self.HOP_LENGTH)
            stft_matrix_p = np.abs(stft_complex_p)

            zoom_freq_p = self.N_FREQ / stft_matrix_p.shape[0]
            surface_resized_p = zoom(stft_matrix_p, (zoom_freq_p, 1.0), order=3)
            max_p = np.max(surface_resized_p) + 1e-6
            surf_p_galois = np.floor((surface_resized_p / max_p) * (self.P - 1)).astype(np.int64)

            # =========================================================================
            # ШАГ 2: Сборка коренной поверхности для Объекта Б
            # =========================================================================
            self.log_output.append(f"[INFO] Загрузка и анализ Объекта Б: {os.path.basename(path_b)}")
            y_b, sr_b = librosa.load(path_b, sr=self.SAMPLE_RATE, duration=self.DURATION)

            # Используем оригинал без растяжения времени для честного сравнения
            y_b_processed = y_b

            stft_complex_b = librosa.stft(y_b_processed, n_fft=2048, hop_length=self.HOP_LENGTH)
            stft_matrix_b = np.abs(stft_complex_b)

            zoom_freq_b = self.N_FREQ / stft_matrix_b.shape[0]
            surface_resized_b = zoom(stft_matrix_b, (zoom_freq_b, 1.0), order=3)
            max_b = np.max(surface_resized_b) + 1e-6
            surf_b_galois = np.floor((surface_resized_b / max_b) * (self.P - 1)).astype(np.int64)

            # Синхронизация временных кадров под общий минимальный размер
            min_frames = min(surf_p_galois.shape[1], surf_b_galois.shape[1])
            surf_p_trimmed = surf_p_galois[:, :min_frames]
            surf_b_trimmed = surf_b_galois[:, :min_frames]
            stft_complex_p_trimmed = stft_complex_p[:, :min_frames]
            stft_complex_b_trimmed = stft_complex_b[:, :min_frames]

            # =========================================================================
            # ШАГ 3: Алгебраическое разделение рядов оператором Панкратова
            # =========================================================================
            self.log_output.append("[INFO] Выполнение алгебраического разделения на Мелодию и Барабаны...")

            # Ряд МЕЛОДИИ (сглаживание)
            surf_p_melody = ndimage.gaussian_filter(surf_p_trimmed.astype(np.float64), sigma=(1.5, 0.5))
            surf_p_melody = np.clip(surf_p_melody, 0, 256).astype(np.int64)

            surf_b_melody = ndimage.gaussian_filter(surf_b_trimmed.astype(np.float64), sigma=(1.5, 0.5))
            surf_b_melody = np.clip(surf_b_melody, 0, 256).astype(np.int64)

            # Ряд БАРАБАНОВ (вычитание мелодии из общего остова)
            surf_p_drums = surf_p_trimmed.astype(np.float64) - surf_p_melody.astype(np.float64)
            surf_p_drums = np.clip(surf_p_drums, 0, 256).astype(np.int64)

            surf_b_drums = surf_b_trimmed.astype(np.float64) - surf_b_melody.astype(np.float64)
            surf_b_drums = np.clip(surf_b_drums, 0, 256).astype(np.int64)

            # =========================================================================
            # ШАГ 4: Выгрузка числовых 2D-матриц в CSV
            # =========================================================================
            self._save_csv(surf_p_melody, "MELODY_ROW", os.path.basename(path_a))
            self._save_csv(surf_p_drums, "DRUMS_ROW", os.path.basename(path_a))
            self._save_csv(surf_b_melody, "MELODY_ROW", os.path.basename(path_b))
            self._save_csv(surf_b_drums, "DRUMS_ROW", os.path.basename(path_b))

            # =========================================================================
            # ШАГ 5: Регенерация аудиофайлов рядов через оригинальную фазу
            # =========================================================================
            self.log_output.append("\n[AUDIO] Синтез раздельных звуковых дорожек...")
            amp_p_drums = (surf_p_drums.astype(np.float64) / (self.P - 1)) * max_p
            amp_b_drums = (surf_b_drums.astype(np.float64) / (self.P - 1)) * max_b

            self._restore_audio(amp_p_drums, stft_complex_p_trimmed, "row2_drums_track_a.wav")
            self._restore_audio(amp_b_drums, stft_complex_b_trimmed, "row2_drums_track_b.wav")

            # =========================================================================
            # ШАГ 6: Расчет корреляций и вывод вердиктов
            # =========================================================================

            # 6.1 Проверка РИТМА (Drums)
            self.log_output.append("\n" + "=" * 65)
            self.log_output.append(" АНАЛИЗ РИТМИЧЕСКИХ ОСТОВОВ (DRUMS ROW) ")
            self.log_output.append("=" * 65)
            self._calculate_and_log_metrics(surf_p_drums, surf_b_drums, os.path.basename(path_a),
                                            os.path.basename(path_b))

            # 6.2 Проверка МЕЛОДИИ (Melody) - ИНТЕГРИРОВАННЫЙ АНАЛИЗ
            self.log_output.append("\n" + "=" * 65)
            self.log_output.append(" АНАЛИЗ ГАРМОНИЧЕСКИХ СКЕЛЕТОВ (MELODY ROW) ")
            self.log_output.append("=" * 65)
            self.verify_melody_harmony(surf_p_melody, surf_b_melody, os.path.basename(path_a), os.path.basename(path_b))

            QMessageBox.information(self, "Успех",
                                    f"Декомпозиция завершена! Все матрицы Галуа и WAV-файлы сохранены в:\n{self.BACKUP_DIR}")

        except Exception as e:
            self.log_output.append(f"\n[CRITICAL ERROR] Ошибка ядра: {e}")
            import traceback
            self.log_output.append(traceback.format_exc())
            QMessageBox.critical(self, "Критический сбой", f"Не удалось выполнить тензорный анализ:\n{e}")

    def _save_csv(self, matrix: np.ndarray, prefix: str, filename: str):
        """Внутренний метод: пишет числовой массив Галуа на диск."""
        if not os.path.exists(self.BACKUP_DIR): os.makedirs(self.BACKUP_DIR)
        clean_name = filename.replace('.', '_').replace(' ', '_')
        path = os.path.join(self.BACKUP_DIR, f"galois_matrix_{prefix}_{clean_name}.csv")
        np.savetxt(path, matrix, fmt='%d', delimiter=',')
        self.log_output.append(f"[CSV EXPORT] Выгружена числовая матрица: {os.path.basename(path)}")

    def _restore_audio(self, amp_matrix: np.ndarray, stft_complex: np.ndarray, out_name: str):
        """Внутренний метод: восстанавливает плотную аудиоволну без свиста."""
        orig_freq, orig_time = stft_complex.shape
        zoom_freq = orig_freq / self.N_FREQ
        restored = zoom(amp_matrix, (zoom_freq, 1.0), order=3)[:orig_freq, :orig_time]
        stft_final = restored * np.exp(1j * np.angle(stft_complex))
        y = librosa.istft(stft_final, hop_length=self.HOP_LENGTH)
        wavfile.write(os.path.join(self.BACKUP_DIR, out_name), self.SAMPLE_RATE,
                      (np.clip(y, -1.0, 1.0) * 32767).astype(np.int16))

    def _calculate_and_log_metrics(self, matrix_p: np.ndarray, matrix_b: np.ndarray, name_a: str, name_b: str):
        """
        Схлопывает матрицы по столбцам времени и выводит динамический график тайминга.
        Используется для DRUMS ROW.
        """
        vector_p = np.sum(matrix_p.astype(np.float64), axis=0)
        vector_b = np.sum(matrix_b.astype(np.float64), axis=0)
        min_len = min(len(vector_p), len(vector_b))

        v_p_centered = vector_p[:min_len] - np.mean(vector_p[:min_len])
        v_b_centered = vector_b[:min_len] - np.mean(vector_b[:min_len])

        # Вычисляем коэффициент Пирсона
        corr_matrix = np.corrcoef(v_p_centered, v_b_centered)
        score = corr_matrix[0, 1] * 100.0

        clean_a = name_a.replace('_mp3', '').replace('_wav', '')[:20]
        clean_b = name_b.replace('_mp3', '').replace('_wav', '')[:20]

        self.log_output.append(f"  -> Анализируемая временная лента: {min_len} квантов времени.")
        self.log_output.append(f"  -> ИСТИННАЯ КОРРЕЛЯЦИЯ ИМПУЛЬСОВ ВРЕМЕНИ = {score:.2f}%")
        self.log_output.append("-" * 65)
        self.log_output.append("  [ВИЗУАЛИЗАЦИЯ СЕТКИ ТАЙМИНГА (Первые 40 квантов)]:")

        str_b = f"  {clean_b:<20}: " + "".join(["█" if x > 0 else "░" for x in v_b_centered[:40]])
        str_p = f"  {clean_a:<20}: " + "".join(["█" if x > 0 else "░" for x in v_p_centered[:40]])

        self.log_output.append(str_b)
        self.log_output.append(str_p)
        self.log_output.append("-" * 65)

        if score > 35.0:
            self.log_output.append(f"  ✅ ВЕРДИКТ: Ритмический вшитый код совпадает!")
        else:
            self.log_output.append(f"  ❌ ВЕРДИКТ: Ритмические остовы независимы (Сходство: {score:.2f}%).")

    def verify_melody_harmony(self, matrix_p_mel: np.ndarray, matrix_b_mel: np.ndarray, name_a: str, name_b: str):
        """
        УЛУЧШЕННЫЙ алгоритм Чвана для MELODY_ROW:
        1. Схлопывает матрицы в векторы энергии.
        2. Применяет сильное сглаживание (sigma=15.0) для выделения аккордовых плато.
        3. Нормализует векторы и использует кросс-корреляцию для поиска сдвига.
        """
        self.log_output.append(f"  -> Объект А (Гармония): {name_a[:25]}")
        self.log_output.append(f"  -> Объект Б (Гармония): {name_b[:25]}")

        # Шаг 1: Схлопываем 2D-матрицы мелодий по вертикали (ось частот) в 1D-векторы энергии
        vector_a = np.sum(matrix_p_mel.astype(np.float64), axis=0)
        vector_b = np.sum(matrix_b_mel.astype(np.float64), axis=0)

        min_len = min(len(vector_a), len(vector_b))
        v_a_trimmed = vector_a[:min_len]
        v_b_trimmed = vector_b[:min_len]

        # Шаг 2: Сильное сглаживание для превращения нот в аккордовые плато
        # Sigma увеличена до 15.0 для игнорирования ритма игры и выделения гармонии
        v_a_smoothed = ndimage.gaussian_filter1d(v_a_trimmed, sigma=15.0)
        v_b_smoothed = ndimage.gaussian_filter1d(v_b_trimmed, sigma=15.0)

        # Шаг 3: Нормализация векторов (Zero-mean, Unit-variance)
        def normalize(vec):
            mean = np.mean(vec)
            std = np.std(vec)
            if std == 0: return vec - mean
            return (vec - mean) / std

        v_a_norm = normalize(v_a_smoothed)
        v_b_norm = normalize(v_b_smoothed)

        # Шаг 4: Поиск максимального сходства через кросс-корреляцию
        correlation = np.correlate(v_a_norm, v_b_norm, mode='full')

        max_corr_idx = np.argmax(correlation)
        max_corr_value = correlation[max_corr_idx]

        # Нормализуем значение корреляции относительно длины вектора
        harmony_score_raw = max_corr_value / min_len
        harmony_score = min(harmony_score_raw * 100.0, 100.0)

        # Вычисляем сдвиг
        shift = max_corr_idx - (min_len - 1)

        clean_a = name_a.replace('_mp3', '').replace('_wav', '')[:18]
        clean_b = name_b.replace('_mp3', '').replace('_wav', '')[:18]

        self.log_output.append(f"  -> Длина гармонической ленты: {min_len} квантов времени.")
        self.log_output.append(f"  -> Обнаруженный временной сдвиг: {shift} кадров")
        self.log_output.append(f"  -> ТОПОЛОГИЧЕСКОЕ СХОДСТВО АККОРДОВ = {harmony_score:.2f}%")
        self.log_output.append("-" * 65)

        # 5. Визуализация волнового контура гармонии в лог
        self.log_output.append("  [КОНТУР ГАРМОНИЧЕСКОЙ ВОЛНЫ (Нормализованный)]:")

        str_b = f"  {clean_b:<18}: " + "".join(["█" if x > 0 else "░" for x in v_b_norm[:40]])
        str_p = f"  {clean_a:<18}: " + "".join(["█" if x > 0 else "░" for x in v_a_norm[:40]])

        self.log_output.append(str_b)
        self.log_output.append(str_p)
        self.log_output.append("-" * 65)

        # ПОНИЖЕННЫЙ ПОРОГ ДЛЯ РАЗНЫХ ИСПОЛНЕНИЙ (было 60.0, стало 45.0)
        if harmony_score > 45.0:
            self.log_output.append(f"  ✅ ГАРМОНИЧЕСКИЙ ИНВАРИАНТ ПОДТВЕРЖДЕН!")
            self.log_output.append(f"     Движок MOZART обнаружил структурное сходство аккордов.")
        else:
            self.log_output.append(f"  ❌ Топологического сходства аккордов на данном участке не найдено.")
        self.log_output.append("=" * 65)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MozartAudioAnalyzerWindow()
    window.show()
    sys.exit(app.exec())