# -*- coding: utf-8 -*-
"""
Запускаемый стенд проверки взаимодействия Вася-Петя с визуализацией носителей.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime

from mozart_crypto_core_optimized import MozartCryptoEngine
from mozart_nodes_optimized import VasyaServer, PetyaClient


def save_surface_matrix(matrix, title, filename, vmin=None, vmax=None):
    """Сохраняет матрицу носителя как изображение."""
    plt.figure(figsize=(14, 8))

    # Создаем тепловую карту
    if vmin is None:
        vmin = np.min(matrix)
    if vmax is None:
        vmax = np.max(matrix)

    # Используем colormap от синего (гладкий) к красному (шумный)
    cmap = LinearSegmentedColormap.from_list('smooth_noise', ['darkblue', 'cyan', 'yellow', 'red'], N=256)

    plt.imshow(matrix, aspect='auto', cmap=cmap, vmin=vmin, vmax=vmax)
    plt.colorbar(label='Значение в поле GF(257)')
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel('Время (N_TIME = 100)', fontsize=10)
    plt.ylabel('Частота (N_FREQ = 128)', fontsize=10)

    # Добавляем статистику
    tau = calculate_tau_simple(matrix)
    plt.text(0.02, 0.98, f'Тау = {tau:.4f}',
             transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Сохранено: {filename}")


def calculate_tau_simple(matrix):
    """Быстрый расчет тау для статистики."""
    diff_x = np.diff(matrix, axis=1)
    diff_y = np.diff(matrix, axis=0)
    tau = np.sum(np.abs(diff_x)) + np.sum(np.abs(diff_y))
    return tau / float(matrix.size)


def save_all_surfaces(engine, source_carrier, encrypted_packet, decrypted_correct, decrypted_wrong, sl_seed):
    """Сохраняет все четыре носителя."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("\n" + "=" * 70)
    print(" СОХРАНЕНИЕ НОСИТЕЛЕЙ ")
    print("=" * 70)

    # 1. Исходный носитель (из музыки)
    save_surface_matrix(
        source_carrier,
        f"ИСХОДНЫЙ НОСИТЕЛЬ (из музыки) - SL={sl_seed}",
        f"surface_1_source_SL{sl_seed}_{timestamp}.png"
    )

    # 2. Зашифрованный носитель
    save_surface_matrix(
        encrypted_packet,
        f"ЗАШИФРОВАННЫЙ НОСИТЕЛЬ (криптограмма) - SL={sl_seed}",
        f"surface_2_encrypted_SL{sl_seed}_{timestamp}.png"
    )

    # 3. Расшифрованный носитель (ВЕРНЫЙ ключ)
    save_surface_matrix(
        decrypted_correct,
        f"РАСШИФРОВАННЫЙ НОСИТЕЛЬ (ВЕРНЫЙ ключ, SL={sl_seed}) - ГЛАДКИЙ",
        f"surface_3_decrypted_correct_SL{sl_seed}_{timestamp}.png"
    )

    # 4. Расшифрованный носитель (НЕВЕРНЫЙ ключ - атака)
    save_surface_matrix(
        decrypted_wrong,
        f"РАСШИФРОВАННЫЙ НОСИТЕЛЬ (НЕВЕРНЫЙ ключ, SL={sl_seed}+1) - КАКОФОНИЯ",
        f"surface_4_decrypted_wrong_SL{sl_seed}_{timestamp}.png",
        vmin=0, vmax=256
    )

    # 5. Сравнительная статистика
    print("\n" + "-" * 70)
    print(" СТАТИСТИКА НОСИТЕЛЕЙ ")
    print("-" * 70)

    tau_source = calculate_tau_simple(source_carrier)
    tau_encrypted = calculate_tau_simple(encrypted_packet)
    tau_correct = calculate_tau_simple(decrypted_correct)
    tau_wrong = calculate_tau_simple(decrypted_wrong)

    print(f"\n  {'Носитель':<35} {'Тау':<12} {'Оценка'}")
    print(f"  {'-' * 35} {'-' * 12} {'-' * 20}")
    print(f"  {'1. Исходный (из музыки)':<35} {tau_source:.4f}     {'ГЛАДКИЙ' if tau_source < 45 else 'ШУМНОЙ'}")
    print(f"  {'2. Зашифрованный':<35} {tau_encrypted:.4f}     {'ГЛАДКИЙ' if tau_encrypted < 45 else 'ШУМНОЙ'}")
    print(
        f"  {'3. Расшифрованный (ВЕРНЫЙ ключ)':<35} {tau_correct:.4f}     {'ГЛАДКИЙ' if tau_correct < 45 else 'ШУМНОЙ'} ✓")
    print(
        f"  {'4. Расшифрованный (НЕВЕРНЫЙ ключ)':<35} {tau_wrong:.4f}     {'ГЛАДКИЙ' if tau_wrong < 45 else 'ШУМНОЙ'} ✗")

    print(f"\n  Порог гладкости (тау < {45}): музыка/носитель")
    print(f"  Порог какофонии (тау >= {45}): шум/атака")

    return {
        'source': tau_source,
        'encrypted': tau_encrypted,
        'correct': tau_correct,
        'wrong': tau_wrong
    }


