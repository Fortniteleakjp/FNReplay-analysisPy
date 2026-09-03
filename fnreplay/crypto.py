"""リプレイチャンクの復号 (AES-256 ECB)。

``cryptography`` または ``pycryptodome`` が入っていればそれを使い、
無ければ純 Python 実装にフォールバックする。
"""

from __future__ import annotations

from typing import Callable

_backend: Callable[[bytes, bytes], bytes] | None = None
_backend_name = "pure-python"


def _load_backend() -> tuple[Callable[[bytes, bytes], bytes], str]:
    """利用可能な AES 実装を選ぶ。"""
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        def decrypt_cryptography(key: bytes, data: bytes) -> bytes:
            cipher = Cipher(algorithms.AES(key), modes.ECB())
            decryptor = cipher.decryptor()
            return decryptor.update(data) + decryptor.finalize()

        return decrypt_cryptography, "cryptography"
    except ImportError:
        pass

    try:
        from Crypto.Cipher import AES  # type: ignore[import-not-found]

        def decrypt_pycryptodome(key: bytes, data: bytes) -> bytes:
            return AES.new(key, AES.MODE_ECB).decrypt(data)

        return decrypt_pycryptodome, "pycryptodome"
    except ImportError:
        pass

    return _pure_python_ecb_decrypt, "pure-python"


def backend_name() -> str:
    """使用中の AES 実装名を返す。"""
    global _backend, _backend_name
    if _backend is None:
        _backend, _backend_name = _load_backend()
    return _backend_name


def aes_ecb_decrypt(key: bytes, data: bytes, remove_padding: bool = True) -> bytes:
    """AES-ECB で復号する。

    Args:
        key: 16 / 24 / 32 バイトの鍵。
        data: 復号するデータ (16 バイトの倍数)。
        remove_padding: PKCS#7 パディングを取り除くかどうか。
    """
    global _backend, _backend_name
    if _backend is None:
        _backend, _backend_name = _load_backend()

    if len(data) % 16 != 0:
        # 末尾の端数は復号できないためそのまま無視する
        data = data[: len(data) - (len(data) % 16)]

    plain = _backend(key, data)

    if remove_padding and plain:
        pad = plain[-1]
        if 1 <= pad <= 16 and plain[-pad:] == bytes([pad]) * pad:
            plain = plain[:-pad]
    return plain


# ---------------------------------------------------------------------------
# 純 Python の AES 実装 (依存ライブラリが無い場合のフォールバック)
# ---------------------------------------------------------------------------

_SBOX = [
    0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
    0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
    0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
    0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
    0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
    0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
    0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
    0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
    0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
    0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
    0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
    0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
    0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
    0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
    0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
    0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16,
]

_INV_SBOX = [0] * 256
for _i, _v in enumerate(_SBOX):
    _INV_SBOX[_v] = _i

_RCON = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36, 0x6C, 0xD8, 0xAB, 0x4D]


def _xtime(value: int) -> int:
    value <<= 1
    if value & 0x100:
        value ^= 0x11B
    return value & 0xFF


# GF(2^8) の乗算テーブル
_MUL = [[0] * 256 for _ in range(15)]
for _a in (9, 11, 13, 14):
    for _b in range(256):
        result = 0
        aa, bb = _a, _b
        while aa:
            if aa & 1:
                result ^= bb
            bb = _xtime(bb)
            aa >>= 1
        _MUL[_a][_b] = result


def _expand_key(key: bytes) -> list[list[int]]:
    """AES の鍵スケジュールを生成する。"""
    key_words = len(key) // 4
    rounds = key_words + 6
    words: list[list[int]] = [list(key[4 * i : 4 * i + 4]) for i in range(key_words)]

    for i in range(key_words, 4 * (rounds + 1)):
        temp = list(words[i - 1])
        if i % key_words == 0:
            temp = temp[1:] + temp[:1]
            temp = [_SBOX[b] for b in temp]
            temp[0] ^= _RCON[i // key_words - 1]
        elif key_words > 6 and i % key_words == 4:
            temp = [_SBOX[b] for b in temp]
        words.append([words[i - key_words][j] ^ temp[j] for j in range(4)])

    return [sum(words[4 * r : 4 * r + 4], []) for r in range(rounds + 1)]


def _decrypt_block(block: list[int], round_keys: list[list[int]]) -> list[int]:
    """1 ブロック (16 バイト) を復号する。"""
    rounds = len(round_keys) - 1
    state = [block[i] ^ round_keys[rounds][i] for i in range(16)]

    for round_index in range(rounds - 1, -1, -1):
        # InvShiftRows + InvSubBytes
        shifted = [0] * 16
        for column in range(4):
            for row in range(4):
                shifted[((column + row) % 4) * 4 + row] = _INV_SBOX[state[column * 4 + row]]
        # AddRoundKey
        key = round_keys[round_index]
        state = [shifted[i] ^ key[i] for i in range(16)]

        if round_index != 0:
            # InvMixColumns
            mixed = [0] * 16
            mul = _MUL
            for column in range(4):
                base = column * 4
                a0, a1, a2, a3 = state[base : base + 4]
                mixed[base] = mul[14][a0] ^ mul[11][a1] ^ mul[13][a2] ^ mul[9][a3]
                mixed[base + 1] = mul[9][a0] ^ mul[14][a1] ^ mul[11][a2] ^ mul[13][a3]
                mixed[base + 2] = mul[13][a0] ^ mul[9][a1] ^ mul[14][a2] ^ mul[11][a3]
                mixed[base + 3] = mul[11][a0] ^ mul[13][a1] ^ mul[9][a2] ^ mul[14][a3]
            state = mixed

    return state


def _pure_python_ecb_decrypt(key: bytes, data: bytes) -> bytes:
    """純 Python の AES-ECB 復号。"""
    round_keys = _expand_key(key)
    output = bytearray(len(data))
    for offset in range(0, len(data), 16):
        block = list(data[offset : offset + 16])
        output[offset : offset + 16] = bytes(_decrypt_block(block, round_keys))
    return bytes(output)
