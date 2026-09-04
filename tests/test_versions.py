"""新しいエンジンバージョン (37〜44) 対応のテスト。

Unreal Engine の ``FEngineNetworkCustomVersion`` と、
Shiqan/FortniteReplayDecompressor#77 で判明したビルド差分に基づく。
"""

from __future__ import annotations

import struct

import pytest

from fnreplay.fortnite.exports.handwritten import PlaylistInfo
from fnreplay.unreal.archives import NetBitReader
from fnreplay.unreal.enums import EngineNetworkVersionHistory
from fnreplay.unreal.models import (
    FGameplayAbilityRepAnimMontage,
    FPredictionKey,
    NetworkReplayVersion,
)
from fnreplay.unreal.net_field_parser import uses_wide_rep_movement_rotation


class BitWriter:
    """テスト用に Unreal と同じ並び (LSB から) でビット列を作る。"""

    def __init__(self) -> None:
        self._bits: list[int] = []

    def bit(self, value: bool | int) -> "BitWriter":
        self._bits.append(1 if value else 0)
        return self

    def bits(self, value: int, count: int) -> "BitWriter":
        for index in range(count):
            self._bits.append((value >> index) & 1)
        return self

    def raw(self, data: bytes) -> "BitWriter":
        for byte in data:
            self.bits(byte, 8)
        return self

    def byte(self, value: int) -> "BitWriter":
        return self.bits(value, 8)

    def single(self, value: float) -> "BitWriter":
        return self.raw(struct.pack("<f", value))

    def int_packed(self, value: int) -> "BitWriter":
        while True:
            chunk = (value & 0x7F) << 1
            value >>= 7
            if value:
                chunk |= 1
            self.byte(chunk)
            if not value:
                return self

    def build(self) -> tuple[bytes, int]:
        """``(バイト列, ビット数)`` を返す。"""
        length = (len(self._bits) + 7) // 8
        data = bytearray(length)
        for index, bit in enumerate(self._bits):
            if bit:
                data[index >> 3] |= 1 << (index & 7)
        return bytes(data), len(self._bits)


def _reader(writer: BitWriter, engine_version: int) -> NetBitReader:
    data, bit_count = writer.build()
    reader = NetBitReader(data, bit_count)
    reader.engine_network_version = engine_version
    return reader


# ---------------------------------------------------------------------------
# エンジンバージョン
# ---------------------------------------------------------------------------


def test_engine_network_version_latest() -> None:
    """UE 6.0 系の最新バージョンまで定義されている。"""
    assert EngineNetworkVersionHistory.LATEST == 45
    assert EngineNetworkVersionHistory.MontagePlayCountSerialization == 37
    assert EngineNetworkVersionHistory.PawnRemoteViewPitchTo16Bit == 42
    assert EngineNetworkVersionHistory.ExplicitAckHistorySeq == 44
    assert EngineNetworkVersionHistory.CongestionExperiencedBit == 45


# ---------------------------------------------------------------------------
# RepMovement の回転量子化 (ビルド判定)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "branch,changelist,expected",
    [
        ("++Fortnite+Release-41.30", 56274335, True),
        ("++Fortnite+Release-41.00", 54618515, True),
        ("++Fortnite+Release-40.41", 54326946, False),
        ("++Fortnite+Release-32.00", 0, False),
        ("++Fortnite+Release-11.31", 0, False),
        # ブランチ名が無い場合は変更リスト番号で判定する
        ("", 54618515, True),
        ("", 54326946, False),
        # 他ゲームのブランチは対象外
        ("++PUBG+Release-41.11", 0, True),
        ("++PUBG+Release-11.11", 0, False),
    ],
)
def test_uses_wide_rep_movement_rotation(
    branch: str, changelist: int, expected: bool
) -> None:
    version = NetworkReplayVersion(branch=branch, changelist=changelist)
    assert uses_wide_rep_movement_rotation(version) is expected


def test_uses_wide_rep_movement_rotation_without_version() -> None:
    assert uses_wide_rep_movement_rotation(None) is False


