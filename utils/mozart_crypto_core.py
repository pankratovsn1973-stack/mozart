# -*- coding: utf-8 -*-
# Путь: /home/sergey/Documents/configurate/layer2_server/mozart_crypto_core.py
# Описание: Финальное детерминированное ядро криптозащиты Mozart ERP с полновесным базисом Галуа.

import os
import numpy as np
import librosa
import scipy.ndimage as ndimage


class MozartCryptoEngine:
    def __init__(self, p=257, n_freq=128, n_time=100, music_dir="/home/sergey/Documents/configurate/music_pool"):
        self.P = p
        self.N_FREQ = n_freq
        self.N_TIME = n_time
        # Порог канонической гладкости Панкратова. Всё, что ниже — музыка, выше — какофония.
        self.TAU_THRESHOLD = 45.0
        self.MUSIC_DIR = music_dir

    def select_stochastic_track(self):
        if not os.path.exists(self.MUSIC_DIR):
            os.makedirs(self.MUSIC_DIR, exist_ok=True)
            return None, 1, 1

        valid_extensions = ('.mp3', '.wav', '.ogg', '.flac')
        all_tracks = [f for f in os.listdir(self.MUSIC_DIR) if f.lower().endswith(valid_extensions)]
        all_tracks.sort()

        total_files = len(all_tracks)
        if total_files == 0:
            return None, 0, 0

        if total_files == 1:
            return os.path.join(self.MUSIC_DIR, all_tracks), 1, 1

        SL = int(np.random.randint(1, 1000001))
        TR = int(np.random.randint(2, total_files + 1))

        target_index = (SL * TR) % TR
        final_index = target_index % total_files

        return os.path.join(self.MUSIC_DIR, all_tracks[final_index]), SL, TR

    def generate_carrier_from_file(self, file_path, sl_seed):
        """Формирует гладкое многообразие методом прямого канонического среза."""
        if file_path is None or not os.path.exists(file_path):
            t_axis = np.linspace(0, 4 * np.pi, self.N_TIME)
            f_trajectory = np.sin(t_axis) * (self.N_FREQ // 4) + (self.N_FREQ // 2)
            surface = np.zeros((self.N_FREQ, self.N_TIME))
            for f in range(self.N_TIME):
                center = int(f_trajectory[f])
                surface[max(0, center - 3):min(self.N_FREQ, center + 4), f] = 1.0
            return np.floor(surface * (self.P - 1)).astype(np.int64)

        try:
            y, sr = librosa.load(file_path, sr=22050, duration=8.0)
            stft = librosa.stft(y, n_fft=2048, hop_length=512)
            matrix_orig = np.abs(stft)

            matrix_harmonic, _ = librosa.decompose.hpss(matrix_orig, margin=2.0)

            slice_freq = min(self.N_FREQ, matrix_harmonic.shape)
            slice_time = min(self.N_TIME, matrix_harmonic.shape)

            clean_slice = np.zeros((self.N_FREQ, self.N_TIME))
            clean_slice[:slice_freq, :slice_time] = matrix_harmonic[:slice_freq, :slice_time]

            # Разглаживаем остов
            clean_slice = ndimage.gaussian_filter(clean_slice, sigma=1.2)

            max_val = np.max(clean_slice) + 1e-6
            gf_carrier = np.floor((clean_slice / max_val) * (self.P - 1)).astype(np.int64)
            return gf_carrier

        except Exception:
            return self.generate_carrier_from_file(None, sl_seed)

    def generate_keypair(self):
        """ИСПРАВЛЕНО: Открытый ключ A теперь является ПОЛНОВЕСНЫМ случайным многообразием поля Галуа."""
        matrix_A = np.random.randint(0, self.P, size=(self.N_FREQ, self.N_FREQ), dtype=np.int64)
        secret_s = np.random.randint(0, self.P, size=(self.N_FREQ, self.N_TIME), dtype=np.int64)
        return matrix_A, secret_s

    def encapsulate_key(self, matrix_A, symmetric_key, file_path, sl_seed):
        """Шифрование под полновесным открытым ключом Пети с каскадным размножением."""
        gf_carrier = self.generate_carrier_from_file(file_path, sl_seed)

        key_bytes = symmetric_key.encode("utf-8")
        msg_vector = np.array([int(b) for b in key_bytes], dtype=np.int64)
        msg_len = len(msg_vector)

        # Контролируемый пространственный туман Гаусса (ошибки 'e')
        raw_noise = np.random.normal(loc=0.0, scale=12.0, size=(self.N_FREQ, self.N_TIME))
        smooth_noise = ndimage.gaussian_filter(raw_noise, sigma=2.0)
        noise_e = np.round(smooth_noise).astype(np.int64)

        np.random.seed(sl_seed + 500)
        shared_s = np.random.randint(0, self.P, size=(self.N_FREQ, self.N_TIME), dtype=np.int64)

        # Инкапсуляция LWE: b = (A * s + gf_carrier + e) mod P
        packet_b = np.mod(matrix_A @ shared_s + gf_carrier + noise_e, self.P)

        # Тотально-каскадное размазывание симметричного ключа по всей площади
        idx_counter = 0
        for f in range(self.N_TIME):
            for q in range(self.N_FREQ):
                packet_b[q, f] = (packet_b[q, f] + msg_vector[idx_counter % msg_len]) % self.P
                idx_counter += 1

        return packet_b

    def calculate_surface_tau(self, matrix):
        """Расчет удельной изрезанности дискретной канонической поверхности."""
        diff_x = np.diff(matrix, axis=1)
        diff_y = np.diff(matrix, axis=0)
        tau = np.sum(np.abs(diff_x)) + np.sum(np.abs(diff_y))
        return tau / float(matrix.size)

    def decapsulate_and_verify(self, matrix_A, packet_b, secret_s, symmetric_key_len):
        """Декапсуляция ловушкой s. Демонстрирует бритвенно-точный скачок тау при атаке."""
        ax_s = matrix_A @ secret_s
        gf_recovered = (packet_b - ax_s) % self.P

        # Считаем изрезанность прямо на целочисленной дискретной матрице Галуа
        tau_index = self.calculate_surface_tau(gf_recovered)

        if tau_index < self.TAU_THRESHOLD:
            extracted_bytes = []
            idx_counter = 0
            for f in range(self.N_TIME):
                for q in range(self.N_FREQ):
                    if idx_counter < symmetric_key_len:
                        extracted_bytes.append(int(gf_recovered[q, f]))
                        idx_counter += 1
            return True, tau_index, extracted_bytes
        else:
            return False, tau_index, None
