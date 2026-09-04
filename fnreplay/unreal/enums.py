"""Unreal のリプレイ形式で使われる列挙型。

C# 版 (Shiqan/FortniteReplayDecompressor) の `Unreal.Core.Models.Enums` に対応する。
"""

from __future__ import annotations

from enum import IntEnum, IntFlag


class EngineNetworkVersionHistory(IntEnum):
    """エンジンのネットワークバージョン履歴。

    see https://github.com/EpicGames/UnrealEngine/blob/ue6-main/Engine/Source/Runtime/Core/Public/Misc/EngineNetworkCustomVersion.h
    """

    HISTORY_INITIAL = 1
    HISTORY_REPLAY_BACKWARDS_COMPAT = 2
    HISTORY_MAX_ACTOR_CHANNELS_CUSTOMIZATION = 3
    HISTORY_REPCMD_CHECKSUM_REMOVE_PRINTF = 4
    HISTORY_NEW_ACTOR_OVERRIDE_LEVEL = 5
    HISTORY_CHANNEL_NAMES = 6
    HISTORY_CHANNEL_CLOSE_REASON = 7
    HISTORY_ACKS_INCLUDED_IN_HEADER = 8
    HISTORY_NETEXPORT_SERIALIZATION = 9
    HISTORY_NETEXPORT_SERIALIZE_FIX = 10
    HISTORY_FAST_ARRAY_DELTA_STRUCT = 11
    HISTORY_FIX_ENUM_SERIALIZATION = 12
    HISTORY_OPTIONALLY_QUANTIZE_SPAWN_INFO = 13
    HISTORY_JITTER_IN_HEADER = 14
    HISTORY_CLASSNETCACHE_FULLNAME = 15
    HISTORY_REPLAY_DORMANCY = 16
    HISTORY_ENUM_SERIALIZATION_COMPAT = 17
    HISTORY_SUBOBJECT_OUTER_CHAIN = 18
    HISTORY_HITRESULT_INSTANCEHANDLE = 19
    HISTORY_INTERFACE_PROPERTY_SERIALIZATION = 20
    HISTORY_MONTAGE_PLAY_INST_ID_SERIALIZATION = 21
    HISTORY_SERIALIZE_DOUBLE_VECTORS_AS_DOUBLES = 22
    HISTORY_PACKED_VECTOR_LWC_SUPPORT = 23
    HISTORY_PAWN_REMOTEVIEWPITCH = 24
    HISTORY_REPMOVE_SERVERFRAME_AND_HANDLE = 25
    HISTORY_21_AND_VIEWPITCH_ONLY_DO_NOT_USE = 26
    HISTORY_PLACEHOLDER = 27
    HISTORY_RUNTIME_FEATURES_COMPATIBILITY = 28
    HISTORY_SOFTOBJECTPTR_NETGUIDS = 29
    HISTORY_SUBOBJECT_DESTROY_FLAG = 30
    HISTORY_GAMESTATE_REPLCIATED_TIME_AS_DOUBLE = 31
    HISTORY_CUSTOMVERION = 32
    DynamicMontageSerialization = 33
    PredictionKeyBaseNotReplicated = 34
    RepMoveOptionalAcceleration = 35
    CustomExports = 36
    # 以下は Unreal Engine 5.6 系 (FEngineNetworkCustomVersion) の定義
    MontagePlayCountSerialization = 37
    RemoteObjectReferences = 38
    BeaconNetIDVariant = 39
    JoinNoPawn = 40
    ClientHandshakeId = 41
    PawnRemoteViewPitchTo16Bit = 42
    CloseChildConnection = 43
    ExplicitAckHistorySeq = 44
    # 以下は Unreal Engine 6.0 系 (ue6-main の FEngineNetworkCustomVersion) の定義
    CongestionExperiencedBit = 45
    LATEST = 45


class NetworkVersionHistory(IntEnum):
    """リプレイのネットワークバージョン履歴。"""

    HISTORY_REPLAY_INITIAL = 1
    HISTORY_SAVE_ABS_TIME_MS = 2
    HISTORY_INCREASE_BUFFER = 3
    HISTORY_SAVE_ENGINE_VERSION = 4
    HISTORY_EXTRA_VERSION = 5
    HISTORY_MULTIPLE_LEVELS = 6
    HISTORY_MULTIPLE_LEVELS_TIME_CHANGES = 7
    HISTORY_DELETED_STARTUP_ACTORS = 8
    HISTORY_HEADER_FLAGS = 9
    HISTORY_LEVEL_STREAMING_FIXES = 10
    HISTORY_SAVE_FULL_ENGINE_VERSION = 11
    HISTORY_HEADER_GUID = 12
    HISTORY_CHARACTER_MOVEMENT = 13
    HISTORY_CHARACTER_MOVEMENT_NOINTERP = 14
    HISTORY_GUID_NAMETABLE = 15
    HISTORY_GUIDCACHE_CHECKSUMS = 16
    HISTORY_SAVE_PACKAGE_VERSION_UE = 17
    HISTORY_RECORDING_METADATA = 18
    HISTORY_USE_CUSTOM_VERSION = 19
    LATEST = 19


