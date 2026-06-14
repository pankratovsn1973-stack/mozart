# -*- coding: utf-8 -*-
"""
Оценка музыкальности по методу Панкратова.
Чем ниже тау - тем глаже поверхность, тем "музыкальнее".
"""

import os
import numpy as np
import librosa
import scipy.ndimage as ndimage
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime


class MusicEvaluator:
    """Оценщик музыкальности по методу канонической гладкости Панкратова."""

    def __init__(self, p=257, n_freq=128, n_time=100):
        self.P = p
        self.N_FREQ = n_freq
        self.N_TIME = n_time
        self.TAU_THRESHOLD = 45.0  # Порог Панкратова

        # Шкала музыкальности
        self.MUSICALITY_SCALE = {
            (0, 10): "🎵 ГЕНИАЛЬНО - Эталонная гладкость",
            (10, 20): "🎶 ПРЕКРАСНО - Высокая музыкальность",
            (20, 30): "🎵 ХОРОШО - Качественная музыка",
            (30, 40): "👍 НОРМАЛЬНО - Приемлемая гладкость",
            (40, 45): "🤔 НА ГРАНИ - Слегка нервная, но ещё музыка",
            (45, 60): "⚠️ СОМНИТЕЛЬНО - На грани какофонии",
            (60, 80): "😬 НЕРВНО - Очень нервная музыка",
            (80, 100): "🤯 РАЗРЫВ ШАБЛОНА - Крайне нестабильная",
            (100, 200): "💥 КАКОФОНИЯ - Это уже не музыка",
            (200, float('inf')): "🔥 ХАОС - Абсолютный шум"
        }

    def generate_surface_from_file(self, file_path, sl_seed=42, duration=8.0):
        """Генерирует каноническую поверхность из аудиофайла."""
        try:
            np.random.seed(sl_seed)

            # Загрузка аудио
            y, sr = librosa.load(file_path, sr=22050, duration=duration)

            # STFT
            stft = librosa.stft(y, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)

            # Выделение гармонической составляющей
            harmonic, _ = librosa.decompose.hpss(magnitude, margin=2.0)

            # Интерполяция до нужного размера
            from scipy.ndimage import zoom
            zoom_freq = self.N_FREQ / harmonic.shape[0]
            zoom_time = self.N_TIME / harmonic.shape[1]
            surface = zoom(harmonic, (zoom_freq, zoom_time), order=3)
            surface = surface[:self.N_FREQ, :self.N_TIME]

            # Сглаживание
            surface = ndimage.gaussian_filter(surface, sigma=1.2)

            # Нормализация в поле Галуа (опционально)
            max_val = np.max(surface) + 1e-6
            surface_gf = np.floor((surface / max_val) * (self.P - 1)).astype(np.int64)

            return surface, surface_gf

        except Exception as e:
            print(f"Ошибка обработки {file_path}: {e}")
            return None, None

    def calculate_tau(self, surface):
        """Расчет индекса изрезанности Панкратова."""
        if surface is None or surface.size == 0:
            return float('inf')

        diff_x = np.diff(surface, axis=1)
        diff_y = np.diff(surface, axis=0)
        tau = np.sum(np.abs(diff_x)) + np.sum(np.abs(diff_y))
        tau = tau / float(surface.size)

        return tau

    def evaluate_musicality(self, tau):
        """Оценка музыкальности по шкале Панкратова."""
        for (low, high), description in self.MUSICALITY_SCALE.items():
            if low <= tau < high:
                return description

        # Если тау очень высокое
        if tau >= 200:
            return "💥 АБСОЛЮТНЫЙ ХАОС - Это даже не шум, это белый шум в кубе"

        return "📊 НЕОПРЕДЕЛЕННО"

    def analyze_file(self, file_path, verbose=True):
        """Полный анализ музыкального файла."""
        print("\n" + "=" * 70)
        print(f" АНАЛИЗ: {os.path.basename(file_path)}")
        print("=" * 70)

        surface, surface_gf = self.generate_surface_from_file(file_path)

        if surface is None:
            print("  ❌ НЕ УДАЛОСЬ ОБРАБОТАТЬ ФАЙЛ")
            return None

        tau = self.calculate_tau(surface)
        verdict = self.evaluate_musicality(tau)

        print(f"\n  📊 ИНДЕКС ИЗРЕЗАННОСТИ ТАУ = {tau:.4f}")
        print(f"  🎯 ПОРОГ ПАНКРАТОВА = {self.TAU_THRESHOLD}")
        print(f"\n  🎵 ВЕРДИКТ: {verdict}")

        if tau < self.TAU_THRESHOLD:
            print(f"  ✅ СТАТУС: МУЗЫКА - Произведение прошло проверку гладкости")
        else:
            print(f"  ❌ СТАТУС: КАКОФОНИЯ - Произведение не прошло проверку")

        # Дополнительная статистика
        print(f"\n  📈 СТАТИСТИКА:")
        print(f"     - Среднее значение: {np.mean(surface):.2f}")
        print(f"     - Стандартное отклонение: {np.std(surface):.2f}")
        print(f"     - Минимум: {np.min(surface):.2f}")
        print(f"     - Максимум: {np.max(surface):.2f}")

        return {
            'file': file_path,
            'tau': tau,
            'verdict': verdict,
            'is_music': tau < self.TAU_THRESHOLD,
            'surface': surface,
            'surface_gf': surface_gf
        }

    def compare_tracks(self, file_paths):
        """Сравнение нескольких треков."""
        print("\n" + "=" * 70)
        print(" СРАВНИТЕЛЬНЫЙ АНАЛИЗ ТРЕКОВ ")
        print("=" * 70)

        results = []
        for file_path in file_paths:
            surface, _ = self.generate_surface_from_file(file_path)
            if surface is not None:
                tau = self.calculate_tau(surface)
                results.append((os.path.basename(file_path), tau))

        # Сортировка по тау (от самого гладкого к самому шумному)
        results.sort(key=lambda x: x[1])

        print("\n  РЕЙТИНГ МУЗЫКАЛЬНОСТИ (от гладкого к нервному):")
        print("  " + "-" * 60)
        for i, (name, tau) in enumerate(results, 1):
            if tau < self.TAU_THRESHOLD:
                status = "🎵"
            else:
                status = "💥"

            bar_len = min(50, int(tau / 4))
            bar = "█" * bar_len + "░" * (50 - bar_len)
            print(f"  {i:2}. {status} {name[:35]:<35} тау={tau:6.2f} [{bar}]")

        return results

    def save_surface_image(self, surface, title, filename):
        """Сохраняет поверхность как изображение."""
        plt.figure(figsize=(14, 8))

        cmap = LinearSegmentedColormap.from_list(
            'musicality',
            ['darkblue', 'cyan', 'yellow', 'orange', 'red'],
            N=256
        )

        plt.imshow(surface, aspect='auto', cmap=cmap)
        plt.colorbar(label='Амплитуда')
        plt.title(title, fontsize=14, fontweight='bold')
        plt.xlabel('Время')
        plt.ylabel('Частота')

        tau = self.calculate_tau(surface)
        plt.text(0.02, 0.98, f'Тау Панкратова = {tau:.4f}',
                 transform=plt.gca().transAxes, fontsize=10,
                 verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        plt.tight_layout()
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  Сохранено: {filename}")


def evaluate_tango():
    """Оценка танго и других стилей."""

    evaluator = MusicEvaluator()

    # Путь к директории с музыкой
    music_dir = "/home/sergey/Documents/configurate"

    # Находим все аудиофайлы
    valid_ext = ('.mp3', '.wav', '.ogg', '.flac')
    all_files = [os.path.join(music_dir, f) for f in os.listdir(music_dir)
                 if f.lower().endswith(valid_ext)]

    print("=" * 70)
    print("   ОЦЕНКА МУЗЫКАЛЬНОСТИ ПО МЕТОДУ ПАНКРАТОВА")
    print("   Чем ниже тау - тем музыка глаже")
    print("=" * 70)

    print(f"\nНайдено файлов: {len(all_files)}")

    # Анализ каждого файла
    all_results = []
    for file_path in all_files:
        result = evaluator.analyze_file(file_path, verbose=True)
        if result:
            all_results.append(result)

            # Сохраняем визуализацию для каждого файла
            timestamp = datetime.now().strftime("%H%M%S")
            name = os.path.basename(file_path).replace('.', '_')
            evaluator.save_surface_image(
                result['surface'],
                f"{os.path.basename(file_path)}\nТау = {result['tau']:.4f}",
                f"surface_{name}_{timestamp}.png"
            )

    # Общий рейтинг
    if all_results:
        print("\n" + "=" * 70)
        print(" ИТОГОВЫЙ РЕЙТИНГ МУЗЫКАЛЬНОСТИ ")
        print("=" * 70)

        sorted_results = sorted(all_results, key=lambda x: x['tau'])

        print("\n  🏆 РЕЙТИНГ (от самого гладкого к самому нервному):")
        print("  " + "-" * 70)

        for i, result in enumerate(sorted_results, 1):
            name = os.path.basename(result['file'])
            tau = result['tau']

            if tau < 10:
                medal = "🏆"
            elif tau < 20:
                medal = "🥈"
            elif tau < 30:
                medal = "🥉"
            else:
                medal = "📊"

            # Визуальная шкала
            bar = "█" * min(50, int(tau)) + "░" * max(0, 50 - int(tau))

            status = "✅ МУЗЫКА" if result['is_music'] else "❌ КАКОФОНИЯ"

            print(f"  {i:2}. {medal} {name[:40]:<40} тау={tau:6.2f} [{bar}] {status}")

        # Средняя оценка
        avg_tau = np.mean([r['tau'] for r in all_results])
        print(f"\n  📊 СРЕДНИЙ ТАУ по коллекции: {avg_tau:.2f}")

        if avg_tau < 45:
            print(f"  ✅ Коллекция в целом МУЗЫКАЛЬНА (среднее ниже порога)")
        else:
            print(f"  ❌ Коллекция в целом КАКОФОНИЧНА (среднее выше порога)")

    return all_results


def evaluate_single_file(file_path):
    """Оценка одного конкретного файла."""
    evaluator = MusicEvaluator()
    result = evaluator.analyze_file(file_path, verbose=True)

    if result and result['surface'] is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        evaluator.save_surface_image(
            result['surface'],
            f"{os.path.basename(file_path)}\nТау Панкратова = {result['tau']:.4f}",
            f"evaluation_{timestamp}.png"
        )

    return result


if __name__ == "__main__":
    import sys

    # Если передан конкретный файл - анализируем его
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            evaluate_single_file(file_path)
        else:
            print(f"Файл не найден: {file_path}")
    else:
        # Иначе анализируем всю директорию
        evaluate_tango()