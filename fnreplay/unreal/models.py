"""Unreal のリプレイに含まれる基本データ構造。

C# 版の ``Unreal.Core.Models`` に対応する。``Property`` を継承したクラスは
``serialize()`` でビットストリームから自身を読み取る。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from .enums import (
    BuildTargetType,
    ChannelCloseReason,
    ChannelName,
    ChannelType,
    EngineNetworkVersionHistory,
    ETextHistoryType,
    NetworkVersionHistory,
    PacketState,
    ReplayHeaderFlags,
    ReplayVersionHistory,
    RotatorQuantization,
    VectorQuantization,
)
from .unreal_names import unreal_name

if TYPE_CHECKING:  # pragma: no cover - 型チェック専用
    from .archives import NetBitReader
    from .net_guid_cache import NetGuidCache


class Property:
    """ビットストリームから自身を読み取れるプロパティの基底クラス。"""

    def serialize(self, reader: "NetBitReader") -> None:
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        """公開属性を辞書化する (JSON 出力用)。"""
        if hasattr(self, "__dict__"):
            items = vars(self).items()
        else:
            items = ((name, getattr(self, name)) for name in self.__slots__)
        return {k: v for k, v in items if not k.startswith("_")}


class Resolvable:
    """NetGuidCache を使って名前解決が必要なプロパティ。"""

    def resolve(self, cache: "NetGuidCache") -> None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 幾何プリミティブ
# ---------------------------------------------------------------------------


class FVector:
    """3 次元ベクトル。"""

    __slots__ = ("x", "y", "z", "scale_factor", "bits")

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        scale_factor: int = 0,
        bits: int = 0,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.scale_factor = scale_factor
        self.bits = bits

    def size(self) -> float:
        """ベクトルの長さ。"""
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def distance_to(self, other: "FVector") -> float:
        """他のベクトルとの距離。"""
        return math.sqrt(
            (other.x - self.x) ** 2 + (other.y - self.y) ** 2 + (other.z - self.z) ** 2
        )

    def __sub__(self, other: "FVector") -> "FVector":
        return FVector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FVector):
            return NotImplemented
        return (self.x, self.y, self.z) == (other.x, other.y, other.z)

    def __hash__(self) -> int:
        return hash((self.x, self.y, self.z))

    def __repr__(self) -> str:
        return f"FVector(x={self.x}, y={self.y}, z={self.z})"

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "z": self.z}


class FVector2D:
    """2 次元ベクトル。"""

    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = x
        self.y = y

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FVector2D):
            return NotImplemented
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __repr__(self) -> str:
        return f"FVector2D(x={self.x}, y={self.y})"

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y}


class FRotator:
    """ピッチ・ヨー・ロールによる回転。"""

    __slots__ = ("pitch", "yaw", "roll")

    def __init__(self, pitch: float = 0.0, yaw: float = 0.0, roll: float = 0.0) -> None:
        self.pitch = pitch
        self.yaw = yaw
        self.roll = roll

    def __repr__(self) -> str:
        return f"FRotator(pitch={self.pitch}, yaw={self.yaw}, roll={self.roll})"

    def to_dict(self) -> dict[str, float]:
        return {"pitch": self.pitch, "yaw": self.yaw, "roll": self.roll}


class FQuat(Property):
    """クォータニオン。ネット送信時は X/Y/Z のみで W は再計算される。"""

    __slots__ = ("x", "y", "z", "w")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def serialize(self, reader: "NetBitReader") -> None:
        self.x = reader.read_single()
        self.y = reader.read_single()
        self.z = reader.read_single()
        xyz_mag_squared = self.x * self.x + self.y * self.y + self.z * self.z
        w_squared = 1.0 - xyz_mag_squared
        if w_squared >= 0.0:
            self.w = math.sqrt(w_squared)
        else:
            self.w = 0.0
            if xyz_mag_squared > 0:
                inv = 1.0 / math.sqrt(xyz_mag_squared)
                self.x *= inv
                self.y *= inv
                self.z *= inv

    def __repr__(self) -> str:
        return f"FQuat(x={self.x}, y={self.y}, z={self.z}, w={self.w})"

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "z": self.z, "w": self.w}


@dataclass
class FTransform:
    """位置・回転・スケール。"""

    rotation: FQuat | None = None
    translation: FVector | None = None
    scale_3d: FVector | None = None


# ---------------------------------------------------------------------------
# NetGUID
# ---------------------------------------------------------------------------


class NetworkGUID(Property):
    """ネットワーク上のオブジェクト識別子。"""

    __slots__ = ("value",)

    def __init__(self, value: int = 0) -> None:
        self.value = value

    def is_valid(self) -> bool:
        return self.value > 0

    def is_dynamic(self) -> bool:
        return self.value > 0 and (self.value & 1) != 1

    def is_default(self) -> bool:
        return self.value == 1

    def serialize(self, reader: "NetBitReader") -> None:
        self.value = reader.read_int_packed()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.value})"

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value}


class ActorGuid(NetworkGUID):
    """アクターを指す NetGUID。"""

    __slots__ = ()


class ItemDefinition(NetworkGUID, Resolvable):
    """アイテム定義への参照。解決するとパス名が入る。"""

    __slots__ = ("name",)

    def __init__(self, value: int = 0) -> None:
        super().__init__(value)
        self.name: str | None = None

    def resolve(self, cache: "NetGuidCache") -> None:
        if self.is_valid():
            name = cache.try_get_path_name(self.value)
            if name is not None:
                self.name = name

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "name": self.name}


# ---------------------------------------------------------------------------
# 名前・文字列系プロパティ
# ---------------------------------------------------------------------------


class FName(Property):
    """FName (名前テーブル参照または文字列)。"""

    __slots__ = ("name",)

    def __init__(self, name: str | None = None) -> None:
        self.name = name

    def serialize(self, reader: "NetBitReader") -> None:
        self.name = reader.serialize_property_name()

    def __str__(self) -> str:
        return self.name or ""

    def __repr__(self) -> str:
        return f"FName({self.name!r})"

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name}


class FStaticName(Property):
    """ハードコードされた名前を含む FName。"""

    __slots__ = ("value",)

    def __init__(self, value: str | None = None) -> None:
        self.value = value

    def serialize(self, reader: "NetBitReader") -> None:
        is_hardcoded = reader.read_boolean()
        if is_hardcoded:
            if reader.engine_network_version < EngineNetworkVersionHistory.HISTORY_CHANNEL_NAMES:
                name_index = reader.read_uint32()
            else:
                name_index = reader.read_int_packed()
            self.value = unreal_name(name_index)
            return
        self.value = reader.read_fstring()
        reader.read_int32()  # in_number

    def __str__(self) -> str:
        return self.value or ""

    def __repr__(self) -> str:
        return f"FStaticName({self.value!r})"

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value}


class FText(Property):
    """ローカライズ文字列。"""

    __slots__ = ("namespace", "key", "text")

    def __init__(self) -> None:
        self.namespace: str | None = None
        self.key: str | None = None
        self.text: str | None = None

    def serialize(self, reader: "NetBitReader") -> None:
        reader.read_int32()  # flags
        history_type = reader.read_byte()
        if history_type == ETextHistoryType.Base:
            self.namespace = reader.read_fstring()
            self.key = reader.read_fstring()
            self.text = reader.read_fstring()

    def __repr__(self) -> str:
        return f"FText({self.text!r})"


class FDateTime(Property):
    """.NET の DateTime tick 表現による日時。"""

    __slots__ = ("ticks",)

    _EPOCH = datetime(1, 1, 1)

    def __init__(self) -> None:
        self.ticks = 0

    def serialize(self, reader: "NetBitReader") -> None:
        self.ticks = reader.read_uint64()

    @property
    def time(self) -> datetime | None:
        """tick を datetime に変換する。範囲外なら None。"""
        try:
            return self._EPOCH + timedelta(microseconds=self.ticks // 10)
        except (OverflowError, OSError, ValueError):
            return None

    def to_dict(self) -> dict[str, Any]:
        time = self.time
        return {"ticks": self.ticks, "time": time.isoformat() if time else None}


# ---------------------------------------------------------------------------
# GameplayTag
# ---------------------------------------------------------------------------


class FGameplayTag(Property, Resolvable):
    """GameplayTag。インデックスを名前に解決できる。"""

    __slots__ = ("tag_name", "tag_index")

    def __init__(self, reader: "NetBitReader | None" = None) -> None:
        self.tag_name: str | None = None
        self.tag_index = 0
        if reader is not None:
            self.serialize(reader)

    def serialize(self, reader: "NetBitReader") -> None:
        serialize_replication_method = (
            reader.engine_network_version >= EngineNetworkVersionHistory.CustomExports
        )
        use_fast_replication = True
        use_dynamic_replication = False
        if serialize_replication_method:
            use_fast_replication = reader.read_bit()
            if not use_fast_replication:
                use_dynamic_replication = reader.read_bit()

        if use_fast_replication:
            self.tag_index = reader.read_int_packed()
        elif use_dynamic_replication:
            self.tag_index = reader.read_int_packed()
            if self.tag_index > 0:
                reader.read_bit()  # bIsAssignedByAuthority

    def resolve(self, cache: "NetGuidCache") -> None:
        name = cache.try_get_tag_name(self.tag_index)
        if name is not None:
            self.tag_name = name

    def __repr__(self) -> str:
        return f"FGameplayTag({self.tag_name or self.tag_index!r})"

    def to_dict(self) -> dict[str, Any]:
        return {"tag_index": self.tag_index, "tag_name": self.tag_name}


class FGameplayTagContainer(Property, Resolvable):
    """GameplayTag の集合。"""

    __slots__ = ("tags",)

    def __init__(self) -> None:
        self.tags: list[FGameplayTag] = []

    def serialize(self, reader: "NetBitReader") -> None:
        # 先頭 1 ビットが空コンテナかどうかを表す
        if reader.read_bit():
            return
        num_tags = reader.read_bits_to_int(7)
        self.tags = [FGameplayTag(reader) for _ in range(num_tags)]

    def resolve(self, cache: "NetGuidCache") -> None:
        for tag in self.tags:
            tag.resolve(cache)

    def to_dict(self) -> dict[str, Any]:
        return {"tags": [t.to_dict() for t in self.tags]}


# ---------------------------------------------------------------------------
# その他のプロパティ構造体
# ---------------------------------------------------------------------------


class FHitResult(Property):
    """トレース/衝突の結果。"""

    def __init__(self, reader: "NetBitReader | None" = None) -> None:
        self.blocking_hit = False
        self.start_penetrating = False
        self.face_index = 0
        self.element_index = 0
        self.time = 0.0
        self.distance = 0.0
        self.location: FVector | None = None
        self.impact_point: FVector | None = None
        self.normal: FVector | None = None
        self.impact_normal: FVector | None = None
        self.trace_start: FVector | None = None
        self.trace_end: FVector | None = None
        self.penetration_depth = 0.0
        self.item = 0
        self.phys_material = 0
        self.actor = 0
        self.component = 0
        self.bone_name: str | None = None
        self.my_bone_name: str | None = None
        if reader is not None:
            self.serialize(reader)

    def serialize(self, reader: "NetBitReader") -> None:
        self.blocking_hit = reader.read_bit()
        self.start_penetrating = reader.read_bit()
        impact_point_equals_location = reader.read_bit()
        impact_normal_equals_normal = reader.read_bit()
        invalid_item = reader.read_bit()
        invalid_face_index = reader.read_bit()
        no_penetration_depth = reader.read_bit()
        has_element_index = (
            reader.engine_network_version
            >= EngineNetworkVersionHistory.HISTORY_ENUM_SERIALIZATION_COMPAT
        )
        invalid_element_index = has_element_index and reader.read_bit()

        self.time = reader.read_single()
        self.location = reader.read_packed_vector(1, 20)
        self.normal = reader.serialize_property_vector_normal()
        self.impact_point = (
            reader.read_packed_vector(1, 20) if not impact_point_equals_location else self.location
        )
        self.impact_normal = (
            reader.serialize_property_vector_normal()
            if not impact_normal_equals_normal
            else self.normal
        )
        self.trace_start = reader.read_packed_vector(1, 20)
        self.trace_end = reader.read_packed_vector(1, 20)
        self.penetration_depth = 0.0 if no_penetration_depth else reader.read_single()
        self.distance = (self.impact_point - self.trace_start).size()
        self.item = 0 if invalid_item else reader.read_int32()
        self.phys_material = reader.serialize_property_object()
        self.actor = reader.serialize_property_object()
        self.component = reader.serialize_property_object()
        self.bone_name = reader.serialize_property_name()
        self.face_index = 0 if invalid_face_index else reader.read_int32()
        self.element_index = (
            reader.read_byte() if (has_element_index and not invalid_element_index) else 0
        )


class FPredictionKey(Property):
    """クライアント予測キー。"""

    __slots__ = ("current_key", "base_key", "is_server_initiated")

    def __init__(self) -> None:
        self.current_key = 0
        self.base_key = 0
        self.is_server_initiated = False

    def serialize(self, reader: "NetBitReader") -> None:
        # BaseKey はエンジンバージョン 34 以降は複製されない
        # (FEngineNetworkCustomVersion::PredictionKeyBaseNotReplicated)
        replicates_base_key = (
            reader.engine_network_version
            < EngineNetworkVersionHistory.PredictionKeyBaseNotReplicated
        )

        has_base_key = False
        valid_key_for_connection = reader.read_bit()
        if replicates_base_key and valid_key_for_connection:
            has_base_key = reader.read_bit()
        self.is_server_initiated = reader.read_bit()
        if valid_key_for_connection:
            self.current_key = reader.read_int16()
            if has_base_key:
                self.base_key = reader.read_int16()


class FGameplayEffectContextHandle(Property):
    """GameplayEffect の発生コンテキスト。"""

    def __init__(self) -> None:
        self.instigator = 0
        self.effect_causer = 0
        self.ability_cdo = 0
        self.source_object = 0
        self.actors: list[ActorGuid] = []
        self.hit_result: FHitResult | None = None
        self.world_origin: FVector | None = None
        self.has_world_origin = False

    def serialize(self, reader: "NetBitReader") -> None:
        if not reader.read_bit():
            return
        rep_bits = reader.read_bits_to_int(7)
        if rep_bits & (1 << 0):
            self.instigator = reader.read_int_packed()
        if rep_bits & (1 << 1):
            self.effect_causer = reader.read_int_packed()
        if rep_bits & (1 << 2):
            self.ability_cdo = reader.read_int_packed()
        if rep_bits & (1 << 3):
            self.source_object = reader.read_int_packed()
        if rep_bits & (1 << 4):
            # SafeNetSerializeTArray_HeaderOnly
            bit_count = math.ceil(math.log2(31))
            array_num = reader.read_bits_to_int(bit_count)
            self.actors = [ActorGuid(reader.read_int_packed()) for _ in range(array_num)]
        if rep_bits & (1 << 5):
            self.hit_result = FHitResult(reader)
        if rep_bits & (1 << 6):
            self.world_origin = reader.serialize_property_vector100()
            self.has_world_origin = True
        else:
            self.has_world_origin = False


class _RepFlag:
    """FGameplayCueParameters の複製ビット位置。"""

    REP_NormalizedMagnitude = 0
    REP_RawMagnitude = 1
    REP_EffectContext = 2
    REP_Location = 3
    REP_Normal = 4
    REP_Instigator = 5
    REP_EffectCauser = 6
    REP_SourceObject = 7
    REP_TargetAttachComponent = 8
    REP_PhysMaterial = 9
    REP_GELevel = 10
    REP_AbilityLevel = 11
    REP_MAX = 12


class FGameplayCueParameters(Property):
    """GameplayCue のパラメータ。"""

    def __init__(self) -> None:
        self.normalized_magnitude = 0.0
        self.raw_magnitude = 0.0
        self.effect_context: FGameplayEffectContextHandle | None = None
        self.matched_tag_name: FGameplayTag | None = None
        self.original_tag: FGameplayTag | None = None
        self.aggregated_source_tags = FGameplayTagContainer()
        self.aggregated_target_tags = FGameplayTagContainer()
        self.location: FVector | None = None
        self.normal: FVector | None = None
        self.instigator = 0
        self.effect_causer = 0
        self.source_object = 0
        self.physical_material = 0
        self.gameplay_effect_level = 0
        self.ability_level = 0
        self.target_attach_component = 0

    def serialize(self, reader: "NetBitReader") -> None:
        num_level_bits = 5
        rep_bits = reader.read_bits_to_int(_RepFlag.REP_MAX)

        # タグコンテナは空でも 1 ビットで表現されるため RepBits には含まれない
        self.aggregated_source_tags.serialize(reader)
        self.aggregated_target_tags.serialize(reader)

        if rep_bits & (1 << _RepFlag.REP_NormalizedMagnitude):
            self.normalized_magnitude = reader.read_single()
        if rep_bits & (1 << _RepFlag.REP_RawMagnitude):
            self.raw_magnitude = reader.read_single()
        if rep_bits & (1 << _RepFlag.REP_EffectContext):
            if reader.read_bit():
                handle = FGameplayEffectContextHandle()
                handle.serialize(reader)
                self.effect_context = handle
        if rep_bits & (1 << _RepFlag.REP_Location):
            self.location = reader.serialize_property_vector10()
        if rep_bits & (1 << _RepFlag.REP_Normal):
            self.normal = reader.serialize_property_vector_normal()
        if rep_bits & (1 << _RepFlag.REP_Instigator):
            self.instigator = reader.read_int_packed()
        if rep_bits & (1 << _RepFlag.REP_EffectCauser):
            self.effect_causer = reader.read_int_packed()
        if rep_bits & (1 << _RepFlag.REP_SourceObject):
            self.source_object = reader.read_int_packed()
        if rep_bits & (1 << _RepFlag.REP_TargetAttachComponent):
            self.target_attach_component = reader.read_int_packed()
        if rep_bits & (1 << _RepFlag.REP_PhysMaterial):
            self.physical_material = reader.read_int_packed()
        if rep_bits & (1 << _RepFlag.REP_GELevel):
            self.gameplay_effect_level = reader.read_bits_to_int(num_level_bits)
        if rep_bits & (1 << _RepFlag.REP_AbilityLevel):
            self.ability_level = reader.read_bits_to_int(num_level_bits)


class FGameplayAbilityRepAnimMontage(Property):
    """アニメーションモンタージュの複製データ。

    Unreal Engine の ``FGameplayAbilityRepAnimMontage::NetSerialize`` に合わせている。
    """

    def __init__(self) -> None:
        self.anim_montage: NetworkGUID | None = None
        self.is_montage = True
        self.play_rate = 0.0
        self.position = 0.0
        self.blend_time = 0.0
        self.next_section_id = 0
        self.rep_position = True
        self.is_stopped = True
        self.force_play_bit = False
        self.skip_position_correction = False
        self.skip_play_rate = False
        self.prediction_key: FPredictionKey | None = None
        self.section_id_to_play = 0
        self.play_instance_id = 0
        self.blend_out_time: float | None = None
        self.slot_name: str | None = None
        self.play_count: float | None = None

    def serialize(self, reader: "NetBitReader") -> None:
        engine_version = reader.engine_network_version

        # モンタージュ以外のアニメーションも送れるようになった
        if engine_version >= EngineNetworkVersionHistory.DynamicMontageSerialization:
            self.is_montage = reader.read_bit()

        if reader.read_bit():
            self.rep_position = True
            self.section_id_to_play = 0
            self.skip_position_correction = False
            # 精度の問題から、位置は圧縮せず float のまま送られる
            self.position = reader.read_single()
        else:
            self.rep_position = False
            self.skip_position_correction = True
            self.position = 0.0
            self.section_id_to_play = reader.read_bits_to_int(7)

        self.is_stopped = reader.read_bit()

        if (
            engine_version
            < EngineNetworkVersionHistory.HISTORY_MONTAGE_PLAY_INST_ID_SERIALIZATION
        ):
            self.force_play_bit = reader.read_bit()
            self.play_instance_id = 1 if self.force_play_bit else 0

        self.skip_position_correction = reader.read_bit()
        self.skip_play_rate = reader.read_bit()
        self.anim_montage = NetworkGUID(reader.read_int_packed())
        self.play_rate = reader.read_single()
        self.blend_time = reader.read_single()
        self.next_section_id = reader.read_byte()

        if (
            engine_version
            >= EngineNetworkVersionHistory.HISTORY_MONTAGE_PLAY_INST_ID_SERIALIZATION
        ):
            self.play_instance_id = reader.read_byte()

        self.prediction_key = FPredictionKey()
        self.prediction_key.serialize(reader)

        if not self.is_montage:
            self.blend_out_time = reader.read_single()
            self.slot_name = reader.read_fname()

        if engine_version >= EngineNetworkVersionHistory.MontagePlayCountSerialization:
            self.play_count = reader.read_single()


@dataclass
class FRepMovement:
    """アクターの複製された移動情報。"""

    linear_velocity: FVector | None = None
    angular_velocity: FVector | None = None
    location: FVector | None = None
    rotation: FRotator | None = None
    acceleration: FVector | None = None
    simulated_physic_sleep: bool = False
    rep_physics: bool = False
    rep_acceleration: bool = False
    #: テレポート連番 (3 ビット)。Unreal Engine 6.0 以降で ``rep_physics`` のときだけ届く
    teleport_seq: int = 0
    server_frame: int = 0
    server_physics_handle: int = 0
    location_quantization_level: VectorQuantization = VectorQuantization.RoundTwoDecimals
    velocity_quantization_level: VectorQuantization = VectorQuantization.RoundWholeNumber
    rotation_quantization_level: RotatorQuantization = RotatorQuantization.ByteComponents


# ---------------------------------------------------------------------------
# リプレイ構造
# ---------------------------------------------------------------------------


@dataclass
class NetworkReplayVersion:
    """リプレイを記録したエンジンのバージョン。"""

    major: int = 0
    minor: int = 0
    patch: int = 0
    changelist: int = 0
    branch: str = ""


@dataclass
class ReplayInfo:
    """リプレイファイルのメタ情報 (先頭に格納される)。"""

    length_in_ms: int = 0
    network_version: int = 0
    changelist: int = 0
    friendly_name: str = ""
    timestamp: datetime | None = None
    total_data_size_in_bytes: int = 0
    is_live: bool = False
    is_compressed: bool = False
    is_encrypted: bool = False
    encryption_key: bytes = b""
    file_version: ReplayVersionHistory = ReplayVersionHistory.HISTORY_INITIAL


@dataclass
class ReplayHeader:
    """リプレイのネットワークヘッダー。"""

    network_version: NetworkVersionHistory = NetworkVersionHistory.HISTORY_REPLAY_INITIAL
    network_checksum: int = 0
    engine_network_version: EngineNetworkVersionHistory = (
        EngineNetworkVersionHistory.HISTORY_INITIAL
    )
    game_network_protocol_version: int = 0
    guid: str = ""
    major: int = 0
    minor: int = 0
    patch: int = 0
    changelist: int = 0
    branch: str = ""
    ue4_version: int = 0
    ue5_version: int = 0
    package_version_licensee_ue: int = 0
    level_names_and_times: list[tuple[str, int]] = field(default_factory=list)
    flags: ReplayHeaderFlags = ReplayHeaderFlags.NONE
    game_specific_data: list[str] = field(default_factory=list)
    platform: str | None = None
    build_target_type: BuildTargetType | None = None

    def has_level_streaming_fixes(self) -> bool:
        return bool(self.flags & ReplayHeaderFlags.HasStreamingFixes)


@dataclass
class Replay:
    """リプレイ解析結果の基底クラス。"""

    info: ReplayInfo = field(default_factory=ReplayInfo)
    header: ReplayHeader = field(default_factory=ReplayHeader)


@dataclass
class EventInfo:
    """イベントチャンクのヘッダー。"""

    id: str = ""
    group: str = ""
    metadata: str = ""
    start_time: int = 0
    end_time: int = 0
    size_in_bytes: int = 0


@dataclass
class CheckpointInfo:
    """チェックポイントチャンクのヘッダー。"""

    id: str = ""
    group: str = ""
    metadata: str = ""
    start_time: int = 0
    end_time: int = 0
    size_in_bytes: int = 0


@dataclass
class ReplayDataInfo:
    """リプレイデータチャンクのヘッダー。"""

    start: int = 0
    end: int = 0
    length: int = 0


@dataclass
class PlaybackPacket:
    """再生用パケット。"""

    data: bytes = b""
    time_seconds: float = 0.0
    level_index: int = 0
    seen_level_index: int = 0
    state: PacketState = PacketState.Success


@dataclass
class NetFieldExport:
    """1 つのプロパティのエクスポート情報。"""

    handle: int = 0
    compatible_checksum: int = 0
    name: str = ""
    type: str | None = None
    is_exported: bool = False
    incompatible: bool = False
    property_id: int = -1


class NetFieldExportGroup:
    """あるクラスのプロパティ一覧。"""

    __slots__ = (
        "path_name",
        "path_name_index",
        "net_field_exports_length",
        "net_field_exports",
        "group_id",
    )

    def __init__(
        self,
        path_name: str = "",
        path_name_index: int = 0,
        net_field_exports_length: int = 0,
        net_field_exports: list[NetFieldExport | None] | None = None,
    ) -> None:
        self.path_name = path_name
        self.path_name_index = path_name_index
        self.net_field_exports_length = net_field_exports_length
        self.net_field_exports: list[NetFieldExport | None] = (
            net_field_exports
            if net_field_exports is not None
            else [None] * net_field_exports_length
        )
        self.group_id = -1

    def is_valid_index(self, handle: int) -> bool:
        return 0 <= handle < self.net_field_exports_length

    def __repr__(self) -> str:
        return f"NetFieldExportGroup({self.path_name!r}, {self.net_field_exports_length})"


@dataclass
class NetGuidCacheObject:
    """NetGUID に対応するオブジェクト情報。"""

    outer_guid: NetworkGUID | None = None
    path_name: str = ""
    network_checksum: int = 0
    read_only_timestamp: float = 0.0
    flags: int = 0
    is_broken: bool = False
    is_pending: bool = False

    @property
    def no_load(self) -> bool:
        return bool(self.flags & (1 << 0))

    @property
    def ignore_when_missing(self) -> bool:
        return bool(self.flags & (1 << 1))


@dataclass
class ExternalData:
    """アクターに紐づく外部データ。"""

    net_guid: int = 0
    archive: Any = None
    time_seconds: int = 0


@dataclass
class NetDeltaUpdate:
    """FastArray の差分更新。"""

    element_index: int = 0
    export: Any = None
    deleted: bool = False
    channel_index: int = 0


@dataclass
class FFastArraySerializerHeader:
    """FastArraySerializer のヘッダー。"""

    array_replication_key: int = 0
    base_replication_key: int = 0
    num_changed: int = 0
    num_deletes: int = 0


@dataclass
class Actor:
    """チャンネルに紐づくアクター。"""

    actor_net_guid: NetworkGUID | None = None
    archetype: NetworkGUID | None = None
    level: NetworkGUID | None = None
    location: FVector | None = None
    rotation: FRotator | None = None
    scale: FVector | None = None
    velocity: FVector | None = None


class UChannel:
    """アクターチャンネル。"""

    __slots__ = ("channel_name", "channel_index", "channel_type", "actor", "_ignore")

    def __init__(self, channel_index: int = 0) -> None:
        self.channel_name = ChannelName.NONE
        self.channel_index = channel_index
        self.channel_type = ChannelType.NONE
        self.actor: Actor | None = None
        self._ignore: set[str] = set()

    def ignore_group(self, group: str) -> None:
        self._ignore.add(group)

    def is_ignoring_group(self, group: str) -> bool:
        return group in self._ignore

    @property
    def archetype_id(self) -> int | None:
        if self.actor is not None and self.actor.archetype is not None:
            return self.actor.archetype.value
        return None

    @property
    def actor_id(self) -> int | None:
        if self.actor is not None and self.actor.actor_net_guid is not None:
            return self.actor.actor_net_guid.value
        return None


class DataBunch:
    """1 つのバンチ (チャンネル単位のデータ塊)。"""

    __slots__ = (
        "archive",
        "packet_id",
        "ch_index",
        "ch_type",
        "ch_name",
        "ch_sequence",
        "b_open",
        "b_close",
        "b_dormant",
        "b_is_replication_paused",
        "b_reliable",
        "b_partial",
        "b_partial_initial",
        "b_has_partial_custom_exports_final_bit",
        "b_partial_final",
        "b_has_package_map_exports",
        "b_has_must_be_mapped_guids",
        "b_ignore_rpcs",
        "close_reason",
    )

    def __init__(self, other: "DataBunch | None" = None) -> None:
        if other is None:
            self.archive = None
            self.packet_id = 0
            self.ch_index = 0
            self.ch_type = ChannelType.NONE
            self.ch_name = ChannelName.NONE
            self.ch_sequence = 0
            self.b_open = False
            self.b_close = False
            self.b_dormant = False
            self.b_is_replication_paused = False
            self.b_reliable = False
            self.b_partial = False
            self.b_partial_initial = False
            self.b_has_partial_custom_exports_final_bit = False
            self.b_partial_final = False
            self.b_has_package_map_exports = False
            self.b_has_must_be_mapped_guids = False
            self.b_ignore_rpcs = False
            self.close_reason = ChannelCloseReason.Destroyed
        else:
            self.archive = other.archive
            self.packet_id = other.packet_id
            self.ch_index = other.ch_index
            self.ch_type = other.ch_type
            self.ch_name = other.ch_name
            self.ch_sequence = other.ch_sequence
            self.b_open = other.b_open
            self.b_close = other.b_close
            self.b_dormant = other.b_dormant
            self.b_is_replication_paused = other.b_is_replication_paused
            self.b_reliable = other.b_reliable
            self.b_partial = other.b_partial
            self.b_partial_initial = other.b_partial_initial
            self.b_has_partial_custom_exports_final_bit = (
                other.b_has_partial_custom_exports_final_bit
            )
            self.b_partial_final = other.b_partial_final
            self.b_has_package_map_exports = other.b_has_package_map_exports
            self.b_has_must_be_mapped_guids = other.b_has_must_be_mapped_guids
            self.b_ignore_rpcs = other.b_ignore_rpcs
            self.close_reason = other.close_reason