class ReplayVersionHistory(IntEnum):
    """リプレイファイル自体のバージョン履歴。"""

    HISTORY_INITIAL = 0
    HISTORY_FIXEDSIZE_FRIENDLY_NAME = 1
    HISTORY_COMPRESSION = 2
    HISTORY_RECORDED_TIMESTAMP = 3
    HISTORY_STREAM_CHUNK_TIMES = 4
    HISTORY_FRIENDLY_NAME_ENCODING = 5
    HISTORY_ENCRYPTION = 6
    HISTORY_CUSTOM_VERSIONS = 7
    LATEST = 7


class ReplayHeaderFlags(IntFlag):
    """リプレイヘッダーのフラグ。"""

    NONE = 0
    ClientRecorded = 1 << 0
    HasStreamingFixes = 1 << 1
    DeltaCheckpoints = 1 << 2
    GameSpecificFrameData = 1 << 3
    ReplayConnection = 1 << 4
    ActorPrioritizationEnabled = 1 << 5
    NetRelevancyEnabled = 1 << 6
    AsyncRecorded = 1 << 7


class ReplayChunkType(IntEnum):
    """リプレイファイル内のチャンク種別。"""

    Header = 0
    ReplayData = 1
    Checkpoint = 2
    Event = 3
    Unknown = 0xFFFFFFFF


class ChannelCloseReason(IntEnum):
    """チャンネルが閉じられた理由。"""

    Destroyed = 0
    Dormancy = 1
    LevelUnloaded = 2
    Relevancy = 3
    TearOff = 4
    MAX = 15


class ChannelType(IntEnum):
    """(非推奨) チャンネル種別。"""

    NONE = 0
    Control = 1
    Actor = 2
    File = 3
    Voice = 4
    MAX = 8


class ChannelName(IntEnum):
    """チャンネル名。"""

    Control = 0
    Voice = 1
    Actor = 2
    NONE = 3


class ExportFlags(IntFlag):
    """NetGUID エクスポートのフラグ。"""

    NONE = 0
    bHasPath = 1
    bNoLoad = 2
    bHasPathAndNoLoad = 3
    bHasNetworkChecksum = 4
    bHasPathAndNetWorkChecksum = 5
    bNoLoadAndNetworkChecksum = 6
    All = 7


class ParseMode(IntEnum):
    """解析の深さ。値が大きいほど多くの情報を読み取る。"""

    EventsOnly = 0
    Minimal = 1
    Normal = 2
    Full = 3
    Debug = 4
    Ignore = 5


class RepLayoutCmdType(IntEnum):
    """プロパティのシリアライズ方式。"""

    DynamicArray = 0
    Return = 1
    Property = 2
    PropertyBool = 3
    PropertyFloat = 4
    PropertyInt = 5
    PropertyByte = 6
    PropertyName = 7
    PropertyObject = 8
    PropertyUInt32 = 9
    PropertyVector = 10
    PropertyRotator = 11
    PropertyPlane = 12
    PropertyVector100 = 13
    PropertyNetId = 14
    RepMovement = 15
    PropertyVectorNormal = 16
    PropertyVector10 = 17
    PropertyVectorQ = 18
    PropertyString = 19
    PropertyUInt64 = 20
    PropertyNativeBool = 21
    PropertySoftObject = 22
    PropertyWeakObject = 23
    PropertyInterface = 24
    NetSerializeStructWithObjectReferences = 25
    PropertyDouble = 94
    PropertyVector2D = 95
    PropertyInt16 = 96
    PropertyUInt16 = 97
    PropertyQuat = 98
    Enum = 99
    Ignore = 100


class VectorQuantization(IntEnum):
    """ベクトルの量子化レベル。"""

    RoundWholeNumber = 0
    RoundOneDecimal = 1
    RoundTwoDecimals = 2


class RotatorQuantization(IntEnum):
    """回転の量子化レベル。"""

    ByteComponents = 0
    ShortComponents = 1


class UniqueIdEncodingFlags(IntFlag):
    """NetId のエンコード方式フラグ。"""

    NotEncoded = 0
    IsEncoded = 1 << 0
    IsEmpty = 1 << 1
    Unused1 = 1 << 2
    Reserved1 = 1 << 3
    Reserved2 = 1 << 4
    Reserved3 = 1 << 5
    Reserved4 = 1 << 6
    Reserved5 = 1 << 7
    FlagsMask = (1 << 3) - 1
    TypeMask = 255 ^ ((1 << 3) - 1)


class PacketState(IntEnum):
    """パケット読み取りの結果。"""

    Success = 0
    End = 1
    Error = 2


class ArchiveEndIndex(IntEnum):
    """一時的な終端位置を保持するためのスロット識別子。"""

    BUNCH = 0
    CONTENT_BLOCK_PAYLOAD = 1
    FIELD_HEADER_PAYLOAD = 2
    READ_ARRAY_FIELD = 3


class BuildTargetType(IntEnum):
    """ビルドターゲット種別。"""

    Unknown = 0
    Game = 1
    Server = 2
    Client = 3
    Editor = 4
    Program = 5


class ETextHistoryType(IntEnum):
    """FText の履歴種別。"""

    NONE = -1
    Base = 0
    NamedFormat = 1
    OrderedFormat = 2
    ArgumentFormat = 3
    AsNumber = 4
    AsPercent = 5
    AsCurrency = 6
    AsDate = 7
    AsTime = 8
    AsDateTime = 9
    Transform = 10
    StringTableEntry = 11
    TextGenerator = 12


class SeekOrigin(IntEnum):
    """シークの基準位置。"""

    Begin = 0
    Current = 1
    End = 2
