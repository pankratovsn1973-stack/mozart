# tensor_crypto.py

import random
import numpy as np
from hashlib import sha256

# ------------------------------------------------------------
# Арифметика в конечном поле GF(p)
# ------------------------------------------------------------
class GFp:
    """Элемент поля Fp (простое p)."""
    def __init__(self, value, p):
        self.p = p
        self.value = value % p

    def __add__(self, other):
        return GFp((self.value + other.value) % self.p, self.p)
    def __sub__(self, other):
        return GFp((self.value - other.value) % self.p, self.p)
    def __mul__(self, other):
        return GFp((self.value * other.value) % self.p, self.p)
    def __truediv__(self, other):
        inv = pow(other.value, self.p-2, self.p)
        return GFp((self.value * inv) % self.p, self.p)
    def __neg__(self):
        return GFp((-self.value) % self.p, self.p)
    def __eq__(self, other):
        return self.value == other.value and self.p == other.p
    def __int__(self):
        return self.value
    def __repr__(self):
        return str(self.value)

def random_element(p):
    return GFp(random.randrange(p), p)

# ------------------------------------------------------------
# Матрицы n x n над GF(p)
# ------------------------------------------------------------
class Matrix:
    def __init__(self, n, p, data=None):
        self.n = n
        self.p = p
        if data is not None:
            self.data = data
        else:
            self.data = [[GFp(0, p) for _ in range(n)] for _ in range(n)]

    def __getitem__(self, idx):
        return self.data[idx]

    def __setitem__(self, idx, val):
        self.data[idx] = val

    @staticmethod
    def identity(n, p):
        m = Matrix(n, p)
        for i in range(n):
            m[i][i] = GFp(1, p)
        return m

    @staticmethod
    def random_invertible(n, p):
        """Генерация случайной обратимой матрицы через LU-подобный метод."""
        # Создаём верхнетреугольную с единицами на диагонали и случайными наддиагональными
        # и нижнетреугольную со случайными поддиагональными и диагональю 1.
        # Перемножаем, получаем обратимую.
        L = Matrix.identity(n, p)
        U = Matrix.identity(n, p)
        for i in range(n):
            for j in range(i+1, n):
                L[j][i] = random_element(p)
                U[i][j] = random_element(p)
        # Перемножаем L * U
        M = Matrix(n, p)
        for i in range(n):
            for j in range(n):
                s = GFp(0, p)
                for k in range(n):
                    s = s + L[i][k] * U[k][j]
                M[i][j] = s
        return M

    def inverse(self):
        """Обратная матрица методом Гаусса-Жордана."""
        n = self.n
        # Расширенная матрица [A | I]
        a = [[self[i][j] for j in range(n)] for i in range(n)]
        inv = [[GFp(1, p) if i==j else GFp(0, p) for j in range(n)] for i in range(n)]

        for col in range(n):
            # поиск ненулевого элемента в столбце col
            pivot_row = col
            while pivot_row < n and a[pivot_row][col] == GFp(0, self.p):
                pivot_row += 1
            if pivot_row == n:
                raise ValueError("Matrix is singular")
            if pivot_row != col:
                a[col], a[pivot_row] = a[pivot_row], a[col]
                inv[col], inv[pivot_row] = inv[pivot_row], inv[col]

            pivot = a[col][col]
            inv_pivot = GFp(1, self.p) / pivot
            for j in range(n):
                a[col][j] = a[col][j] * inv_pivot
                inv[col][j] = inv[col][j] * inv_pivot

            for r in range(n):
                if r != col:
                    factor = a[r][col]
                    if factor != GFp(0, self.p):
                        for j in range(n):
                            a[r][j] = a[r][j] - factor * a[col][j]
                            inv[r][j] = inv[r][j] - factor * inv[col][j]

        result = Matrix(n, self.p)
        for i in range(n):
            for j in range(n):
                result[i][j] = inv[i][j]
        return result

    def __mul__(self, other):
        """Умножение матриц."""
        n = self.n
        result = Matrix(n, self.p)
        for i in range(n):
            for k in range(n):
                aik = self[i][k]
                if aik != GFp(0, self.p):
                    for j in range(n):
                        result[i][j] = result[i][j] + aik * other[k][j]
        return result

    def to_bytes(self):
        """Сериализация матрицы в байты (для хэширования)."""
        data = b''
        for i in range(self.n):
            for j in range(self.n):
                data += int(self[i][j]).to_bytes(2, 'big')  # т.к. p < 2^16
        return data

