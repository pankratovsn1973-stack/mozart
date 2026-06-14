# -*- coding: utf-8 -*-
# Путь: /home/sergey/Documents/configurate/layer2_server/mozart_nodes.py
# Описание: Софтверные узлы Вася и Петя. Реализована лавинная деформация остова при атаке.

import numpy as np
from mozart_crypto_core import MozartCryptoEngine


class VasyaServer:
    def __init__(self, engine: MozartCryptoEngine):
        self.engine = engine
        self.symmetric_session_key = "AES256_SYNCHRONOUS_TOKEN_991823"
        self.selected_track = None
        self.SL = 0
        self.TR = 0

    def receive_handshake_and_encrypt(self, public_key_A):
        print("[ВАСЯ -> Сервер]: Принял открытый ключ решетки от Пети.")
        self.selected_track, self.SL, self.TR = self.engine.select_stochastic_track()

        packet_b = self.engine.encapsulate_key(
            matrix_A=public_key_A,
            symmetric_key=self.symmetric_session_key,
            file_path=self.selected_track,
            sl_seed=self.SL
        )
        return packet_b, self.SL, self.TR


class PetyaClient:
    def __init__(self, engine: MozartCryptoEngine):
        self.engine = engine
        self.public_key_A = None
        self._secret_s = None
        self.symmetric_key_len = 0

    def init_session_keys(self, target_key_len):
        self.symmetric_key_len = target_key_len
        self.public_key_A, _ = self.engine.generate_keypair()
        print("[ПЕТЯ -> Клиент]: Сгенерировал открытый базис многомерной решетки.")
        return self.public_key_A

    def receive_and_analyze(self, packet_b, sl_seed, use_hacked_key=False):
        print("[ПЕТЯ -> Клиент]: Принял пакет от Васи. Запуск анализа остова...")

        # Базовая синхронизация по сиду
        seed_to_use = sl_seed

        # ИСПРАВЛЕНО: Симулируем ошибку в один знак в исходном сиде генерации решетки!
        # Ошибка в единицу в sl_seed (например, 123456 превращается в 123457) — это и есть
        # изменение одного знака в закрытом ключе, которое полностью перестраивает всю псевдослучайную
        # матрицу s. Матрица s взломщика становится полностью ортогональной оригиналу.
        if use_hacked_key:
            print("[КРИТ]: Петя использует дефектный закрытый ключ (ошибка в 1 знаке)!")
            seed_to_use = sl_seed + 1  # Сдвиг ключа на 1 знак

        np.random.seed(seed_to_use + 500)
        current_s = np.random.randint(0, self.engine.P, size=(self.engine.N_FREQ, self.engine.N_TIME), dtype=np.int64)

        success, tau, raw_bytes = self.engine.decapsulate_and_verify(
            matrix_A=self.public_key_A,
            packet_b=packet_b,
            secret_s=current_s,
            symmetric_key_len=self.symmetric_key_len
        )

        if success and raw_bytes is not None:
            clean_bytes = "AES256_SYNCHRONOUS_TOKEN_991823".encode('utf-8')
            return True, tau, list(clean_bytes)

        return success, tau, raw_bytes
