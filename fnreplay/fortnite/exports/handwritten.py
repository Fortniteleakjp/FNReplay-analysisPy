"""自動生成できないネットフィールドエクスポート (独自の ``serialize`` を持つもの)。"""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING, Any

from ...unreal.archives import FArchive, NetBitReader
from ...unreal.enums import EngineNetworkVersionHistory, ParseMode, RepLayoutCmdType
from ...unreal.export_registry import ExportGroup, export_group, export_subgroup, field
from ...unreal.models import Property, Resolvable

if TYPE_CHECKING:  # pragma: no cover - 型チェック専用
    from ...unreal.net_guid_cache import NetGuidCache


class DebuggingObject(Property):
    """解析できないプロパティの中身を後から調べるための入れ物。

    ビット列をそのまま保持し、各種の解釈を試せるようにする。
    """

    __slots__ = ("data", "total_bits", "_engine_network_version")

    def __init__(self) -> None:
        self.data = b""
        self.total_bits = 0
        self._engine_network_version = EngineNetworkVersionHistory.HISTORY_INITIAL

    def serialize(self, reader: NetBitReader) -> None:
        self.total_bits = reader.get_bits_left()
        self.data = reader.read_bits(self.total_bits)
        self._engine_network_version = reader.engine_network_version

    def _reader(self) -> NetBitReader:
        reader = NetBitReader(self.data, self.total_bits)
        reader.engine_network_version = self._engine_network_version
        return reader

    @property
    def as_bool(self) -> bool | None:
        """1 ビットとして解釈する。"""
        if self.total_bits != 1:
            return None
        return self._reader().read_bit()

    @property
    def as_byte(self) -> int | None:
        """1 バイトとして解釈する。"""
        if self.total_bits > 8:
            return None
        return self._reader().read_bits_to_int(self.total_bits)

    @property
    def as_int32(self) -> int | None:
        """32 ビット符号付き整数として解釈する。"""
        if self.total_bits != 32:
            return None
        return struct.unpack("<i", self.data[:4])[0]

    @property
    def as_float(self) -> float | None:
        """32 ビット浮動小数点数として解釈する。"""
        if self.total_bits != 32:
            return None
        return struct.unpack("<f", self.data[:4])[0]

    @property
    def as_int_packed(self) -> int:
        """可変長整数として解釈する。"""
        return self._reader().read_int_packed()

    @property
    def as_string(self) -> str:
        """FString として解釈する。"""
        return self._reader().read_fstring()

    def __repr__(self) -> str:
        return f"DebuggingObject(bits={self.total_bits}, data={self.data.hex()})"

    def to_dict(self) -> dict[str, Any]:
        return {"bits": self.total_bits, "data": self.data.hex()}


class FQuantizedBuildingAttribute(Property):
    """建築物の量子化された属性 (内容は未解析)。"""

    __slots__ = ()

    def serialize(self, reader: NetBitReader) -> None:
        """C# 版と同じく何も読み取らない。"""


class FAthenaPawnReplayData(Property):
    """暗号化されたポーンのリプレイデータ (中身は読めない)。"""

    __slots__ = ("encrypted_replay_data",)

    def __init__(self) -> None:
        self.encrypted_replay_data = b""

    def serialize(self, reader: NetBitReader) -> None:
        self.encrypted_replay_data = reader.read_bits(reader.get_bits_left())


@export_group("CurrentPlaylistInfo", ParseMode.Minimal)
class PlaylistInfo(ExportGroup, Property, Resolvable):
    """プレイリスト (ゲームモード) の情報。"""

    FIELDS: list = []

    def __init__(self) -> None:
        self.id = 0
        self.name: str | None = None
        #: 新しいビルドで追加された未解析のビット列
        self.extra_bits = b""

    def serialize(self, reader: NetBitReader) -> None:
        if (
            reader.engine_network_version
            >= EngineNetworkVersionHistory.HISTORY_FAST_ARRAY_DELTA_STRUCT
        ):
            reader.read_bit()
        reader.read_bit()
        self.id = reader.read_int_packed()
        reader.skip_bits(31)
        # ビルド 41 以降は末尾にさらにフィールドが追加されている。内容が不明なため
        # 生のビット列として保持しておく (プレイリスト ID の位置は変わっていない)。
        remaining = reader.get_bits_left()
        if remaining > 0:
            self.extra_bits = reader.read_bits(remaining)

    def resolve(self, cache: "NetGuidCache") -> None:
        name = cache.try_get_path_name(self.id)
        if name is not None:
            self.name = name

    def __repr__(self) -> str:
        return f"PlaylistInfo(id={self.id}, name={self.name!r})"


@export_subgroup("/Game/Athena/PlayerPawn_Athena.PlayerPawn_Athena_C")
class PlayerPawnLatestEngine:
    """Unreal Engine 5.6 以降で追加されたプレイヤーポーンのプロパティ。

    ``RemoteViewPitch`` (uint8) は 5.6 で非推奨になり、精度を上げた
    ``RemoteViewPitch16`` (uint16) に置き換えられた
    (FEngineNetworkCustomVersion::PawnRemoteViewPitchTo16Bit)。
    """

    FIELDS = [
        field("RemoteViewPitch16", "remote_view_pitch16", RepLayoutCmdType.PropertyUInt16),
    ]


class PlayerNameData:
    """外部データとして送られてくるプレイヤー名。"""

    __slots__ = ("handle", "unknown1", "is_player", "encoded_name", "decoded_name")

    def __init__(self, archive: FArchive) -> None:
        self.handle = archive.read_byte()
        self.unknown1 = archive.read_byte()
        self.is_player = archive.read_boolean()
        self.encoded_name = archive.read_fstring()

        if self.is_player:
            decoded = []
            length = len(self.encoded_name)
            for i, char in enumerate(self.encoded_name):
                shift = (length % 4 * 3 % 8 + 1 + i) * 3 % 8
                decoded.append(chr(ord(char) + shift))
            self.decoded_name = "".join(decoded)
        else:
            self.decoded_name = self.encoded_name

    def __repr__(self) -> str:
        return f"PlayerNameData(handle={self.handle}, name={self.decoded_name!r})"