def test_rep_movement_uses_short_rotation_on_build41() -> None:
    """ビルド 41 のリプレイでは既定の回転量子化が 16 ビットになる。"""
    from fnreplay.unreal.enums import ParseMode, RepLayoutCmdType
    from fnreplay.unreal.export_registry import FieldDef
    from fnreplay.unreal.net_field_parser import NetFieldParser
    from fnreplay.unreal.net_guid_cache import NetGuidCache

    # フラグ 4 ビット + 位置 (量子化ヘッダのみ) + 回転 3 ビット + 速度 + 加速度フラグ
    writer = BitWriter()
    writer.bits(0, 4)  # bSimulatedPhysicSleep / bRepPhysics / ServerFrame / ServerHandle
    writer.bits(0, 7)  # 位置: componentBitCount = 0, extraInfo = 0
    writer.single(1.0).single(2.0).single(3.0)
    # 回転は「有無ビット + 値」の順に並ぶ。ここでは yaw だけを送る
    writer.bit(0)  # pitch なし
    writer.bit(1).bits(0x8000, 16)  # yaw (16 ビット = ShortComponents)
    writer.bit(0)  # roll なし
    writer.bits(0, 7)  # 速度
    writer.single(0.0).single(0.0).single(0.0)
    writer.bit(0)  # bRepAcceleration

    parser = NetFieldParser(NetGuidCache(), ParseMode.Full)
    definition = FieldDef(
        name="ReplicatedMovement", attr="movement", type=RepLayoutCmdType.RepMovement
    )

    reader = _reader(writer, EngineNetworkVersionHistory.ExplicitAckHistorySeq)
    reader.network_replay_version = NetworkReplayVersion(branch="++Fortnite+Release-41.30")

    movement = parser._read_rep_movement(definition, reader)

    assert not reader.is_error
    assert reader.at_end()
    assert movement.rotation.yaw == pytest.approx(180.0)


# ---------------------------------------------------------------------------
# FPredictionKey (バージョン 34 で BaseKey が複製されなくなった)
# ---------------------------------------------------------------------------


def test_prediction_key_without_base_key() -> None:
    """バージョン 34 以降は BaseKey のビットを読まない。"""
    writer = BitWriter()
    writer.bit(1)  # ValidKeyForConnection
    writer.bit(0)  # bIsServerInitiated
    writer.bits(0x1234, 16)  # Current

    reader = _reader(writer, EngineNetworkVersionHistory.PredictionKeyBaseNotReplicated)
    key = FPredictionKey()
    key.serialize(reader)

    assert key.current_key == 0x1234
    assert key.base_key == 0
    assert not reader.is_error
    assert reader.at_end()


def test_prediction_key_with_base_key() -> None:
    """バージョン 33 以前は BaseKey も複製される。"""
    writer = BitWriter()
    writer.bit(1)  # ValidKeyForConnection
    writer.bit(1)  # HasBaseKey
    writer.bit(0)  # bIsServerInitiated
    writer.bits(0x1234, 16)  # Current
    writer.bits(0x0056, 16)  # Base

    reader = _reader(writer, EngineNetworkVersionHistory.DynamicMontageSerialization)
    key = FPredictionKey()
    key.serialize(reader)

    assert key.current_key == 0x1234
    assert key.base_key == 0x56
    assert not reader.is_error
    assert reader.at_end()


# ---------------------------------------------------------------------------
# FGameplayAbilityRepAnimMontage
# ---------------------------------------------------------------------------


def _montage_payload(engine_version: int, is_montage: bool = True) -> BitWriter:
    writer = BitWriter()
    if engine_version >= EngineNetworkVersionHistory.DynamicMontageSerialization:
        writer.bit(is_montage)
    writer.bit(1)  # RepPosition
    writer.single(12.5)  # Position (float)
    writer.bit(0)  # IsStopped
    if engine_version < EngineNetworkVersionHistory.HISTORY_MONTAGE_PLAY_INST_ID_SERIALIZATION:
        writer.bit(1)  # ForcePlayBit
    writer.bit(0)  # SkipPositionCorrection
    writer.bit(0)  # bSkipPlayRate
    writer.int_packed(42)  # Animation (NetGUID)
    writer.single(1.5)  # PlayRate
    writer.single(0.25)  # BlendTime
    writer.byte(3)  # NextSectionID
    if engine_version >= EngineNetworkVersionHistory.HISTORY_MONTAGE_PLAY_INST_ID_SERIALIZATION:
        writer.byte(7)  # PlayInstanceId (uint8)
    # FPredictionKey: 無効なキー
    writer.bit(0)  # ValidKeyForConnection
    if engine_version < EngineNetworkVersionHistory.PredictionKeyBaseNotReplicated:
        pass  # BaseKey のビットは ValidKey が真のときだけ
    writer.bit(0)  # bIsServerInitiated
    if not is_montage:
        writer.single(0.75)  # BlendOutTime
        # SlotName: ハードコード名フラグ + 空文字列 + 番号
        writer.bit(0).bits(0, 32).bits(0, 32)
    if engine_version >= EngineNetworkVersionHistory.MontagePlayCountSerialization:
        writer.single(2.0)  # PlayCount
    return writer


