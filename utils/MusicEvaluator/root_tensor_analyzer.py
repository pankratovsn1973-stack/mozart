# utils/MusicEvaluator/root_tensor_analyzer.py
# -*- coding: utf-8 -*-
"""
Анализатор ритмического сходства v7.0
  - ТОЛЬКО РИТМ (percussive слой через HPSS)
  - Beat-synchronous паттерны: для каждого такта — onset-паттерн (16 отсчётов)
  - Матрица соответствий тактов A × B через косинусное расстояние
  - Поиск диагональных участков совпадения
  - Корневая поверхность Панкратова как дополнительная метрика
  - Аудио-экспорт найденных фрагментов (A, B, MIX, DIFF)
"""

import os
import sys
import traceback
from datetime import datetime

import numpy as np
import librosa
import soundfile as sf
import scipy.ndimage as ndi

import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QFormLayout, QLineEdit, QPushButton,
                               QTextEdit, QFileDialog, QMessageBox,
                               QProgressBar, QDoubleSpinBox, QSpinBox, QTabWidget,
                               QWidget, QCheckBox)
from PySide6.QtCore import QThread, Signal, QUrl
from PySide6.QtGui import QFont, QDesktopServices


# ============================================================================
#  УТИЛИТЫ
# ============================================================================
def _safe_audio_write(path, y, sr):
    y = np.asarray(y, dtype=np.float32)
    if y.size == 0:
        return False
    peak = float(np.max(np.abs(y)))
    if peak > 1e-9:
        y = y / peak * 0.95
    try:
        sf.write(path, y, sr, subtype='PCM_16')
        return True
    except Exception:
        return False


def _resize_bilinear(src, target_shape):
    th, tw = target_shape
    sh, sw = src.shape
    if sh == th and sw == tw:
        return src.astype(np.float64, copy=False)
    ys = np.linspace(0, sh - 1, th)
    xs = np.linspace(0, sw - 1, tw)
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    y1 = np.minimum(y0 + 1, sh - 1)
    x1 = np.minimum(x0 + 1, sw - 1)
    wy = (ys - y0)[:, None]
    wx = (xs - x0)[None, :]
    v00 = src[np.ix_(y0, x0)]
    v01 = src[np.ix_(y0, x1)]
    v10 = src[np.ix_(y1, x0)]
    v11 = src[np.ix_(y1, x1)]
    return (v00 * (1 - wy) * (1 - wx) +
            v10 * wy * (1 - wx) +
            v01 * (1 - wy) * wx +
            v11 * wy * wx)


# ============================================================================
#  КОРНЕВАЯ ПОВЕРХНОСТЬ
# ============================================================================
class RootSurfaceEngine:
    def __init__(self, p=257, rank_priority='sum'):
        self.P = p
        self.rank_priority = rank_priority

    def _quantize(self, m):
        mx = float(np.max(m)) + 1e-12
        q = np.floor((m / mx) * (self.P - 1)).astype(np.int64)
        return np.clip(q, 0, self.P - 1)

    @staticmethod
    def _weights(vec):
        v = vec.astype(np.float64)
        return np.array([v.sum(), (v ** 2).sum(), (v ** 3).sum()])

    def _rank_axis(self, m, axis):
        n = m.shape[axis]
        w = np.empty((n, 3))
        if axis == 0:
            for i in range(n):
                w[i] = self._weights(m[i, :])
        else:
            for j in range(n):
                w[j] = self._weights(m[:, j])
        if self.rank_priority == 'cube':
            return np.lexsort((w[:, 0], w[:, 1], w[:, 2]))
        return np.lexsort((w[:, 2], w[:, 1], w[:, 0]))

    def build(self, raw):
        n_f, n_t = raw.shape
        if n_f < 2 or n_t < 2:
            raise ValueError(f"Матрица слишком мала: {raw.shape}")
        gf = self._quantize(raw)
        ro = self._rank_axis(gf, 0)
        co = self._rank_axis(gf, 1)
        canon = gf[ro, :][:, co]

        sy = (n_f - 1) / (self.P - 1)
        sx = (n_t - 1) / (self.P - 1)
        fy = np.arange(self.P) * sy
        fx = np.arange(self.P) * sx
        iy = np.floor(fy).astype(int)
        dy = (fy - iy)[:, None]
        ix = np.floor(fx).astype(int)
        dx = (fx - ix)[None, :]
        iy_n = np.minimum(iy + 1, n_f - 1)
        ix_n = np.minimum(ix + 1, n_t - 1)

        v00 = canon[np.ix_(iy, ix)]
        v01 = canon[np.ix_(iy, ix_n)]
        v10 = canon[np.ix_(iy_n, ix)]
        v11 = canon[np.ix_(iy_n, ix_n)]
        return (v00 * (1 - dy) * (1 - dx) +
                v10 * dy * (1 - dx) +
                v01 * (1 - dy) * dx +
                v11 * dy * dx)

    def gap(self, sa, sb):
        raw = float(np.sum(np.abs(sa - sb)))
        return raw / (sa.size * (self.P - 1))


