# -*- coding: utf-8 -*-
# Путь: /home/sergey/Documents/configurate/layer2_server/main_verification.py
# Описание: Запускаемый стенд проверки взаимодействия Вася-Петя с цензором гладкости.

import sys
from mozart_crypto_core import MozartCryptoEngine
from mozart_nodes import VasyaServer, PetyaClient


def run_pankratov_protocol_test():
    print("======================================================================")
    print("   СТЕНД СИНХРОННОЙ ПОСТКВАНТОВОЙ СЕССИИ ERP MOZART: ВАСЯ И ПЕТЯ")
    print("======================================================================")

    # Инициализируем общее математическое ядро системы
    crypto_core = MozartCryptoEngine()

    # Создаем экземпляры класса Вася и Петя
    vasya_server = VasyaServer(crypto_core)
    petya_client = PetyaClient(crypto_core)

    # --- ЭТАП 1: Петя инициирует сессию и шлет открытый ключ Васе ---
    expected_len = len(vasya_server.symmetric_session_key)
    petya_pub_A = petya_client.init_session_keys(target_key_len=expected_len)

    # --- ЭТАП 2: Вася принимает ключ Пети и шифрует симметричный токен ---
    encrypted_packet, SL, TR = vasya_server.receive_handshake_and_encrypt(petya_pub_A)

    print("\n----------------------------------------------------------------------")
    print(" СЦЕНАРИЙ А: ЛЕГИТИМНЫЙ ОБМЕН ДАННЫМИ (Ключевая пара верна)")
    print("----------------------------------------------------------------------")
    # Петя анализирует прилетевшую корневую функцию истинным ключом ловушки
    success, tau, data_bytes = petya_client.receive_and_analyze(encrypted_packet, SL, use_hacked_key=False)

    print(f"\n[РЕЗУЛЬТАТ ЦЕНЗОРА ПЕТИ]: Индекс изрезанности тау = {tau:.4f}")
    if success:
        recovered_key_str = bytes(data_bytes).decode('utf-8', errors='ignore')
        print(">>> УСПЕХ: Носитель ГЛАДКИЙ (Музыка узнана)! Верификация пройдена.")
        print(f">>> Симметричный ключ сессии успешно принят Петей: '{recovered_key_str}'")
    else:
        print(">>> БРАК: Слышна какофония шума. Пакет сброшен.")

    print("\n----------------------------------------------------------------------")
    print(" СЦЕНАРИЙ Б: ПОПЫТКА ВЗЛОМА / ДЕФЕКТНЫЙ ЗАКРЫТЫЙ КЛЮЧ (Ошибка в 1 знаке)")
    print("----------------------------------------------------------------------")
    # Петя пытается дешифровать тот же пакет, но в ключе ловушки допущена ошибка в единицу
    success, tau, data_bytes = petya_client.receive_and_analyze(encrypted_packet, SL, use_hacked_key=True)

    print(f"\n[РЕЗУЛЬТАТ ЦЕНЗОРА ПЕТИ]: Индекс изрезанности тау = {tau:.4f}")
    if not success:
        print(">>> УСПЕХ АВТОМАТА: Зафиксирована НЕГЛАДКАЯ КАКОФОНИЯ (Поверхность уничтожена)!")
        print(">>> ДЕЙСТВИЕ: Приложение ПЕТЯ разорвало сессию. Команда на ПОВТОРЯЕМСЯ отправлена.")
        print(">>> Злоумышленник остался с дыркой от бублика.")
    else:
        print(">>> Критическая ошибка: дыра в безопасности, софт пропустил мусор.")


if __name__ == "__main__":
    run_pankratov_protocol_test()