def test_montage_latest_version() -> None:
    """バージョン 44 のモンタージュを最後まで読み切れる。"""
    reader = _reader(
        _montage_payload(EngineNetworkVersionHistory.ExplicitAckHistorySeq),
        EngineNetworkVersionHistory.ExplicitAckHistorySeq,
    )
    montage = FGameplayAbilityRepAnimMontage()
    montage.serialize(reader)

    assert montage.is_montage is True
    assert montage.position == pytest.approx(12.5)
    assert montage.play_rate == pytest.approx(1.5)
    assert montage.blend_time == pytest.approx(0.25)
    assert montage.next_section_id == 3
    assert montage.play_instance_id == 7
    assert montage.play_count == pytest.approx(2.0)
    assert montage.anim_montage.value == 42
    assert not reader.is_error
    assert reader.at_end()


def test_montage_dynamic_animation() -> None:
    """モンタージュ以外のアニメーションでは BlendOutTime と SlotName が続く。"""
    version = EngineNetworkVersionHistory.ExplicitAckHistorySeq
    reader = _reader(_montage_payload(version, is_montage=False), version)
    montage = FGameplayAbilityRepAnimMontage()
    montage.serialize(reader)

    assert montage.is_montage is False
    assert montage.blend_out_time == pytest.approx(0.75)
    assert montage.slot_name == ""
    assert not reader.is_error
    assert reader.at_end()


def test_montage_older_version() -> None:
    """バージョン 30 では bIsMontage と PlayCount が無い。"""
    version = EngineNetworkVersionHistory.HISTORY_SUBOBJECT_DESTROY_FLAG
    reader = _reader(_montage_payload(version), version)
    montage = FGameplayAbilityRepAnimMontage()
    montage.serialize(reader)

    assert montage.play_count is None
    assert montage.play_instance_id == 7
    assert not reader.is_error
    assert reader.at_end()


# ---------------------------------------------------------------------------
# CurrentPlaylistInfo
# ---------------------------------------------------------------------------


def test_playlist_info_reads_trailing_fields() -> None:
    """ビルド 41 の CurrentPlaylistInfo を最後まで読み切れる。

    実際のリプレイ (++Fortnite+Release-41.30) から取得したペイロード。
    """
    raw = bytes.fromhex("7f400002000002000000000000000000000000000000")
    reader = NetBitReader(raw, 177)
    reader.engine_network_version = EngineNetworkVersionHistory.ExplicitAckHistorySeq

    playlist = PlaylistInfo()
    playlist.serialize(reader)

    assert playlist.id == 1039
    assert len(playlist.extra_bits) == 16  # 128 ビット分の未解析データ
    assert not reader.is_error
    assert reader.at_end()


# ---------------------------------------------------------------------------
# プレイヤーコントローラーのチャンネルオープン
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "engine_version,expected_bits",
    [
        # NetPlayerIndex のみ
        (EngineNetworkVersionHistory.HISTORY_JITTER_IN_HEADER, 8),
        (EngineNetworkVersionHistory.CustomExports, 8),
        (EngineNetworkVersionHistory.JoinNoPawn, 8),
        # + ClientHandshakeId (uint32)
        (EngineNetworkVersionHistory.ClientHandshakeId, 8 + 32),
        (EngineNetworkVersionHistory.PawnRemoteViewPitchTo16Bit, 8 + 32),
        # + LocalPlayerConnectionIdentifier (int32)
        (EngineNetworkVersionHistory.CloseChildConnection, 8 + 32 + 32),
        (EngineNetworkVersionHistory.ExplicitAckHistorySeq, 8 + 32 + 32),
    ],
)
def test_player_controller_channel_open(
    engine_version: EngineNetworkVersionHistory, expected_bits: int
) -> None:
    """バージョンに応じて追加フィールドを読み取る。"""
    from fnreplay.unreal.replay_reader import ReplayReader

    archive = NetBitReader(bytes(16))
    archive.engine_network_version = engine_version

    ReplayReader().read_player_controller_header(archive)

    assert archive.position == expected_bits
    assert not archive.is_error


# ---------------------------------------------------------------------------
# RepMovement の TeleportSeq (Unreal Engine 6.0)
# ---------------------------------------------------------------------------