# ------------------------------------------------------------
# 3-тензоры n x n x n над GF(p)
# ------------------------------------------------------------
class Tensor3:
    def __init__(self, n, p, data=None):
        self.n = n
        self.p = p
        if data is not None:
            self.data = data
        else:
            self.data = np.empty((n, n, n), dtype=object)
            for i in range(n):
                for j in range(n):
                    for k in range(n):
                        self.data[i,j,k] = GFp(0, p)

    @staticmethod
    def fixed_tensor(n, p):
        """
        Эталонный тензор T0 с ненулевыми элементами только при i=j и k=1.
        T0[i,i,1] = 1 для всех i.
        Индексы: 0..n-1.
        """
        T = Tensor3(n, p)
        for i in range(n):
            T.data[i,i,1] = GFp(1, p)
        return T

    def apply_isometry(self, A, B, C):
        """Применяет (A, B, C) к тензору: возвращает новый тензор."""
        n = self.n
        p = self.p

        # Преобразование по первому измерению
        T1 = np.empty((n, n, n), dtype=object)
        for i in range(n):
            for i1 in range(n):
                coeff = A[i][i1]
                if coeff != GFp(0, p):
                    for j in range(n):
                        for k in range(n):
                            if i == 0 and j == 0 and k == 0:
                                T1[i,j,k] = coeff * self.data[i1,j,k]
                            else:
                                T1[i,j,k] = T1[i,j,k] + coeff * self.data[i1,j,k]

        # по второму измерению
        T2 = np.empty((n, n, n), dtype=object)
        for j in range(n):
            for j1 in range(n):
                coeff = B[j][j1]
                if coeff != GFp(0, p):
                    for i in range(n):
                        for k in range(n):
                            if i == 0 and j == 0 and k == 0:
                                T2[i,j,k] = coeff * T1[i,j1,k]
                            else:
                                T2[i,j,k] = T2[i,j,k] + coeff * T1[i,j1,k]

        # по третьему измерению
        T3 = np.empty((n, n, n), dtype=object)
        for k in range(n):
            for k1 in range(n):
                coeff = C[k][k1]
                if coeff != GFp(0, p):
                    for i in range(n):
                        for j in range(n):
                            if i == 0 and j == 0 and k == 0:
                                T3[i,j,k] = coeff * T2[i,j,k1]
                            else:
                                T3[i,j,k] = T3[i,j,k] + coeff * T2[i,j,k1]

        result = Tensor3(n, p)
        result.data = T3
        return result

    def __repr__(self):
        return f"Tensor3({self.n}, {self.p})"

    def to_bytes(self):
        """Сериализация тензора в байты."""
        data = b''
        for i in range(self.n):
            for j in range(self.n):
                for k in range(self.n):
                    data += int(self.data[i,j,k]).to_bytes(2, 'big')
        return data

# ------------------------------------------------------------
# Параметры системы (должны быть одинаковы у всех участников)
# ------------------------------------------------------------
P = 65521        # простое число (2^16 - 15)
N = 16           # размерность тензора (можно увеличить до 32 для безопасности)
T0 = Tensor3.fixed_tensor(N, P)

# ------------------------------------------------------------
# Основные функции криптосистемы
# ------------------------------------------------------------
def generate_keypair():
    """Генерирует пару (публичный тензор, секретные матрицы)."""
    B = Matrix.random_invertible(N, P)
    C = Matrix.random_invertible(N, P)
    I = Matrix.identity(N, P)
    T_pub = T0.apply_isometry(I, B, C)
    return T_pub, (B, C)

def message_to_matrix(message: bytes, n: int, p: int) -> Matrix:
    """
    Преобразует байтовое сообщение в матрицу n x n над GF(p).
    Сообщение дополняется хэшем для обеспечения целостности и произвольной длины.
    """
    # Вычисляем хэш сообщения (32 байта) и добавляем в начало
    h = sha256(message).digest()
    data = h + message
    # Дополняем нулями до n*n*2 байт (т.к. каждый элемент матрицы кодируется 2 байтами)
    total_cells = n * n
    needed = total_cells * 2
    if len(data) < needed:
        data += b'\x00' * (needed - len(data))
    else:
        data = data[:needed]
    # Разбиваем на пары байт и превращаем в числа
    M = Matrix(n, p)
    idx = 0
    for i in range(n):
        for j in range(n):
            val = data[idx] * 256 + data[idx+1]
            M[i][j] = GFp(val, p)
            idx += 2
    return M

def matrix_to_message(M: Matrix) -> bytes:
    """
    Извлекает сообщение из матрицы.
    Ожидается, что первые 32 байта – хэш, затем само сообщение, затем дополнение.
    """
    n = M.n
    # Собираем байты
    data = b''
    for i in range(n):
        for j in range(n):
            v = int(M[i][j])
            data += v.to_bytes(2, 'big')
    # Извлекаем хэш (первые 32 байта) и остальное
    h_received = data[:32]
    rest = data[32:]
    # Ищем нулевое дополнение в конце
    rest = rest.rstrip(b'\x00')
    # Проверяем хэш
    h_calc = sha256(rest).digest()
    if h_received != h_calc:
        raise ValueError("Контрольная сумма не совпадает – сообщение повреждено")
    return rest

def encrypt(public_tensor: Tensor3, message: bytes) -> Tensor3:
    """Шифрует сообщение с использованием публичного тензора."""
    X = message_to_matrix(message, public_tensor.n, public_tensor.p)
    I = Matrix.identity(public_tensor.n, public_tensor.p)
    # Вычисляем Y = (X, I, I) · T_pub
    Y = public_tensor.apply_isometry(X, I, I)
    return Y

def decrypt(secret_matrices, cipher_tensor: Tensor3) -> bytes:
    """Дешифрует тензор, используя секретные матрицы (B, C)."""
    B, C = secret_matrices
    n = cipher_tensor.n
    p = cipher_tensor.p
    I = Matrix.identity(n, p)
    Binv = B.inverse()
    Cinv = C.inverse()
    # Z = (I, Binv, Cinv) · Y
    Z = cipher_tensor.apply_isometry(I, Binv, Cinv)
    # Извлекаем матрицу X из слоя k=1 (индекс 1)
    X = Matrix(n, p)
    for i in range(n):
        for j in range(n):
            X[i][j] = Z.data[i,j,1]
    return matrix_to_message(X)