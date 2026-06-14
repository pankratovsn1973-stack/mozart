import numpy as np
import matplotlib.pyplot as plt

# Параметры
levels = 7
# Амплитуды: A_k = A0 * (0.3)^k
A0 = 1.0
decay = 0.32
# Частоты: f_k = f0 * 8^k
f0 = 1.0

# Генерируем массивы амплитуд и частот
A = [A0 * (decay ** k) for k in range(levels)]
f = [f0 * (8 ** k) for k in range(levels)]

# Параметрическая кривая: x(t) = t, y(t) = Σ A_k * sin(2π f_k t + φ_k)  (но это не даст обвивания)
# Для обвивания нужно на каждом уровне смещать по нормали, но при 7 уровнях это крайне тяжело вычислить.
# Поэтому я предлагаю упрощённую модель: кривая задаётся как (X(t), Y(t)) = (t, F(t)), где F(t) = Σ A_k sin(2π f_k t)
# Это даст сильную осцилляцию, но без самопересечений. Для самопересечений нужно параметрическое обвивание.

# Для демонстрации сложности построим график функции y = Σ A_k sin(2π f_k t) (уровни накладываются аддитивно).
# Это не совсем то, что мы рисовали раньше, но зато вычислимо для 7 уровней.

t = np.linspace(0, 2*np.pi, 50000)
y = np.zeros_like(t)
for k in range(levels):
    y += A[k] * np.sin(f[k] * t)

plt.figure(figsize=(14, 6))
plt.plot(t, y, 'r-', lw=0.3)
plt.title(f'Сумма синусоид: 7 уровней, частота растёт в 8 раз, амплитуда умножается на {decay}')
plt.xlabel('t')
plt.ylabel('y')
plt.grid(True, alpha=0.2)
plt.show()

# Теперь увеличенный фрагмент, чтобы увидеть мелкие колебания
t_fragment = np.linspace(0, 0.05, 20000)
y_fragment = np.zeros_like(t_fragment)
for k in range(levels):
    y_fragment += A[k] * np.sin(f[k] * t_fragment)

plt.figure(figsize=(14, 6))
plt.plot(t_fragment, y_fragment, 'b-', lw=0.5)
plt.title('Фрагмент [0, 0.05] — видны высокочастотные осцилляции')
plt.xlabel('t')
plt.ylabel('y')
plt.grid(True, alpha=0.2)
plt.show()