"""リプレイデータの展開 (Oodle)。

既定では純 Python 実装 (:mod:`fnreplay.compression.kraken`) を使う。
``use_native_oodle()`` を呼ぶとネイティブライブラリを優先して使用する。
"""

from __future__ import annotations

from . import kraken, oodle_native

_prefer_native = False


def use_native_oodle(path: str | None = None) -> bool:
    """ネイティブの Oodle ライブラリを優先して使うようにする。

    Args:
        path: ライブラリのパス。``None`` なら自動探索する。

    Returns:
        ライブラリを読み込めたかどうか。読み込めなければ純 Python 実装のままになる。
    """
    global _prefer_native
    _prefer_native = oodle_native.load(path)
    return _prefer_native


def decompress_replay_data(compressed: bytes, uncompressed_size: int) -> bytes:
    """リプレイのチャンクを展開する。

    Args:
        compressed: 圧縮済みデータ。
        uncompressed_size: 展開後のバイト数。
    """
    if _prefer_native and oodle_native.is_available():
        return oodle_native.decompress(compressed, uncompressed_size)
    return kraken.decompress(compressed, uncompressed_size)


__all__ = ["decompress_replay_data", "use_native_oodle", "kraken", "oodle_native"]