def run_pankratov_protocol_test():
    print("=" * 70)
    print("   СТЕНД СИНХРОННОЙ ПОСТКВАНТОВОЙ СЕССИИ ERP MOZART: ВАСЯ И ПЕТЯ")
    print("   С ВИЗУАЛИЗАЦИЕЙ НОСИТЕЛЕЙ")
    print("=" * 70)

    # Инициализация
    crypto_core = MozartCryptoEngine(music_dir="/home/sergey/Documents/configurate")
    vasya_server = VasyaServer(crypto_core)
    petya_client = PetyaClient(crypto_core)

    # Генерация ключей
    expected_len = len(vasya_server.symmetric_session_key)
    petya_pub_A = petya_client.init_session_keys(target_key_len=expected_len)

    # Получаем исходный носитель ДО шифрования (для сохранения)
    file_path, SL, TR = crypto_core.select_stochastic_track()
    print(f"\n[DEBUG] Выбран файл: {file_path}")
    print(f"[DEBUG] SL = {SL}, TR = {TR}")

    # Генерируем исходный носитель
    source_carrier = crypto_core.generate_carrier_from_file(file_path, SL)
    tau_source = crypto_core.calculate_surface_tau(source_carrier)
    print(f"\n[ИСХОДНЫЙ НОСИТЕЛЬ] Тау = {tau_source:.4f}")

    # Шифрование
    encrypted_packet, SL, TR = vasya_server.receive_handshake_and_encrypt(petya_pub_A)
    tau_encrypted = crypto_core.calculate_surface_tau(encrypted_packet)
    print(f"[ЗАШИФРОВАННЫЙ] Тау = {tau_encrypted:.4f}")

    # === СЦЕНАРИЙ А: ЛЕГИТИМНЫЙ ОБМЕН ===
    print("\n" + "-" * 70)
    print(" СЦЕНАРИЙ А: ЛЕГИТИМНЫЙ ОБМЕН ДАННЫМИ (Верный SL)")
    print("-" * 70)

    # Дешифрование с ВЕРНЫМ SL
    success, tau_correct, data_bytes = petya_client.receive_and_analyze(
        encrypted_packet, SL, use_hacked_key=False
    )

    # Получаем расшифрованный носитель для визуализации (используем метод из engine)
    np.random.seed(SL + 500)
    shared_s = np.random.randint(0, crypto_core.P,
                                 size=(crypto_core.N_FREQ, crypto_core.N_TIME),
                                 dtype=np.int64)
    ax_s = petya_client.public_key_A @ shared_s
    decrypted_correct = (encrypted_packet - ax_s) % crypto_core.P

    print(f"\n[РЕЗУЛЬТАТ]: Тау = {tau_correct:.4f}")
    if success:
        recovered_key_str = bytes(data_bytes).decode('utf-8', errors='ignore')
        print(">>> УСПЕХ: Носитель ГЛАДКИЙ! Верификация пройдена.")
        print(f">>> Ключ: '{recovered_key_str}'")
    else:
        print(">>> БРАК: Какофония! Пакет сброшен.")

    # === СЦЕНАРИЙ Б: АТАКА ===
    print("\n" + "-" * 70)
    print(" СЦЕНАРИЙ Б: ПОПЫТКА ВЗЛОМА (SL+1)")
    print("-" * 70)

    # Дешифрование с НЕВЕРНЫМ SL (атака)
    success_wrong, tau_wrong, _ = petya_client.receive_and_analyze(
        encrypted_packet, SL, use_hacked_key=True
    )

    # Получаем расшифрованный носитель при атаке
    np.random.seed(SL + 1 + 500)
    shared_s_wrong = np.random.randint(0, crypto_core.P,
                                       size=(crypto_core.N_FREQ, crypto_core.N_TIME),
                                       dtype=np.int64)
    ax_s_wrong = petya_client.public_key_A @ shared_s_wrong
    decrypted_wrong = (encrypted_packet - ax_s_wrong) % crypto_core.P

    print(f"\n[РЕЗУЛЬТАТ АТАКИ]: Тау = {tau_wrong:.4f}")
    if not success_wrong:
        print(">>> УСПЕХ: Зафиксирована КАКОФОНИЯ! Атака обнаружена.")
    else:
        print(">>> КРИТИЧЕСКАЯ ОШИБКА: Атака не обнаружена!")

    # === СОХРАНЕНИЕ ВСЕХ НОСИТЕЛЕЙ ===
    stats = save_all_surfaces(crypto_core, source_carrier, encrypted_packet,
                              decrypted_correct, decrypted_wrong, SL)

    # === ИТОГИ ===
    print("\n" + "=" * 70)
    print(" ИТОГИ ТЕСТИРОВАНИЯ ".center(70, "="))
    print("=" * 70)

    print(f"\n  Легитимный обмен: {'✓ ПРОЙДЕН' if success else '✗ ПРОВАЛЕН'}")
    print(f"  Атака предотвращена: {'✓ ПРОЙДЕН' if not success_wrong else '✗ ПРОВАЛЕН'}")

    if success and not success_wrong:
        print("\n  ✅ СИСТЕМА РАБОТАЕТ КОРРЕКТНО!")
        print(f"\n  ДИАГНОСТИКА:")
        print(f"    - Исходный носитель:     тау = {stats['source']:.2f}")
        print(f"    - Зашифрованный:         тау = {stats['encrypted']:.2f}")
        print(f"    - Расшифрованный (верн): тау = {stats['correct']:.2f} (< {crypto_core.TAU_THRESHOLD})")
        print(f"    - Расшифрованный (атака): тау = {stats['wrong']:.2f} (> {crypto_core.TAU_THRESHOLD})")

    print("\n" + "=" * 70)
    print(" Сохраненные файлы:")
    print("  - surface_1_source_*.png      - исходный носитель из музыки")
    print("  - surface_2_encrypted_*.png   - зашифрованный носитель")
    print("  - surface_3_decrypted_correct_*.png - расшифрованный (верный ключ)")
    print("  - surface_4_decrypted_wrong_*.png   - расшифрованный (атака)")
    print("=" * 70)


if __name__ == "__main__":
    run_pankratov_protocol_test()