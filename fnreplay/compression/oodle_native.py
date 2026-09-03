"""ネイティブの Oodle ライブラリ (oo2core) を使った展開。

純 Python 実装より高速だが、``oo2core_*.dll`` / ``liboo2core*.so`` を
利用者自身が用意する必要がある (Fortnite のインストールディレクトリなどに含まれる)。
再配布は Oodle のライセンス上できないため、パスを指定して読み込む方式にしている。
"""

from __future__ import annotations

import ctypes
import glob
import os
import platform
from typing import Any

from ..unreal.exceptions import DecoderException

_library: Any = None
_decompress_fn: Any = None

#: 環境変数でライブラリのパスを指定できる
ENV_VAR = "FNREPLAY_OODLE_LIBRARY"


def _candidate_paths() -> list[str]:
    """よくある配置場所からライブラリを探す。"""
    from_env = os.environ.get(ENV_VAR)
    candidates: list[str] = [from_env] if from_env else []

    if platform.system() == "Windows":
        patterns = [
            r"C:\Program Files\Epic Games\Fortnite\FortniteGame\Binaries\Win64\oo2core_*_win64.dll",
            r"C:\Program Files\Epic Games\Fortnite\Engine\Binaries\ThirdParty\Oodle\**\oo2core_*.dll",
            "oo2core_*_win64.dll",
        ]
    else:
        patterns = ["liboo2corelinux64.so.*", "liboo2core*.so", "liboo2core*.dylib"]

    for pattern in patterns:
        candidates.extend(sorted(glob.glob(pattern, recursive=True)))

    return [path for path in candidates if path and os.path.exists(path)]


def load(path: str | None = None) -> bool:
    """ネイティブライブラリを読み込む。

    Args:
        path: 明示的に指定するライブラリのパス。``None`` なら自動探索する。

    Returns:
        読み込みに成功したかどうか。
    """
    global _library, _decompress_fn

    paths = [path] if path else _candidate_paths()
    for candidate in paths:
        try:
            library = ctypes.CDLL(candidate)
            fn = library.OodleLZ_Decompress
        except (OSError, AttributeError):
            continue

        fn.restype = ctypes.c_ssize_t
        fn.argtypes = [
            ctypes.c_char_p,  # src
            ctypes.c_ssize_t,  # src_len
            ctypes.c_char_p,  # dst
            ctypes.c_ssize_t,  # dst_len
            ctypes.c_int,  # fuzz safe
            ctypes.c_int,  # check crc
            ctypes.c_int,  # verbosity
            ctypes.c_void_p,  # dst base
            ctypes.c_ssize_t,  # dst base size
            ctypes.c_void_p,  # callback
            ctypes.c_void_p,  # callback context
            ctypes.c_void_p,  # scratch
            ctypes.c_ssize_t,  # scratch size
            ctypes.c_int,  # thread phase
        ]
        _library = library
        _decompress_fn = fn
        return True

    return False


def is_available() -> bool:
    """ネイティブライブラリが利用可能かどうか。"""
    return _decompress_fn is not None


def decompress(compressed: bytes, uncompressed_size: int) -> bytes:
    """ネイティブライブラリで展開する。"""
    if _decompress_fn is None:
        raise DecoderException("ネイティブの Oodle ライブラリが読み込まれていません")

    output = ctypes.create_string_buffer(uncompressed_size)
    result = _decompress_fn(
        compressed,
        len(compressed),
        output,
        uncompressed_size,
        1,
        0,
        0,
        None,
        0,
        None,
        None,
        None,
        0,
        3,
    )
    if result != uncompressed_size:
        raise DecoderException(f"Oodle の展開に失敗しました (戻り値={result})")
    return output.raw[:uncompressed_size]
