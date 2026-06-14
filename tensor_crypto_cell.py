import numpy as np
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class TensorLWE:
    def __init__(self, n=8, q=1021, use_rip=True):
        self.n = n
        self.q = q
        self.use_rip = use_rip

        # Секретный тензор S (разреженный, чтобы шум был мал)
        self.S = np.random.choice([-1, 0, 1], size=(n, n, n), p=[0.1, 0.8, 0.1])

        # Разрыв ткани (опционально)
        if use_rip:
            self.axis_rip = tuple(np.random.permutation(3))
            self.slice_rip = np.random.permutation(n)
            self.S_fixed = self._rip(self.S)
        else:
            self.S_fixed = self.S

        # Публичный ключ: A случайный, B = A * S_fixed + E (малый шум)
        self.A = np.random.randint(0, q, size=(n, n, n), dtype=np.int64)
        self.E = np.random.randint(-1, 2, size=(n, n, n), dtype=np.int64)
        self.B = (np.einsum('iab,abk->ibk', self.A, self.S_fixed) + self.E) % q

    def _rip(self, T):
        T = np.transpose(T, self.axis_rip)
        return np.take(T, self.slice_rip, axis=0)

    def _contract(self, R, T):
        return np.einsum('iab,abk->ibk', R, T) % self.q

    def encrypt_bit(self, bit, A, B):
        R = np.random.choice([-1, 0, 1], size=(self.n, self.n, self.n), p=[0.1, 0.8, 0.1])
        m = bit * (self.q // 2)
        m_tensor = np.full((self.n, self.n, self.n), m, dtype=np.int64)
        U = self._contract(R, A)
        V = (self._contract(R, B) + m_tensor) % self.q
        return U, V

    def decrypt_bit(self, U, V):
        diff = (V - self._contract(U, self.S_fixed)) % self.q
        diff = np.minimum(diff, self.q - diff)
        return 1 if np.mean(diff) > self.q // 4 else 0

    # --- Методы для байтов ---
    def encrypt_bytes(self, data: bytes, A, B) -> list:
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)
        cipher = []
        for b in bits:
            U, V = self.encrypt_bit(b, A, B)
            cipher.append((U, V))
        return cipher

    def decrypt_bytes(self, cipher: list) -> bytes:
        bits = [self.decrypt_bit(U, V) for (U, V) in cipher]
        byte_list = []
        for i in range(0, len(bits), 8):
            if i + 8 <= len(bits):
                byte = 0
                for j in range(8):
                    byte = (byte << 1) | bits[i + j]
                byte_list.append(byte)
        return bytes(byte_list)


def generate_keypair(n=4, q=1021, use_rip=True):
    bob = TensorLWE(n, q, use_rip)
    return bob, (bob.A, bob.B)


def encrypt_session_key(public_key, symmetric_key: bytes) -> list:
    A, B = public_key
    tmp = TensorLWE(n=A.shape[0], q=1021, use_rip=True)
    return tmp.encrypt_bytes(symmetric_key, A, B)


def decrypt_session_key(private_bob, ciphertext: list) -> bytes:
    return private_bob.decrypt_bytes(ciphertext)


if __name__ == "__main__":
    # 1. Генерация ключей Боба
    bob, bob_pub = generate_keypair(n=4, q=1021, use_rip=True)

    # 2. Сессионный ключ (32 байта для AES-256)
    session_key = os.urandom(32)
    print(f"Сессионный ключ (hex): {session_key.hex()}")

    # 3. Алиса шифрует ключ публичным ключом Боба
    enc_key = encrypt_session_key(bob_pub, session_key)

    # 4. Боб расшифровывает
    dec_key = decrypt_session_key(bob, enc_key)
    assert session_key == dec_key, "Ошибка: ключи не совпадают"
    print("✅ Сессионный ключ успешно передан через TensorLWE")

    # 5. Текст для шифрования (Евгений Онегин)
    onegin = (
        "Мой дядя самых честных правил,\n"
        "Когда не в шутку занемог,\n"
        "Он уважать себя заставил\n"
        "И лучше выдумать не мог.\n"
        "Его пример другим наука;\n"
        "Но, боже мой, какая скука\n"
        "С больным сидеть и день и ночь,\n"
        "Не отходя ни шагу прочь!\n"
        "Какое низкое коварство\n"
        "Полуживого забавлять,\n"
        "Ему подушки поправлять,\n"
        "Печально подносить лекарство,\n"
        "Вздыхать и думать про себя:\n"
        "Когда же чёрт возьмёт тебя!"
    )

    # 6. AES-GCM шифрование
    aes = AESGCM(session_key)
    nonce = os.urandom(12)
    ciphertext = aes.encrypt(nonce, onegin.encode('utf-8'), None)

    # 7. Расшифровка
    decrypted_text = aes.decrypt(nonce, ciphertext, None).decode('utf-8')

    print("\n--- Расшифрованный текст ---")
    print(decrypted_text)

    if decrypted_text == onegin:
        print("\n✅ Гибридная криптосистема работает идеально!")
    else:
        print("\n❌ Ошибка при расшифровке текста")