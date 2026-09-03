"""ライブラリ共通の例外。"""

from __future__ import annotations


class ReplayException(Exception):
    """fnreplay が送出するすべての例外の基底クラス。"""


class InvalidReplayException(ReplayException):
    """リプレイファイルとして不正な内容だった場合。"""


class MalformedPacketException(ReplayException):
    """ネットワークパケットが壊れている場合。"""


class UnknownEventException(ReplayException):
    """未知のイベントチャンクを読み取った場合。"""


class PlayerEliminationException(ReplayException):
    """撃破イベントの解析に失敗した場合。"""


class DecoderException(ReplayException):
    """Oodle (Kraken/Mermaid) 展開に失敗した場合。"""