# ============================================================================
#  ДВИЖОК — ТОЛЬКО РИТМ
# ============================================================================
class RhythmEngineV7:
    def __init__(self):
        self.SR = 22050
        self.HOP = 512
        self.N_FFT = 2048
        self.surface = RootSurfaceEngine()

    # ------------------------------------------------------------------
    def hpss_percussive(self, path, duration=0.0):
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        kw = {'sr': self.SR, 'mono': True}
        if duration and duration > 0:
            kw['duration'] = duration
        y, _ = librosa.load(path, **kw)
        if y.size == 0:
            raise ValueError("Пустой файл")

        D = librosa.stft(y, n_fft=self.N_FFT, hop_length=self.HOP)
        mag, phase = np.abs(D), np.angle(D)

        hm = ndi.median_filter(mag, size=(1, 15))
        pm = ndi.median_filter(mag, size=(15, 1))
        eps = 1e-10
        p_mask = pm / (hm + pm + eps)

        y_p = librosa.istft(mag * p_mask * np.exp(1j * phase),
                            hop_length=self.HOP, n_fft=self.N_FFT,
                            length=len(y))
        return {
            'y_perc': y_p.astype(np.float32),
            'sr': self.SR,
            'hop': self.HOP,
            'duration': len(y) / self.SR,
        }

    # ------------------------------------------------------------------
    def onset_env(self, y, sr):
        env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=self.HOP)
        return env.astype(np.float32)

    # ------------------------------------------------------------------
    def get_beats(self, y, sr):
        tempo, beats = librosa.beat.beat_track(
            y=y, sr=sr, hop_length=self.HOP, trim=False)
        return float(tempo), beats

    # ------------------------------------------------------------------
    def beat_patterns(self, onset_env, beats, n_subdivisions=16):
        """
        Для каждого такта (между beats) извлекаем паттерн onset-энергии,
        нормализованный к n_subdivisions отсчётов и z-нормированный.
        """
        if len(beats) < 2:
            return np.zeros((0, n_subdivisions), dtype=np.float32)

        patterns = []
        for i in range(len(beats) - 1):
            s = beats[i]
            e = beats[i + 1]
            if e <= s:
                continue
            seg = onset_env[s:e]
            if len(seg) < 2:
                patterns.append(np.zeros(n_subdivisions, dtype=np.float32))
                continue
            xs = np.linspace(0, len(seg) - 1, n_subdivisions)
            resampled = np.interp(xs, np.arange(len(seg)), seg)
            mu = resampled.mean()
            sd = resampled.std() + 1e-9
            normed = (resampled - mu) / sd
            patterns.append(normed.astype(np.float32))

        if not patterns:
            return np.zeros((0, n_subdivisions), dtype=np.float32)
        return np.vstack(patterns)

    # ------------------------------------------------------------------
    def beat_similarity_matrix(self, pat_a, pat_b):
        """
        M[i, j] = косинусное расстояние между паттернами A_i и B_j.
        """
        na = pat_a.shape[0]
        nb = pat_b.shape[0]
        if na == 0 or nb == 0:
            return np.zeros((na, nb), dtype=np.float32)

        def norm_rows(P):
            nrm = np.linalg.norm(P, axis=1, keepdims=True) + 1e-9
            return P / nrm

        A = norm_rows(pat_a)
        B = norm_rows(pat_b)
        dot = A @ B.T
        M = 1.0 - dot
        return M.astype(np.float32)

    # ------------------------------------------------------------------
    def find_diagonal_runs(self, M, threshold=0.4, min_run=4):
        """
        Ищем непрерывные диагональные участки, где M[i, j] < threshold
        при движении по диагонали (i+1, j+1).
        Возвращает список сегментов.
        """
        if M.size == 0:
            return []

        na, nb = M.shape
        visited = np.zeros((na, nb), dtype=bool)
        runs = []

        for i0 in range(na):
            for j0 in range(nb):
                if visited[i0, j0] or M[i0, j0] >= threshold:
                    continue
                # Пропускаем, если это продолжение диагонали
                i_prev, j_prev = i0 - 1, j0 - 1
                if i_prev >= 0 and j_prev >= 0 and \
                   M[i_prev, j_prev] < threshold:
                    continue

                costs = []
                i_start, j_start = i0, j0
                i, j = i0, j0
                while i < na and j < nb and M[i, j] < threshold:
                    costs.append(M[i, j])
                    visited[i, j] = True
                    i += 1
                    j += 1

                if len(costs) >= min_run:
                    runs.append({
                        'i_start': i_start,
                        'i_end': i - 1,
                        'j_start': j_start,
                        'j_end': j - 1,
                        'length': len(costs),
                        'mean_cost': float(np.mean(costs)),
                    })

        runs.sort(key=lambda r: r['mean_cost'])
        return runs

    # ------------------------------------------------------------------
    def surface_score(self, y_a, y_b, frame_i_start, frame_i_end,
                      frame_j_start, frame_j_end):
        def frag(y, s, e):
            hop, n_fft = self.HOP, self.N_FFT
            s_p = max(0, int(s) * hop)
            e_p = min(len(y), int(e) * hop + n_fft)
            if e_p - s_p < n_fft:
                return None
            return np.abs(librosa.stft(y[s_p:e_p], n_fft=n_fft,
                                       hop_length=hop))

        Sa = frag(y_a, frame_i_start, frame_i_end)
        Sb = frag(y_b, frame_j_start, frame_j_end)
        if Sa is None or Sb is None:
            return float('inf')

        T = min(Sa.shape[1], Sb.shape[1])
        if T < 4:
            return float('inf')
        Sa, Sb = Sa[:, :T], Sb[:, :T]

        target = (128, T)
        Sa = _resize_bilinear(Sa, target)
        Sb = _resize_bilinear(Sb, target)

        try:
            sa = self.surface.build(Sa)
            sb = self.surface.build(Sb)
        except ValueError:
            return float('inf')
        return self.surface.gap(sa, sb)

    # ------------------------------------------------------------------
    def analyze(self, path_a, path_b, duration=0.0,
                threshold=0.4, min_run=4,
                top_n=5, progress_cb=None):
        def step(m):
            if progress_cb:
                progress_cb(m)

        step("HPSS: percussive A...")
        hp_a = self.hpss_percussive(path_a, duration)

        step("HPSS: percussive B...")
        hp_b = self.hpss_percussive(path_b, duration)

        sr = hp_a['sr']
        hop = hp_a['hop']
        fps = sr / hop

        step("Onset-огибающие...")
        onset_a = self.onset_env(hp_a['y_perc'], sr)
        onset_b = self.onset_env(hp_b['y_perc'], sr)

        step("Beat-tracking A...")
        tempo_a, beats_a = self.get_beats(hp_a['y_perc'], sr)

        step("Beat-tracking B...")
        tempo_b, beats_b = self.get_beats(hp_b['y_perc'], sr)

        if progress_cb:
            progress_cb(f"  Tempo A = {tempo_a:.1f} BPM, "
                        f"beats = {len(beats_a)}")
            progress_cb(f"  Tempo B = {tempo_b:.1f} BPM, "
                        f"beats = {len(beats_b)}")

        if len(beats_a) < 3 or len(beats_b) < 3:
            return {
                'hp_a': hp_a, 'hp_b': hp_b,
                'fps': fps,
                'tempo_a': tempo_a, 'tempo_b': tempo_b,
                'n_beats_a': len(beats_a), 'n_beats_b': len(beats_b),
                'runs': [],
                'msg': "Слишком мало beats",
                'M': None,
            }

        step("Beat-synchronous паттерны...")
        patterns_a = self.beat_patterns(onset_a, beats_a, n_subdivisions=16)
        patterns_b = self.beat_patterns(onset_b, beats_b, n_subdivisions=16)

        if progress_cb:
            progress_cb(f"  Паттернов A = {patterns_a.shape[0]}, "
                        f"B = {patterns_b.shape[0]}")

        step("Матрица соответствий тактов...")
        M = self.beat_similarity_matrix(patterns_a, patterns_b)

        step(f"Поиск диагональных совпадений "
             f"(threshold={threshold}, min_run={min_run})...")
        runs = self.find_diagonal_runs(M, threshold=threshold,
                                       min_run=min_run)

        if progress_cb:
            progress_cb(f"  Найдено диагональных сегментов: {len(runs)}")

        step("Корневая поверхность для топ-кандидатов...")
        for r in runs[:top_n * 3]:
            frame_i_start = int(beats_a[r['i_start']])
            frame_i_end = int(beats_a[min(r['i_end'] + 1, len(beats_a) - 1)])
            frame_j_start = int(beats_b[r['j_start']])
            frame_j_end = int(beats_b[min(r['j_end'] + 1, len(beats_b) - 1)])

            r['time_a_start'] = frame_i_start / fps
            r['time_a_end'] = frame_i_end / fps
            r['time_b_start'] = frame_j_start / fps
            r['time_b_end'] = frame_j_end / fps

            r['surface_gap'] = self.surface_score(
                hp_a['y_perc'], hp_b['y_perc'],
                frame_i_start, frame_i_end,
                frame_j_start, frame_j_end)

            r['frame_i_start'] = frame_i_start
            r['frame_i_end'] = frame_i_end
            r['frame_j_start'] = frame_j_start
            r['frame_j_end'] = frame_j_end

        # Ранжируем по surface_gap
        runs_ranked = sorted(
            [r for r in runs[:top_n * 3] if 'surface_gap' in r],
            key=lambda r: r['surface_gap']
        )[:top_n]

        return {
            'hp_a': hp_a, 'hp_b': hp_b,
            'fps': fps,
            'tempo_a': tempo_a, 'tempo_b': tempo_b,
            'n_beats_a': len(beats_a), 'n_beats_b': len(beats_b),
            'beats_a': beats_a, 'beats_b': beats_b,
            'runs': runs_ranked,
            'M': M,
            'msg': None,
        }