def _rep_movement_writer(*, teleport_seq: int | None) -> BitWriter:
    """``bRepPhysics`` を立てた RepMovement のビット列を作る。

    量子化ベクトルは「成分ビット数 0 / extra_info 0」を選んで float 3 つで書く。
    回転は 3 成分とも「送らない」ビットだけを書く。
    """
    writer = BitWriter()
    writer.bit(0)  # bSimulatedPhysicSleep
    writer.bit(1)  # bRepPhysics
    writer.bit(0)  # bRepServerFrame
    writer.bit(0)  # bRepServerHandle

    def vector() -> None:
        writer.bits(0, 7)  # ComponentBitCount = 0 / ExtraInfo = 0
        writer.single(0.0).single(0.0).single(0.0)

    vector()  # Location
    writer.bit(0).bit(0).bit(0)  # Rotation (pitch / yaw / roll とも未送信)
    vector()  # LinearVelocity
    vector()  # AngularVelocity (bRepPhysics のため)
    if teleport_seq is not None:
        writer.bits(teleport_seq, 3)  # TeleportSeq (UE 6.0)
    writer.bit(0)  # bRepAcceleration
    return writer


def test_rep_movement_reads_teleport_seq_on_engine_6() -> None:
    """UE 6.0 (ネットワークバージョン 45) では TeleportSeq を 3 ビット読む。"""
    reader = _reader(
        _rep_movement_writer(teleport_seq=5),
        EngineNetworkVersionHistory.CongestionExperiencedBit,
    )

    movement = reader.serialize_rep_movement()

    assert movement.rep_physics is True
    assert movement.teleport_seq == 5
    assert not reader.is_error
    assert reader.at_end()


def test_rep_movement_has_no_teleport_seq_before_engine_6() -> None:
    """UE 5.x (ネットワークバージョン 44 以下) では TeleportSeq は送られない。"""
    reader = _reader(
        _rep_movement_writer(teleport_seq=None),
        EngineNetworkVersionHistory.ExplicitAckHistorySeq,
    )

    movement = reader.serialize_rep_movement()

    assert movement.rep_physics is True
    assert movement.teleport_seq == 0
    assert not reader.is_error
    assert reader.at_end()


# ---------------------------------------------------------------------------
# Large World Coordinates (UE5 以降の倍精度ベクトル)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "engine_version,expected_bits",
    [
        # float 2 つ
        (EngineNetworkVersionHistory.HISTORY_INTERFACE_PROPERTY_SERIALIZATION, 64),
        (EngineNetworkVersionHistory.HISTORY_MONTAGE_PLAY_INST_ID_SERIALIZATION, 64),
        # 26 は「21 まで + RemoteViewPitch」なので float のまま
        (EngineNetworkVersionHistory.HISTORY_21_AND_VIEWPITCH_ONLY_DO_NOT_USE, 64),
        # double 2 つ
        (EngineNetworkVersionHistory.HISTORY_SERIALIZE_DOUBLE_VECTORS_AS_DOUBLES, 128),
        (EngineNetworkVersionHistory.ExplicitAckHistorySeq, 128),
        (EngineNetworkVersionHistory.CongestionExperiencedBit, 128),
    ],
)
def test_property_vector2d_uses_doubles_from_engine_22(
    engine_version: EngineNetworkVersionHistory, expected_bits: int
) -> None:
    """FVector2D はエンジンバージョン 22 以降 double 2 つになる。"""
    reader = NetBitReader(bytes(32))
    reader.engine_network_version = engine_version

    reader.serialize_property_vector2d()

    assert reader.position == expected_bits
    assert not reader.is_error


@pytest.mark.parametrize(
    "engine_version,expected_bits",
    [
        (EngineNetworkVersionHistory.HISTORY_MONTAGE_PLAY_INST_ID_SERIALIZATION, 96),
        (EngineNetworkVersionHistory.HISTORY_21_AND_VIEWPITCH_ONLY_DO_NOT_USE, 96),
        (EngineNetworkVersionHistory.HISTORY_SERIALIZE_DOUBLE_VECTORS_AS_DOUBLES, 192),
        (EngineNetworkVersionHistory.CongestionExperiencedBit, 192),
    ],
)
def test_fvector_uses_doubles_from_engine_22(
    engine_version: EngineNetworkVersionHistory, expected_bits: int
) -> None:
    """量子化されていない FVector も同じ 22 が境界 (23 ではない)。"""
    reader = NetBitReader(bytes(32))
    reader.engine_network_version = engine_version

    reader.read_fvector()

    assert reader.position == expected_bits
    assert not reader.is_error
