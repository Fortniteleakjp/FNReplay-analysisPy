"""Fortnite のネットフィールドエクスポート定義。

``generated`` はジェネレーターによる自動生成、``handwritten`` は独自の
シリアライズ処理を持つクラスを収めている。読み込むだけでレジストリに登録される。
"""

from . import generated, handwritten
from .generated import *  # noqa: F401,F403
from .handwritten import (  # noqa: F401
    DebuggingObject,
    FAthenaPawnReplayData,
    FQuantizedBuildingAttribute,
    PlayerNameData,
    PlaylistInfo,
)

__all__ = ["generated", "handwritten"]