# ============================================================================
#  WORKER
# ============================================================================
class Worker(QThread):
    log_signal = Signal(str)
    finished = Signal(dict)

    def __init__(self, engine, path_a, path_b, output_dir,
                 duration=0.0, threshold=0.4, min_run=4, top_n=5,
                 export_audio=True):
        super().__init__()
        self.engine = engine
        self.path_a = path_a
        self.path_b = path_b
        self.output_dir = output_dir
        self.duration = duration
        self.threshold = threshold
        self.min_run = min_run
        self.top_n = top_n
        self.export_audio = export_audio

    def run(self):
        result = None
        try:
            def cb(m):
                self.log_signal.emit(f"[INFO] {m}")

            data = self.engine.analyze(
                self.path_a, self.path_b,
                duration=self.duration,
                threshold=self.threshold,
                min_run=self.min_run,
                top_n=self.top_n,
                progress_cb=cb)

            fps = data['fps']
            self.log_signal.emit("")
            self.log_signal.emit("=== РЕЗУЛЬТАТЫ (РИТМ) ===")
            self.log_signal.emit(f"Tempo A = {data['tempo_a']:.1f} BPM")
            self.log_signal.emit(f"Tempo B = {data['tempo_b']:.1f} BPM")

            if data.get('msg'):
                self.log_signal.emit(f"[WARN] {data['msg']}")
            else:
                self.log_signal.emit(
                    f"Найдено сегментов: {len(data['runs'])}")
                for k, r in enumerate(data['runs'], 1):
                    self.log_signal.emit(
                        f"  #{k}: A[{r['time_a_start']:.2f}–"
                        f"{r['time_a_end']:.2f}s] ↔ "
                        f"B[{r['time_b_start']:.2f}–"
                        f"{r['time_b_end']:.2f}s] | "
                        f"длина={r['length']} тактов | "
                        f"beat_cost={r['mean_cost']:.4f} | "
                        f"surface_gap={r['surface_gap']:.6f}")

            paths = self._save_report(data)
            if self.export_audio and data.get('runs'):
                cb("Аудио-экспорт...")
                audio = self._save_audio(data)
                paths.update(audio)

            result = {'data': data, 'paths': paths, 'fps': fps}

        except Exception as e:
            self.log_signal.emit(f"[ERROR] {e}")
            self.log_signal.emit(traceback.format_exc())
        finally:
            self.finished.emit(result)

    # ------------------------------------------------------------------
    def _save_report(self, data):
        os.makedirs(self.output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        pr = os.path.join(self.output_dir, f"rhythm_report_{ts}.txt")

        with open(pr, "w", encoding="utf-8") as f:
            f.write("=== АНАЛИЗ РИТМИЧЕСКОГО СХОДСТВА v7.0 ===\n")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Файл А: {os.path.basename(self.path_a)}\n")
            f.write(f"Файл Б: {os.path.basename(self.path_b)}\n\n")
            f.write(f"Tempo A = {data['tempo_a']:.1f} BPM\n")
            f.write(f"Tempo B = {data['tempo_b']:.1f} BPM\n")
            f.write(f"beats A = {data['n_beats_a']}\n")
            f.write(f"beats B = {data['n_beats_b']}\n\n")

            if data.get('msg'):
                f.write(f"[WARN] {data['msg']}\n")
            else:
                for k, r in enumerate(data['runs'], 1):
                    f.write(f"#{k}: A[{r['time_a_start']:.2f}–"
                            f"{r['time_a_end']:.2f}s] ↔ "
                            f"B[{r['time_b_start']:.2f}–"
                            f"{r['time_b_end']:.2f}s]\n")
                    f.write(f"     длина       = {r['length']} тактов\n")
                    f.write(f"     beat_cost   = {r['mean_cost']:.6f}\n")
                    f.write(f"     surface_gap = {r['surface_gap']:.6f}\n\n")

            f.write("\nИнтерпретация:\n")
            f.write("  beat_cost — косинусное расстояние паттернов тактов\n")
            f.write("  surface_gap — метрика корневой поверхности:\n")
            f.write("    < 0.10 — очень сильное совпадение\n")
            f.write("    0.10-0.20 — сильное\n")
            f.write("    0.20-0.30 — вероятное\n")
            f.write("    > 0.30 — нет совпадения\n")
        return {'report': pr}

    # ------------------------------------------------------------------
    def _save_audio(self, data):
        os.makedirs(self.output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        sr = data['hp_a']['sr']
        hop = data['hp_a']['hop']
        paths = {}

        def cut(y, s_fr, e_fr):
            s = max(0, int(s_fr) * hop)
            e = min(len(y), int(e_fr) * hop + hop)
            return y[s:e]

        for k, r in enumerate(data['runs'], 1):
            a_fr = cut(data['hp_a']['y_perc'],
                       r['frame_i_start'], r['frame_i_end'])
            b_fr = cut(data['hp_b']['y_perc'],
                       r['frame_j_start'], r['frame_j_end'])
            n = min(len(a_fr), len(b_fr))
            if n <= 0:
                continue
            a_fr, b_fr = a_fr[:n], b_fr[:n]

            pa = os.path.join(self.output_dir, f"rhythm{k}_A_{ts}.wav")
            pb = os.path.join(self.output_dir, f"rhythm{k}_B_{ts}.wav")
            pm = os.path.join(self.output_dir, f"rhythm{k}_MIX_{ts}.wav")
            pd = os.path.join(self.output_dir, f"rhythm{k}_DIFF_{ts}.wav")

            if _safe_audio_write(pa, a_fr, sr):
                paths[f'rhythm{k}_A'] = pa
            if _safe_audio_write(pb, b_fr, sr):
                paths[f'rhythm{k}_B'] = pb
            if _safe_audio_write(pm, a_fr + b_fr, sr):
                paths[f'rhythm{k}_MIX'] = pm
            if _safe_audio_write(pd, a_fr - b_fr, sr):
                paths[f'rhythm{k}_DIFF'] = pd

        return paths


# ============================================================================
#  ВИЗУАЛИЗАЦИЯ
# ============================================================================
class MatrixView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.figure = Figure(figsize=(11, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

    def clear(self):
        self.figure.clear()
        self.canvas.draw()

    def show_result(self, result):
        self.figure.clear()
        data = result.get('data', {})
        M = data.get('M')

        if M is None or M.size == 0:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "Нет данных\n(слишком мало beats)",
                    ha='center', va='center')
            ax.axis('off')
            self.canvas.draw()
            return

        ax = self.figure.add_subplot(111)
        im = ax.imshow(M, cmap='viridis', aspect='auto',
                       interpolation='nearest')
        ax.set_xlabel("Такт B")
        ax.set_ylabel("Такт A")
        ax.set_title(f"Матрица соответствий тактов\n"
                     f"Tempo A={data['tempo_a']:.1f}, "
                     f"B={data['tempo_b']:.1f} BPM")

        for r in data.get('runs', []):
            i0, i1 = r['i_start'], r['i_end']
            j0, j1 = r['j_start'], r['j_end']
            ax.plot([j0, j1], [i0, i1], 'r-', linewidth=2, alpha=0.8)

        self.figure.colorbar(im, ax=ax, fraction=0.046)
        self.figure.tight_layout()
        self.canvas.draw()


# ============================================================================
#  GUI
# ============================================================================
class RhythmAnalyzerV7(QDialog):
    def __init__(self):
        super().__init__()
        self.engine = RhythmEngineV7()
        self.worker = None
        self.last_output = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Анализатор ритма v7.0")
        self.resize(1000, 850)
        main = QVBoxLayout(self)

        g = QGroupBox("Файлы")
        l = QFormLayout(g)

        self.btn_a = QPushButton("Выбрать A")
        self.lbl_a = QLineEdit(); self.lbl_a.setReadOnly(True)
        row = QHBoxLayout(); row.addWidget(self.lbl_a); row.addWidget(self.btn_a)
        l.addRow("Объект A:", row)

        self.btn_b = QPushButton("Выбрать B")
        self.lbl_b = QLineEdit(); self.lbl_b.setReadOnly(True)
        row = QHBoxLayout(); row.addWidget(self.lbl_b); row.addWidget(self.btn_b)
        l.addRow("Объект B:", row)

        self.spin_dur = QDoubleSpinBox()
        self.spin_dur.setMinimum(0.0); self.spin_dur.setMaximum(1200.0)
        self.spin_dur.setValue(0.0)
        self.spin_dur.setSpecialValueText("Весь трек")
        l.addRow("Длительность, с:", self.spin_dur)

        main.addWidget(g)

        g2 = QGroupBox("Параметры поиска")
        l2 = QFormLayout(g2)

        self.spin_thresh = QDoubleSpinBox()
        self.spin_thresh.setMinimum(0.05); self.spin_thresh.setMaximum(1.5)
        self.spin_thresh.setValue(0.40); self.spin_thresh.setSingleStep(0.05)
        self.spin_thresh.setDecimals(3)
        l2.addRow("Порог beat_cost:", self.spin_thresh)

        self.spin_minrun = QSpinBox()
        self.spin_minrun.setMinimum(2); self.spin_minrun.setMaximum(64)
        self.spin_minrun.setValue(4)
        l2.addRow("Мин. длина сегмента (тактов):", self.spin_minrun)

        self.spin_topn = QSpinBox()
        self.spin_topn.setMinimum(1); self.spin_topn.setMaximum(20)
        self.spin_topn.setValue(5)
        l2.addRow("Топ-N:", self.spin_topn)

        self.chk_audio = QCheckBox("Сохранять WAV (A, B, MIX, DIFF)")
        self.chk_audio.setChecked(True)
        l2.addRow("", self.chk_audio)

        main.addWidget(g2)

        g3 = QGroupBox("Каталог результатов")
        l3 = QFormLayout(g3)
        self.btn_out = QPushButton("Обзор...")
        self.lbl_out = QLineEdit(
            os.path.expanduser("~/Documents/rhythm_v7"))
        row = QHBoxLayout(); row.addWidget(self.lbl_out); row.addWidget(self.btn_out)
        l3.addRow("Путь:", row)
        main.addWidget(g3)

        ctrl = QHBoxLayout()
        self.btn_start = QPushButton("Запустить")
        self.btn_start.setStyleSheet(
            "font-weight:bold;background:#00838F;color:white;height:30px;")
        self.btn_open = QPushButton("Открыть папку")
        self.btn_open.setEnabled(False)
        self.prog = QProgressBar()
        self.prog.setRange(0, 0); self.prog.hide()
        ctrl.addWidget(self.btn_start); ctrl.addWidget(self.btn_open)
        ctrl.addWidget(self.prog)
        main.addLayout(ctrl)

        tabs = QTabWidget()
        self.log = QTextEdit(); self.log.setReadOnly(True)
        self.log.setFont(QFont("Courier New", 10))
        tabs.addTab(self.log, "Лог")
        self.matrix_view = MatrixView()
        tabs.addTab(self.matrix_view, "Матрица соответствий")
        main.addWidget(tabs)
        self.tabs = tabs

        self.btn_a.clicked.connect(lambda: self.pick(self.lbl_a))
        self.btn_b.clicked.connect(lambda: self.pick(self.lbl_b))
        self.btn_out.clicked.connect(self.pick_dir)
        self.btn_start.clicked.connect(self.start)
        self.btn_open.clicked.connect(self.open_dir)

    def pick(self, le):
        p, _ = QFileDialog.getOpenFileName(
            self, "Аудио", "", "Audio (*.mp3 *.wav *.ogg *.flac *.m4a)")
        if p:
            le.setText(p)

    def pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Каталог")
        if d:
            self.lbl_out.setText(d)

    def open_dir(self):
        if self.last_output and os.path.isdir(self.last_output):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_output))

    def start(self):
        pa = self.lbl_a.text().strip()
        pb = self.lbl_b.text().strip()
        out = self.lbl_out.text().strip()
        if not pa or not pb or not out:
            QMessageBox.warning(self, "Внимание",
                                "Выберите оба файла и каталог!")
            return

        self.log.clear()
        self.matrix_view.clear()
        self.btn_start.setEnabled(False)
        self.btn_open.setEnabled(False)
        self.prog.show()
        self.tabs.setCurrentIndex(0)

        self.worker = Worker(
            self.engine, pa, pb, out,
            duration=self.spin_dur.value(),
            threshold=self.spin_thresh.value(),
            min_run=self.spin_minrun.value(),
            top_n=self.spin_topn.value(),
            export_audio=self.chk_audio.isChecked())
        self.worker.log_signal.connect(self.log.append)
        self.worker.finished.connect(self.done)
        self.worker.start()

    def done(self, result):
        self.btn_start.setEnabled(True)
        self.prog.hide()
        if result is None:
            QMessageBox.critical(self, "Ошибка", "См. лог.")
            return
        self.matrix_view.show_result(result)
        self.tabs.setCurrentIndex(1)
        self.last_output = self.lbl_out.text().strip()
        self.btn_open.setEnabled(True)

        data = result.get('data', {})
        n = len(data.get('runs', []))
        QMessageBox.information(
            self, "Готово",
            f"Найдено сегментов: {n}\n\n"
            f"Смотри лог, матрицу и WAV в:\n{self.last_output}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = RhythmAnalyzerV7()
    w.show()
    sys.exit(app.exec())