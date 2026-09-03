"""fnreplay - Fortnite / Unreal Engine のリプレイを解析する Python ライブラリ。

Shiqan/FortniteReplayDecompressor (C#) を Python へ移植したもの。

使い方::

    import fnreplay

    replay = fnreplay.read_replay("match.replay")
    print(replay.info.friendly_name)
    for elimination in replay.eliminations:
        print(elimination.time, elimination.eliminator, "->", elimination.eliminated)
"""

from .compression import use_native_oodle
from .fortnite import FortniteReplay, FortniteReplayReader, read_replay
from .unreal import ParseMode, ReplayReader
from .unreal.exceptions import (
    DecoderException,
    InvalidReplayException,
    MalformedPacketException,
    PlayerEliminationException,
    ReplayException,
    UnknownEventException,
)

__version__ = "0.1.0"

__all__ = [
    "read_replay",
    "FortniteReplayReader",
    "FortniteReplay",
    "ReplayReader",
    "ParseMode",
    "use_native_oodle",
    "ReplayException",
    "InvalidReplayException",
    "MalformedPacketException",
    "UnknownEventException",
    "PlayerEliminationException",
    "DecoderException",
    "__version__",
]
