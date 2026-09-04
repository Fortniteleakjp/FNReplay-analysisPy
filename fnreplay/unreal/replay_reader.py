"""Unreal のリプレイファイルを読み取る汎用リーダー。

C# 版の ``Unreal.Core.ReplayReader<T>`` に対応する。ゲーム固有の処理は
``on_export_read`` などをオーバーライドして実装する。
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from .archives import BinaryReader, BitReader, FArchive, NetBitReader
from .enums import (
    ArchiveEndIndex,
    BuildTargetType,
    ChannelCloseReason,
    ChannelName,
    ChannelType,
    EngineNetworkVersionHistory,
    ExportFlags,
    NetworkVersionHistory,
    PacketState,
    ParseMode,
    ReplayChunkType,
    ReplayHeaderFlags,
    ReplayVersionHistory,
    SeekOrigin,
)
from .exceptions import InvalidReplayException, MalformedPacketException, UnknownEventException
from .export_registry import REGISTRY, ExportRegistry
from .models import (
    Actor,
    CheckpointInfo,
    DataBunch,
    EventInfo,
    ExternalData,
    FFastArraySerializerHeader,
    FRotator,
    FVector,
    NetDeltaUpdate,
    NetFieldExport,
    NetFieldExportGroup,
    NetGuidCacheObject,
    NetworkGUID,
    NetworkReplayVersion,
    Replay,
    ReplayDataInfo,
    ReplayHeader,
    ReplayInfo,
    UChannel,
)
from .net_field_parser import NetFieldParser
from .net_guid_cache import NetGuidCache
from .paths import remove_all_path_prefixes

logger = logging.getLogger(__name__)

DEFAULT_MAX_CHANNEL_SIZE = 32767
FILE_MAGIC = 0x1CA2E27F
NETWORK_MAGIC = 0x2CF5A13D
METADATA_MAGIC = 0x3D06B24E
MAX_PACKET_SIZE_IN_BITS = 16384  # 2 * 1024 * 8
OLD_MAX_ACTOR_CHANNELS = 10240
MAX_GUID_COUNT = 2048

#: .NET の DateTime.FromBinary 相当の変換に使うマスク
_TICKS_MASK = 0x3FFFFFFFFFFFFFFF


class ReplayReader:
    """リプレイファイルを解析する基底クラス。"""

    #: 生成するリプレイオブジェクトの型
    replay_factory: Callable[[], Replay] = Replay

    def __init__(
        self,
        parse_mode: ParseMode = ParseMode.Minimal,
        registry: ExportRegistry = REGISTRY,
    ) -> None:
        self.parse_mode = parse_mode
        self.replay: Replay = self.replay_factory()
        self.guid_cache = NetGuidCache()
        self.net_field_parser = NetFieldParser(self.guid_cache, parse_mode, registry)

        self._replay_data_index = 0
        self._checkpoint_index = 0
        self._packet_index = 0
        self._bunch_index = 0
        self._in_packet_id = 0
        self._in_reliable = 0
        self._partial_bunch: DataBunch | None = None

        self._packet_reader = NetBitReader()
        self._export_reader = NetBitReader()
        self._cmd_reader = NetBitReader()

        self.channels: list[UChannel | None] = [None] * DEFAULT_MAX_CHANNEL_SIZE

    @property
    def is_debug_mode(self) -> bool:
        """デバッグモードで解析しているか。"""
        return self.parse_mode == ParseMode.Debug

    # -- エントリポイント ---------------------------------------------------

    def read_replay(self, archive: FArchive) -> Replay:
        """アーカイブ全体を解析する。"""
        self.replay = self.replay_factory()
        self.read_replay_info(archive)
        self.read_replay_chunks(archive)
        self.cleanup()
        return self.replay

    def cleanup(self) -> None:
        """解析状態を初期化する。"""
        self._in_reliable = 0
        self.channels = [None] * DEFAULT_MAX_CHANNEL_SIZE
        self._replay_data_index = 0
        self._checkpoint_index = 0
        self._packet_index = 0
        self._bunch_index = 0
        self._in_packet_id = 0
        self._partial_bunch = None
        self.guid_cache.cleanup()

    # -- チャンク -----------------------------------------------------------

    def read_replay_chunks(self, archive: FArchive) -> None:
        """チャンクを順に読み取る。"""
        while not archive.at_end():
            chunk_type = archive.read_uint32_as_enum(ReplayChunkType)
            chunk_size = archive.read_int32()
            offset = archive.position

            if chunk_size <= 0 or chunk_size + offset > 0x7FFFFFFF:
                logger.error(
                    "チャンクサイズが不正です (size=%s, type=%s, offset=%s)。解析を中止します。",
                    chunk_size,
                    chunk_type,
                    offset,
                )
                archive.set_error()
                return

            if chunk_type == ReplayChunkType.ReplayData and self.parse_mode > ParseMode.EventsOnly:
                self.read_replay_data(archive, chunk_size)
            elif chunk_type == ReplayChunkType.Checkpoint:
                # チェックポイントは早送り用のため通常は読み飛ばす
                pass
            elif chunk_type == ReplayChunkType.Event:
                self.read_event(archive)
            elif chunk_type == ReplayChunkType.Header:
                self.read_replay_header(archive)

            if archive.position != offset + chunk_size:
                logger.debug(
                    "チャンク (%s, offset=%s) を最後まで読み取っていません。", chunk_type, offset
                )
                archive.seek(offset + chunk_size, SeekOrigin.Begin)

    def read_replay_info(self, archive: FArchive) -> None:
        """ファイル先頭のメタ情報を読み取る。"""
        magic_number = archive.read_uint32()
        if magic_number != FILE_MAGIC:
            logger.error(
                "リプレイファイルではありません (magic=%s, expected=%s)", magic_number, FILE_MAGIC
            )
            raise InvalidReplayException("リプレイファイルではありません")

        file_version = archive.read_uint32_as_enum(ReplayVersionHistory)
        archive.replay_version = file_version
        if file_version > ReplayVersionHistory.LATEST:
            logger.warning("未知の ReplayVersionHistory です: %s", file_version)

        if archive.replay_version >= ReplayVersionHistory.HISTORY_CUSTOM_VERSIONS:
            custom_version_count = archive.read_int32()
            # GUID 16 バイト + バージョン 4 バイト
            archive.skip_bytes(custom_version_count * 20)

        info = ReplayInfo(
            file_version=file_version,
            length_in_ms=archive.read_uint32(),
            network_version=archive.read_uint32(),
            changelist=archive.read_uint32(),
            friendly_name=archive.read_fstring(),
            is_live=archive.read_uint32_as_boolean(),
        )

        if file_version >= ReplayVersionHistory.HISTORY_RECORDED_TIMESTAMP:
            info.timestamp = _from_dotnet_binary(archive.read_int64())
        if file_version >= ReplayVersionHistory.HISTORY_COMPRESSION:
            info.is_compressed = archive.read_uint32_as_boolean()
        if file_version >= ReplayVersionHistory.HISTORY_ENCRYPTION:
            info.is_encrypted = archive.read_uint32_as_boolean()
            size = archive.read_uint32()
            info.encryption_key = bytes(archive.read_bytes(size))

        if not info.is_live and info.is_encrypted and len(info.encryption_key) == 0:
            logger.error("暗号化されたリプレイですが鍵がありません")
            raise InvalidReplayException("暗号化されたリプレイですが鍵がありません")

        if info.is_live and info.is_encrypted:
            logger.error("暗号化されたリプレイですがまだ完了していません")
            raise InvalidReplayException("暗号化されたリプレイですがまだ完了していません")

        self.replay.info = info

    def read_replay_header(self, archive: FArchive) -> None:
        """ネットワークヘッダーを読み取る。"""
        magic = archive.read_uint32()
        if magic != NETWORK_MAGIC:
            logger.error(
                "Header.Magic != NETWORK_DEMO_MAGIC (magic=%s, expected=%s)", magic, NETWORK_MAGIC
            )
            raise InvalidReplayException("Header.Magic != NETWORK_DEMO_MAGIC")

        header = ReplayHeader(network_version=archive.read_uint32_as_enum(NetworkVersionHistory))

        if header.network_version > NetworkVersionHistory.LATEST:
            logger.warning("未知の NetworkVersionHistory です: %s", header.network_version)

        if header.network_version <= NetworkVersionHistory.HISTORY_EXTRA_VERSION:
            logger.error("Header.Version < MIN_NETWORK_DEMO_VERSION: %s", header.network_version)
            raise InvalidReplayException("Header.Version < MIN_NETWORK_DEMO_VERSION")

        if header.network_version >= NetworkVersionHistory.HISTORY_USE_CUSTOM_VERSION:
            custom_version_count = archive.read_int32()
            archive.skip_bytes(custom_version_count * 20)

        header.network_checksum = archive.read_uint32()
        header.engine_network_version = archive.read_uint32_as_enum(EngineNetworkVersionHistory)
        if header.engine_network_version > EngineNetworkVersionHistory.LATEST:
            logger.warning(
                "未知の EngineNetworkVersionHistory です: %s", header.engine_network_version
            )
        header.game_network_protocol_version = archive.read_uint32()

        if header.network_version >= NetworkVersionHistory.HISTORY_HEADER_GUID:
            header.guid = archive.read_guid()

        if header.network_version >= NetworkVersionHistory.HISTORY_SAVE_FULL_ENGINE_VERSION:
            header.major = archive.read_uint16()
            header.minor = archive.read_uint16()
            header.patch = archive.read_uint16()
            header.changelist = archive.read_uint32()
            header.branch = archive.read_fstring()
            archive.network_replay_version = NetworkReplayVersion(
                major=header.major,
                minor=header.minor,
                patch=header.patch,
                changelist=header.changelist,
                branch=header.branch,
            )
        else:
            header.changelist = archive.read_uint32()

        if header.network_version >= NetworkVersionHistory.HISTORY_RECORDING_METADATA:
            header.ue4_version = archive.read_uint32()
            header.ue5_version = archive.read_uint32()
            header.package_version_licensee_ue = archive.read_uint32()

        if header.network_version <= NetworkVersionHistory.HISTORY_MULTIPLE_LEVELS:
            raise NotImplementedError("HISTORY_MULTIPLE_LEVELS は未対応です")

        header.level_names_and_times = archive.read_tuple_array(
            archive.read_fstring, archive.read_uint32
        )

        if header.network_version >= NetworkVersionHistory.HISTORY_HEADER_FLAGS:
            header.flags = archive.read_uint32_as_enum(ReplayHeaderFlags)
            archive.replay_header_flags = header.flags

        header.game_specific_data = archive.read_array(archive.read_fstring)

        if header.network_version >= NetworkVersionHistory.HISTORY_SAVE_PACKAGE_VERSION_UE:
            archive.read_single()  # min_record_hz
            archive.read_single()  # max_record_hz
            archive.read_single()  # frame_limit_in_ms
            archive.read_single()  # checkpoint_limit_in_ms
            header.platform = archive.read_fstring()
            archive.read_byte()  # build_config
            header.build_target_type = archive.read_byte_as_enum(BuildTargetType)

        archive.engine_network_version = header.engine_network_version
        archive.network_version = header.network_version
        self.replay.header = header

        for reader in (self._packet_reader, self._export_reader, self._cmd_reader):
            reader.engine_network_version = header.engine_network_version
            reader.network_version = header.network_version
            reader.replay_header_flags = header.flags
            # ゲーム側のビルド判定に使うため、リーダーにもバージョンを渡しておく
            reader.network_replay_version = archive.network_replay_version

    def read_replay_data(self, archive: FArchive, fallback_chunk_size: int) -> None:
        """ReplayData チャンクを読み取り、パケットへ展開する。"""
        info = ReplayDataInfo()
        if archive.replay_version >= ReplayVersionHistory.HISTORY_STREAM_CHUNK_TIMES:
            info.start = archive.read_uint32()
            info.end = archive.read_uint32()
            info.length = archive.read_uint32()
        else:
            info.length = fallback_chunk_size

        if archive.replay_version >= ReplayVersionHistory.HISTORY_ENCRYPTION:
            archive.read_int32()  # memory_size_in_bytes

        decrypted = self.decrypt_buffer(archive, info.length)
        binary_archive = self.decompress(decrypted)

        while not binary_archive.at_end():
            self.read_demo_frame_into_playback_packets(binary_archive)

        self._replay_data_index += 1

    def read_event(self, archive: FArchive) -> None:
        """イベントチャンクを読み取る (ゲーム固有処理でオーバーライドする)。"""
        info = EventInfo(
            id=archive.read_fstring(),
            group=archive.read_fstring(),
            metadata=archive.read_fstring(),
            start_time=archive.read_uint32(),
            end_time=archive.read_uint32(),
            size_in_bytes=archive.read_int32(),
        )
        raise UnknownEventException(
            f"未知のイベントです (id={info.id}, group={info.group}, "
            f"metadata={info.metadata}, size={info.size_in_bytes})"
        )

    def read_checkpoint(self, archive: FArchive) -> None:
        """チェックポイントチャンクを読み取る。"""
        info = CheckpointInfo(
            id=archive.read_fstring(),
            group=archive.read_fstring(),
            metadata=archive.read_fstring(),
            start_time=archive.read_uint32(),
            end_time=archive.read_uint32(),
            size_in_bytes=archive.read_int32(),
        )

        decrypted = self.decrypt_buffer(archive, info.size_in_bytes)
        binary_archive = self.decompress(decrypted)

        if binary_archive.has_delta_checkpoints():
            binary_archive.read_uint32()  # checkpoint_size

        if binary_archive.has_level_streaming_fixes():
            binary_archive.read_int64()  # packet_offset

        if binary_archive.network_version >= NetworkVersionHistory.HISTORY_MULTIPLE_LEVELS:
            binary_archive.read_int32()  # level_for_checkpoint

        if binary_archive.network_version >= NetworkVersionHistory.HISTORY_DELETED_STARTUP_ACTORS:
            if binary_archive.has_delta_checkpoints():
                raise NotImplementedError("差分チェックポイントは未対応です")
            binary_archive.read_array(binary_archive.read_fstring)

        # SerializeGuidCache
        count = binary_archive.read_int32()
        for _ in range(count):
            binary_archive.read_int_packed()  # guid
            cache_object = NetGuidCacheObject(
                outer_guid=NetworkGUID(binary_archive.read_int_packed())
            )
            if binary_archive.network_version < NetworkVersionHistory.HISTORY_GUID_NAMETABLE:
                cache_object.path_name = binary_archive.read_fstring()
            else:
                is_exported = binary_archive.read_boolean()
                if is_exported:
                    cache_object.path_name = binary_archive.read_fstring()
                else:
                    binary_archive.read_int_packed()  # path_name_index
            if binary_archive.network_version < NetworkVersionHistory.HISTORY_GUIDCACHE_CHECKSUMS:
                cache_object.network_checksum = binary_archive.read_uint32()
            cache_object.flags = binary_archive.read_byte()

        if binary_archive.has_delta_checkpoints():
            raise NotImplementedError("差分チェックポイントは未対応です")

        # マッピングをリセットして読み直す
        self.guid_cache.net_field_export_group_map.clear()
        self.guid_cache.net_field_export_group_index_to_group.clear()

        num_net_field_export_groups = binary_archive.read_uint32()
        for _ in range(num_net_field_export_groups):
            group = self.read_net_field_export_group_map(binary_archive)
            self.guid_cache.net_field_export_group_index_to_group[group.path_name_index] = (
                group.path_name
            )
            self.guid_cache.add_to_export_group_map(group.path_name, group)

        for channel in self.channels:
            if channel is not None:
                channel.actor = None

        self.read_demo_frame_into_playback_packets(binary_archive)
        self._checkpoint_index += 1

    # -- フレーム -----------------------------------------------------------

    def read_demo_frame_into_playback_packets(self, archive: FArchive) -> None:
        """1 フレーム分のデータをパケットへ展開する。"""
        if archive.network_version >= NetworkVersionHistory.HISTORY_MULTIPLE_LEVELS:
            archive.read_int32()  # current_level_index

        archive.read_single()  # time_seconds

        if archive.network_version >= NetworkVersionHistory.HISTORY_LEVEL_STREAMING_FIXES:
            self.read_export_data(archive)

        if archive.has_level_streaming_fixes():
            num_streaming_levels = archive.read_int_packed()
            for _ in range(num_streaming_levels):
                archive.read_fstring()  # level_name
        else:
            num_streaming_levels = archive.read_int_packed()
            for _ in range(num_streaming_levels):
                archive.read_fstring()  # package_name
                archive.read_fstring()  # package_name_to_load
                archive.read_ftransform()  # level_transform

        if archive.has_level_streaming_fixes():
            archive.read_uint64()  # external_offset

        self.read_external_data(archive)

        if archive.has_game_specific_frame_data():
            skip_external_offset = archive.read_uint64()
            if skip_external_offset > 0:
                archive.skip_bytes(skip_external_offset)

        while True:
            if archive.has_level_streaming_fixes():
                archive.read_int_packed()  # seen_level_index
            state = self.read_packet(archive)
            if state != PacketState.Success:
                break

    def read_packet(self, archive: FArchive) -> PacketState:
        """1 パケット分を読み取る。"""
        buffer_size = archive.read_int32()
        if buffer_size == 0:
            return PacketState.End
        if buffer_size > 2048:
            logger.warning("read_packet: バッファサイズが 2048 を超えています")
            return PacketState.Error
        if buffer_size < 0:
            logger.warning("read_packet: バッファサイズが負の値です")
            return PacketState.Error

        self.received_raw_packet(archive.read_bytes(buffer_size))
        return PacketState.Success

    def read_external_data(self, archive: FArchive) -> None:
        """フレームに含まれる外部データを読み取る。"""
        while True:
            external_data_num_bits = archive.read_int_packed()
            if external_data_num_bits == 0:
                return

            net_guid = archive.read_int_packed()
            logger.debug(
                "外部データを検出しました (netguid=%s, bits=%s)", net_guid, external_data_num_bits
            )
            data = archive.read_bytes((external_data_num_bits + 7) >> 3)
            reader = BinaryReader(data)
            reader.copy_version_from(archive)
            self.guid_cache.external_data[net_guid] = ExternalData(
                net_guid=net_guid, archive=reader
            )

    # -- ネットフィールドエクスポート ----------------------------------------

    def read_export_data(self, archive: FArchive) -> None:
        """フレーム先頭のエクスポート情報を読み取る。"""
        self.read_net_field_exports(archive)
        self.read_net_export_guids(archive)

    def read_net_export_guids(self, archive: FArchive) -> None:
        """エクスポートされた NetGUID を読み取る。"""
        num_guids = archive.read_int_packed()
        for _ in range(num_guids):
            size = archive.read_int32()
            self._export_reader.fill_buffer(archive.read_bytes(size))
            self.internal_load_object(self._export_reader, True)

    def read_net_field_export(self, archive: FArchive) -> NetFieldExport | None:
        """1 つのネットフィールドエクスポートを読み取る。"""
        is_exported = archive.read_boolean()
        if not is_exported:
            return None

        field_export = NetFieldExport(
            handle=archive.read_int_packed(),
            compatible_checksum=archive.read_uint32(),
            is_exported=True,
        )

        if (
            archive.engine_network_version
            < EngineNetworkVersionHistory.HISTORY_NETEXPORT_SERIALIZATION
        ):
            field_export.name = archive.read_fstring()
            field_export.type = archive.read_fstring()
        elif (
            archive.engine_network_version
            < EngineNetworkVersionHistory.HISTORY_NETEXPORT_SERIALIZE_FIX
        ):
            field_export.name = archive.read_fstring()
        else:
            field_export.name = archive.read_fname()

        return field_export

    def read_net_field_export_group_map(self, archive: FArchive) -> NetFieldExportGroup:
        """エクスポートグループ全体を読み取る。"""
        group = NetFieldExportGroup(
            path_name=archive.read_fstring(),
            path_name_index=archive.read_int_packed(),
            net_field_exports_length=archive.read_int_packed(),
        )
        group.net_field_exports = [None] * group.net_field_exports_length

        for _ in range(group.net_field_exports_length):
            net_field_export = self.read_net_field_export(archive)
            if net_field_export is None:
                continue
            if group.is_valid_index(net_field_export.handle):
                group.net_field_exports[net_field_export.handle] = net_field_export
            else:
                logger.warning(
                    "不正な NetFieldExport ハンドルです (handle=%s, group=%s, length=%s)",
                    net_field_export.handle,
                    group.path_name,
                    group.net_field_exports_length,
                )
        return group

    def read_net_field_exports(self, archive: FArchive) -> None:
        """フレーム内で追加されたネットフィールドエクスポートを読み取る。"""
        num_layout_cmd_exports = archive.read_int_packed()
        for _ in range(num_layout_cmd_exports):
            path_name_index = archive.read_int_packed()
            is_exported = archive.read_int_packed() == 1

            if is_exported:
                path_name = archive.read_fstring()
                num_exports = archive.read_int_packed()
                group = self.guid_cache.net_field_export_group_map.get(path_name)
                if group is None:
                    group = NetFieldExportGroup(
                        path_name=path_name,
                        path_name_index=path_name_index,
                        net_field_exports_length=num_exports,
                    )
                    self.guid_cache.add_to_export_group_map(path_name, group)
                elif num_exports > group.net_field_exports_length:
                    # 受信するたびにエクスポート数が増えることがある
                    old_exports = group.net_field_exports
                    group.net_field_exports = [None] * num_exports
                    group.net_field_exports[: len(old_exports)] = old_exports
                    group.net_field_exports_length = num_exports
            else:
                group = self.guid_cache.get_net_field_export_group_from_index(path_name_index)

            net_field = self.read_net_field_export(archive)
            if group is not None and net_field is not None:
                if group.is_valid_index(net_field.handle):
                    group.net_field_exports[net_field.handle] = net_field
                else:
                    logger.warning(
                        "不正な NetFieldExport ハンドルです (handle=%s, group=%s, length=%s)",
                        net_field.handle,
                        group.path_name,
                        group.net_field_exports_length,
                    )
            else:
                logger.debug("NetFieldExportGroup が見つかりませんでした。")

    def receive_net_field_exports_compat(self, archive: BitReader) -> None:
        """旧形式のネットフィールドエクスポートを読み取る。"""
        num_layout_cmd_exports = archive.read_uint32()
        for _ in range(num_layout_cmd_exports):
            path_name_index = archive.read_int_packed()
            if archive.read_bit():
                path_name = archive.read_fstring()
                num_exports = archive.read_uint32()
                group = self.guid_cache.net_field_export_group_map.get(path_name)
                if group is None:
                    group = NetFieldExportGroup(
                        path_name=path_name,
                        path_name_index=path_name_index,
                        net_field_exports_length=num_exports,
                    )
                    self.guid_cache.add_to_export_group_map(path_name, group)
            else:
                group = self.guid_cache.get_net_field_export_group_from_index(path_name_index)

            net_field = self.read_net_field_export(archive)
            if group is not None and net_field is not None and group.is_valid_index(net_field.handle):
                group.net_field_exports[net_field.handle] = net_field

    def internal_load_object(
        self, archive: FArchive, is_exporting_net_guid_bunch: bool, recursion_count: int = 0
    ) -> NetworkGUID:
        """NetGUID (と必要ならパス名) を読み取る。"""
        if recursion_count > 16:
            logger.warning("internal_load_object: 再帰の上限に達しました。")
            return NetworkGUID()

        net_guid = NetworkGUID(archive.read_int_packed())
        if not net_guid.is_valid():
            return net_guid

        if net_guid.is_default() or is_exporting_net_guid_bunch:
            flags = archive.read_byte()
            if flags & ExportFlags.bHasPath:
                self.internal_load_object(archive, True, recursion_count + 1)  # outer_guid
                path_name = archive.read_fstring()
                if flags & ExportFlags.bHasNetworkChecksum:
                    archive.read_uint32()  # network_checksum
                if is_exporting_net_guid_bunch:
                    self.guid_cache.net_guid_to_path_name[net_guid.value] = (
                        remove_all_path_prefixes(path_name)
                    )
                return net_guid

        return net_guid

    def receive_net_guid_bunch(self, archive: BitReader) -> None:
        """バンチに含まれる NetGUID を読み取る。"""
        has_rep_layout_export = archive.read_bit()
        if has_rep_layout_export:
            self.receive_net_field_exports_compat(archive)
            return

        num_guids_in_bunch = archive.read_int32()
        if num_guids_in_bunch > MAX_GUID_COUNT:
            logger.warning("NumGUIDsInBunch が上限を超えています: %s", num_guids_in_bunch)
            return

        for _ in range(num_guids_in_bunch):
            self.internal_load_object(archive, True)

    # -- パケット・バンチ ----------------------------------------------------

    def received_raw_packet(self, packet: bytes) -> None:
        """生パケットからビットサイズを求めて解析する。"""
        if not packet:
            raise MalformedPacketException("パケットが空です")

        last_byte = packet[-1]
        if last_byte == 0:
            logger.error("末尾バイトが 0 の不正なパケットです (index=%s)", self._packet_index)
            raise MalformedPacketException("末尾バイトが 0 の不正なパケットです")

        bit_size = (len(packet) * 8) - 1
        # 末尾の終端ビットを探す
        while not (last_byte & 0x80):
            last_byte = (last_byte * 2) & 0xFF
            bit_size -= 1

        self._packet_reader.fill_buffer(packet, bit_size)
        try:
            self.received_packet(self._packet_reader)
        except Exception:  # noqa: BLE001 - 1 パケットの失敗で全体を止めない
            logger.exception("received_packet に失敗しました (index=%s)", self._packet_index)

    def received_packet(self, bit_reader: BitReader) -> None:
        """パケットをバンチへ分解する。"""
        self._in_packet_id += 1

        has_partial_custom_exports_final_bit = (
            bit_reader.engine_network_version >= EngineNetworkVersionHistory.CustomExports
        )

        while not bit_reader.at_end():
            if (
                bit_reader.engine_network_version
                < EngineNetworkVersionHistory.HISTORY_ACKS_INCLUDED_IN_HEADER
            ):
                bit_reader.read_bit()  # is_ack_dummy

            bunch = DataBunch()
            b_control = bit_reader.read_bit()
            bunch.packet_id = self._in_packet_id
            bunch.b_open = b_control and bit_reader.read_bit()
            bunch.b_close = b_control and bit_reader.read_bit()

            if (
                bit_reader.engine_network_version
                < EngineNetworkVersionHistory.HISTORY_CHANNEL_CLOSE_REASON
            ):
                bunch.b_dormant = bunch.b_close and bit_reader.read_bit()
                bunch.close_reason = (
                    ChannelCloseReason.Dormancy if bunch.b_dormant else ChannelCloseReason.Destroyed
                )
            else:
                if bunch.b_close:
                    reason = bit_reader.read_serialized_int(int(ChannelCloseReason.MAX))
                    try:
                        bunch.close_reason = ChannelCloseReason(reason)
                    except ValueError:
                        bunch.close_reason = ChannelCloseReason.Destroyed
                else:
                    bunch.close_reason = ChannelCloseReason.Destroyed
                bunch.b_dormant = bunch.close_reason == ChannelCloseReason.Dormancy

            bunch.b_is_replication_paused = bit_reader.read_bit()
            bunch.b_reliable = bit_reader.read_bit()

            if (
                bit_reader.engine_network_version
                < EngineNetworkVersionHistory.HISTORY_MAX_ACTOR_CHANNELS_CUSTOMIZATION
            ):
                bunch.ch_index = bit_reader.read_serialized_int(OLD_MAX_ACTOR_CHANNELS)
            else:
                bunch.ch_index = bit_reader.read_int_packed()

            bunch.b_has_package_map_exports = bit_reader.read_bit()
            bunch.b_has_must_be_mapped_guids = bit_reader.read_bit()
            bunch.b_partial = bit_reader.read_bit()

            if bunch.b_reliable:
                bunch.ch_sequence = self._in_reliable + 1
            elif bunch.b_partial:
                bunch.ch_sequence = self._in_packet_id
            else:
                bunch.ch_sequence = 0

            bunch.b_partial_initial = bunch.b_partial and bit_reader.read_bit()
            bunch.b_has_partial_custom_exports_final_bit = (
                bit_reader.read_bit()
                if (bunch.b_partial and has_partial_custom_exports_final_bit)
                else False
            )
            bunch.b_partial_final = bunch.b_partial and bit_reader.read_bit()

            if bit_reader.engine_network_version < EngineNetworkVersionHistory.HISTORY_CHANNEL_NAMES:
                bit_reader.read_serialized_int(int(ChannelType.MAX))
            elif bunch.b_reliable or bunch.b_open:
                bit_reader.read_fname()

            bunch.ch_type = ChannelType.NONE
            bunch.ch_name = ChannelName.NONE

            channel_exists = self.channels[bunch.ch_index] is not None
            bunch_data_bits = bit_reader.read_serialized_int(MAX_PACKET_SIZE_IN_BITS)

            if bunch.b_partial:
                partial_archive = BitReader(bit_reader.read_bits(bunch_data_bits), bunch_data_bits)
                partial_archive.engine_network_version = bit_reader.engine_network_version
                partial_archive.network_version = bit_reader.network_version
                partial_archive.replay_header_flags = bit_reader.replay_header_flags
                bunch.archive = partial_archive
            else:
                bit_reader.set_temp_end(bunch_data_bits, ArchiveEndIndex.BUNCH)
                bunch.archive = bit_reader

            if bit_reader.is_error:
                # バンチがパケットの残りより大きいと主張している = ストリームが壊れている。
                # 部分バンチでは read_bits が、そうでなければ set_temp_end が
                # 読み取り位置を進めないまま is_error を立てるため、そのまま続行すると
                # at_end() が真にならず while ループが終わらない。
                # UE も UNetConnection::ReceivedPacket で FInBunch::ResetData 直後に
                # Reader.IsError() を見て、そのパケットごと破棄している
                # (ENetCloseResult::BunchDataOverflow)。
                # see https://github.com/EpicGames/UnrealEngine/blob/release/Engine/Source/Runtime/Engine/Private/NetConnection.cpp
                logger.warning(
                    "バンチ (%s ビット) がパケット %s に収まりません。このパケットを破棄します。",
                    bunch_data_bits,
                    self._packet_index,
                )
                break

            self._bunch_index += 1

            if bunch.b_has_package_map_exports:
                self.receive_net_guid_bunch(bunch.archive)

            if not channel_exists:
                self.channels[bunch.ch_index] = UChannel(channel_index=bunch.ch_index)

            try:
                self.received_raw_bunch(bunch)
            except Exception:  # noqa: BLE001 - 1 バンチの失敗で全体を止めない
                logger.exception("received_raw_bunch に失敗しました (index=%s)", self._bunch_index)
            finally:
                if not bunch.b_partial:
                    bit_reader.restore_temp_end(ArchiveEndIndex.BUNCH)

        if not bit_reader.at_end():
            logger.warning("パケットを最後まで読み取っていません (index=%s)", self._packet_index)

    def received_raw_bunch(self, bunch: DataBunch) -> None:
        """未整列のバンチを処理する。"""
        self.received_next_bunch(bunch)

    def received_next_bunch(self, bunch: DataBunch) -> None:
        """部分バンチの結合を行いつつバンチを処理する。"""
        if bunch.b_reliable:
            self._in_reliable = bunch.ch_sequence

        if bunch.b_partial:
            if bunch.b_partial_initial:
                if self._partial_bunch is not None:
                    if not self._partial_bunch.b_partial_final and self._partial_bunch.b_reliable:
                        if bunch.b_reliable:
                            logger.warning("信頼できる部分バンチが別の部分バンチを破棄しました")
                            return
                        logger.warning("信頼できない部分バンチが別の部分バンチを破棄しました")
                        return
                    self._partial_bunch = None

                self._partial_bunch = DataBunch(bunch)
                bits_left = bunch.archive.get_bits_left()
                if not bunch.b_has_package_map_exports and bits_left > 0:
                    if bits_left % 8 != 0:
                        logger.warning(
                            "部分バンチが壊れています。先頭の部分バンチはバイト境界である必要があります。"
                        )
                        return
                else:
                    logger.debug("NetGUID のみを含む部分バンチを受信しました。")
                return

            sequence_matches = False
            if self._partial_bunch is not None:
                reliable_sequences_matches = bunch.ch_sequence == self._partial_bunch.ch_sequence + 1
                unreliable_sequence_matches = reliable_sequences_matches or (
                    bunch.ch_sequence == self._partial_bunch.ch_sequence
                )
                sequence_matches = (
                    reliable_sequences_matches
                    if self._partial_bunch.b_reliable
                    else unreliable_sequence_matches
                )

            if (
                self._partial_bunch is not None
                and not self._partial_bunch.b_partial_final
                and sequence_matches
                and self._partial_bunch.b_reliable == bunch.b_reliable
            ):
                bits_left = bunch.archive.get_bits_left()
                logger.debug("部分バンチを結合します: %s ビット", bits_left)
                if not bunch.b_has_package_map_exports and bits_left > 0:
                    self._partial_bunch.archive.append_data_from_checked(
                        bunch.archive.read_bits(bits_left), bits_left
                    )

                if (
                    not bunch.b_has_package_map_exports
                    and not bunch.b_partial_final
                    and (bits_left % 8 != 0)
                ):
                    logger.warning(
                        "部分バンチが壊れています。最終以外の部分バンチはバイト境界である必要があります。"
                    )
                    return

                self._partial_bunch.ch_sequence = bunch.ch_sequence

                if bunch.b_partial_final:
                    logger.debug("部分バンチの結合が完了しました。")
                    if bunch.b_has_package_map_exports:
                        logger.warning("最終部分バンチにパッケージマップエクスポートがあります。")
                        return
                    self._partial_bunch.b_partial_final = True
                    self._partial_bunch.b_close = bunch.b_close
                    self._partial_bunch.b_dormant = bunch.b_dormant
                    self._partial_bunch.close_reason = bunch.close_reason
                    self._partial_bunch.b_is_replication_paused = bunch.b_is_replication_paused
                    self._partial_bunch.b_has_must_be_mapped_guids = (
                        bunch.b_has_must_be_mapped_guids
                    )
                    self.received_sequenced_bunch(self._partial_bunch)
                return

            logger.warning("部分バンチの結合に失敗しました。")
            return

        self.received_sequenced_bunch(bunch)

    def received_sequenced_bunch(self, bunch: DataBunch) -> bool:
        """整列済みバンチを処理する。"""
        self.received_actor_bunch(bunch)

        if bunch.b_close:
            channel = self.channels[bunch.ch_index]
            actor_guid = None
            if channel is not None and channel.actor is not None:
                actor_guid = channel.actor.actor_net_guid
            self.channels[bunch.ch_index] = None
            self.on_channel_closed(bunch.ch_index, actor_guid)
            return True
        return False

    def received_actor_bunch(self, bunch: DataBunch) -> None:
        """アクター向けバンチを処理する。"""
        if bunch.b_has_must_be_mapped_guids:
            num_must_be_mapped_guids = bunch.archive.read_uint16()
            for _ in range(num_must_be_mapped_guids):
                bunch.archive.read_int_packed()

        self.process_bunch(bunch)

    def conditionally_serialize_quantized_vector(
        self, archive: BitReader, default_vector: FVector
    ) -> FVector:
        """存在する場合のみ量子化ベクトルを読み取る。"""
        was_serialized = archive.read_bit()
        if not was_serialized:
            return default_vector
        should_quantize = (
            archive.engine_network_version
            < EngineNetworkVersionHistory.HISTORY_OPTIONALLY_QUANTIZE_SPAWN_INFO
        ) or archive.read_bit()
        return archive.read_packed_vector(10, 24) if should_quantize else archive.read_fvector()

    def process_bunch(self, bunch: DataBunch) -> None:
        """バンチの内容 (アクター生成・プロパティ) を処理する。"""
        channel = self.channels[bunch.ch_index]

        if channel is not None and channel.actor is None:
            if not bunch.b_open:
                logger.warning("新規アクターチャンネルが open ビット無しで届きました。")
                return

            in_actor = Actor(actor_net_guid=self.internal_load_object(bunch.archive, False))

            if bunch.archive.at_end() and in_actor.actor_net_guid.is_dynamic():
                return

            if in_actor.actor_net_guid.is_dynamic():
                in_actor.archetype = self.internal_load_object(bunch.archive, False)
                if (
                    bunch.archive.engine_network_version
                    >= EngineNetworkVersionHistory.HISTORY_NEW_ACTOR_OVERRIDE_LEVEL
                ):
                    in_actor.level = self.internal_load_object(bunch.archive, False)

                in_actor.location = self.conditionally_serialize_quantized_vector(
                    bunch.archive, FVector(0, 0, 0)
                )
                if bunch.archive.read_bit():
                    in_actor.rotation = bunch.archive.read_rotation_short()
                else:
                    in_actor.rotation = FRotator(0, 0, 0)
                in_actor.scale = self.conditionally_serialize_quantized_vector(
                    bunch.archive, FVector(1, 1, 1)
                )
                in_actor.velocity = self.conditionally_serialize_quantized_vector(
                    bunch.archive, FVector(0, 0, 0)
                )

            channel.actor = in_actor
            self.on_channel_opened(channel.channel_index, in_actor.actor_net_guid)

            path = self.guid_cache.try_get_path_name(channel.archetype_id or 0)
            if path is not None and path in self.net_field_parser.player_controller_groups:
                self.read_player_controller_header(bunch.archive)

        while not bunch.archive.at_end():
            rep_object, object_deleted, has_rep_layout, payload = self.read_content_block_payload(
                bunch
            )

            if bunch.archive.is_error:
                # コンテンツブロックがずれている場合、アーカイブは is_error を立てたまま
                # 読み取り位置が終端に届かない (エラー後の読み取りは何もしない) ため、
                # 下の ``payload is None`` の continue に落ちると while ループが終わらない。
                # UE の UActorChannel::ProcessBunch も ReadContentBlockPayload の直後に
                # Bunch.IsError() を見てバンチの処理を打ち切る。
                # see https://github.com/EpicGames/UnrealEngine/blob/release/Engine/Source/Runtime/Engine/Private/DataChannel.cpp
                logger.warning(
                    "read_content_block_payload でエラーが発生しました。バンチ %s を打ち切ります。",
                    self._bunch_index,
                )
                break

            if payload is None:
                continue

            bunch.archive.set_temp_end(payload, ArchiveEndIndex.CONTENT_BLOCK_PAYLOAD)
            try:
                if object_deleted:
                    continue
                if bunch.archive.is_error:
                    logger.warning(
                        "read_content_block_payload に失敗しました (bunch=%s)", self._bunch_index
                    )
                    break
                if rep_object is None or bunch.archive.at_end():
                    continue
                if not self.received_replicator_bunch(
                    bunch, bunch.archive, rep_object, has_rep_layout
                ):
                    logger.debug("received_replicator_bunch が False を返しました")
                    continue
            finally:
                bunch.archive.restore_temp_end(ArchiveEndIndex.CONTENT_BLOCK_PAYLOAD)

    def read_player_controller_header(self, archive: BitReader) -> None:
        """プレイヤーコントローラーのチャンネルが開かれたときの追加情報を読み取る。

        ``APlayerController::OnActorChannelOpen`` に対応する。
        エンジンバージョン 41 で ``ClientHandshakeId``、43 で
        ``LocalPlayerConnectionIdentifier`` が追加された。

        see https://github.com/EpicGames/UnrealEngine/blob/release/Engine/Source/Runtime/Engine/Private/PlayerController.cpp
        """
        archive.read_byte()  # NetPlayerIndex
        if archive.engine_network_version >= EngineNetworkVersionHistory.ClientHandshakeId:
            archive.read_uint32()  # ClientHandshakeId
        if archive.engine_network_version >= EngineNetworkVersionHistory.CloseChildConnection:
            archive.read_int32()  # LocalPlayerConnectionIdentifier

    def received_replicator_bunch(
        self, bunch: DataBunch, archive: BitReader, rep_object: int | None, has_rep_layout: bool
    ) -> bool:
        """コンテンツブロック内のプロパティを読み取る。"""
        net_field_export_group = self.guid_cache.get_net_field_export_group(rep_object)
        if net_field_export_group is None:
            return True

        if has_rep_layout:
            ok, _ = self.receive_properties(archive, net_field_export_group, bunch.ch_index)
            if not ok:
                return False
            self.receive_external_data(net_field_export_group, bunch.ch_index)

        if archive.at_end():
            return True

        class_net_cache = self.guid_cache.try_get_class_net_cache(
            net_field_export_group.path_name,
            bunch.archive.engine_network_version
            >= EngineNetworkVersionHistory.HISTORY_CLASSNETCACHE_FULLNAME,
        )
        if class_net_cache is None:
            logger.debug("ClassNetCache が見つかりません: %s", net_field_export_group.path_name)
            return False

        while True:
            has_more, field_cache, payload = self.read_field_header_and_payload(
                archive, class_net_cache
            )
            if not has_more:
                break
            if payload is None:
                continue

            archive.set_temp_end(payload, ArchiveEndIndex.FIELD_HEADER_PAYLOAD)
            try:
                if field_cache is None:
                    logger.debug("FieldCache が None です: %s", class_net_cache.path_name)
                    continue
                if field_cache.incompatible:
                    logger.debug("互換性のないフィールドです: %s", field_cache.name)
                    continue
                if archive.is_error or archive.at_end():
                    continue
                if not self.net_field_parser.will_read_class_net_cache(class_net_cache.path_name):
                    continue

                class_net_property = self.net_field_parser.try_get_class_net_cache_property(
                    field_cache.name, class_net_cache.path_name
                )
                if class_net_property is None:
                    logger.debug(
                        "未知の構造体を読み飛ばします (%s / %s)",
                        class_net_cache.path_name,
                        field_cache.name,
                    )
                    continue

                if class_net_property.is_function:
                    function_group = self.guid_cache.get_net_field_export_group_by_path(
                        class_net_property.path_name
                    )
                    if not self.received_rpc(archive, function_group, bunch.ch_index):
                        return False
                elif class_net_property.is_custom_struct:
                    if not self.receive_custom_property(
                        archive, class_net_cache, field_cache, bunch.ch_index
                    ):
                        logger.warning(
                            "カスタムプロパティの解析に失敗しました (%s / %s)",
                            class_net_cache.path_name,
                            field_cache.name,
                        )
                        continue
                else:
                    group = self.guid_cache.get_net_field_export_group_by_path(
                        class_net_property.path_name
                    )
                    if group is None or not self.net_field_parser.will_read_type(group.path_name):
                        continue
                    if not self.receive_custom_delta_property(
                        archive,
                        group,
                        bunch.ch_index,
                        class_net_property.enable_property_checksum,
                    ):
                        logger.warning(
                            "カスタムデルタプロパティの解析に失敗しました: %s", field_cache.name
                        )
                        continue
            finally:
                archive.restore_temp_end(ArchiveEndIndex.FIELD_HEADER_PAYLOAD)

        return True

    def receive_external_data(self, group: NetFieldExportGroup, channel_index: int) -> bool:
        """アクターに紐づく外部データを取り出して通知する。"""
        channel = self.channels[channel_index]
        if channel is None:
            logger.error("チャンネルが見つかりません: %s", channel_index)
            return False
        if channel.is_ignoring_group(group.path_name):
            return False

        external_data = self.guid_cache.try_get_external_data(channel.actor_id)
        if external_data is not None:
            self.on_external_data_read(channel_index, external_data)
        return True

    def received_rpc(
        self, reader: BitReader, net_field_export_group: NetFieldExportGroup | None, channel_index: int
    ) -> bool:
        """RPC のプロパティを読み取る。"""
        if net_field_export_group is None:
            logger.warning("received_rpc: エクスポートグループがありません")
            return False

        self.receive_properties(reader, net_field_export_group, channel_index)

        if reader.is_error:
            logger.warning("received_rpc: 読み取りエラー (bunch=%s)", self._bunch_index)
            return False

        channel = self.channels[channel_index]
        if (
            channel is not None
            and not channel.is_ignoring_group(net_field_export_group.path_name)
            and self.net_field_parser.will_read_type(net_field_export_group.path_name)
            and not reader.at_end()
        ):
            logger.warning("received_rpc: 読み取りビット数が一致しません (bunch=%s)", self._bunch_index)
            return False
        return True

    def receive_custom_property(
        self,
        reader: BitReader,
        class_net_cache: NetFieldExportGroup,
        field_cache: NetFieldExport,
        channel_index: int,
    ) -> bool:
        """カスタム構造体プロパティを読み取る。"""
        export = self.net_field_parser.create_property_type(
            class_net_cache.path_name, field_cache.name
        )
        if export is None:
            return False

        num_bits = reader.get_bits_left()
        self._cmd_reader.fill_buffer(reader.read_bits(num_bits), num_bits)
        export.serialize(self._cmd_reader)

        if self._cmd_reader.is_error:
            logger.warning(
                "カスタムプロパティ %s の読み取りでエラーが発生しました (bits=%s)",
                field_cache.name,
                self._cmd_reader.last_bit,
            )
        if not self._cmd_reader.at_end():
            logger.warning(
                "カスタムプロパティ %s のビット数が一致しません (%s / %s)",
                field_cache.name,
                self._cmd_reader.last_bit - self._cmd_reader.get_bits_left(),
                self._cmd_reader.last_bit,
            )

        resolve = getattr(export, "resolve", None)
        if callable(resolve):
            resolve(self.guid_cache)
        self.on_export_read(channel_index, export)
        return True

    def receive_custom_delta_property(
        self,
        reader: BitReader,
        group: NetFieldExportGroup,
        channel_index: int,
        enable_property_checksum: bool,
    ) -> bool:
        """FastArray の差分プロパティを読み取る。"""
        if (
            reader.engine_network_version
            >= EngineNetworkVersionHistory.HISTORY_FAST_ARRAY_DELTA_STRUCT
        ):
            reader.read_bit()  # bSupportsFastArrayDeltaStructSerialization

        return self.net_delta_serialize(reader, group, channel_index, enable_property_checksum)

    def net_delta_serialize_header(self, reader: BitReader) -> FFastArraySerializerHeader:
        """FastArraySerializer のヘッダーを読み取る。"""
        return FFastArraySerializerHeader(
            array_replication_key=reader.read_int32(),
            base_replication_key=reader.read_int32(),
            num_deletes=reader.read_int32(),
            num_changed=reader.read_int32(),
        )

    def net_delta_serialize(
        self,
        reader: BitReader,
        group: NetFieldExportGroup,
        channel_index: int,
        enable_property_checksum: bool,
    ) -> bool:
        """FastArray の削除・変更要素を読み取る。"""
        header = self.net_delta_serialize_header(reader)
        if reader.is_error:
            return False

        for _ in range(header.num_deletes):
            element_index = reader.read_int32()
            self.on_net_delta_read(
                channel_index,
                NetDeltaUpdate(
                    element_index=element_index,
                    export=None,
                    deleted=True,
                    channel_index=channel_index,
                ),
            )

        for _ in range(header.num_changed):
            element_index = reader.read_int32()
            _, export = self.receive_properties(
                reader,
                group,
                channel_index,
                enable_property_checksum=not enable_property_checksum,
                net_delta_update=True,
            )
            self.on_net_delta_read(
                channel_index,
                NetDeltaUpdate(
                    element_index=element_index,
                    export=export,
                    deleted=True,
                    channel_index=channel_index,
                ),
            )

        return True

    def receive_properties(
        self,
        archive: BitReader,
        group: NetFieldExportGroup,
        channel_index: int,
        enable_property_checksum: bool = True,
        net_delta_update: bool = False,
    ) -> tuple[bool, Any]:
        """ハンドル付きのプロパティ列を読み取る。

        戻り値は ``(成功したか, 生成されたエクスポートオブジェクト)``。
        """
        channel = self.channels[channel_index]
        if channel is None:
            logger.error("チャンネルが見つかりません: %s", channel_index)
            return False, None

        if channel.is_ignoring_group(group.path_name):
            return False, None

        if not self.net_field_parser.will_read_type(group.path_name):
            logger.debug("解析対象外の型です: %s", group.path_name)
            channel.ignore_group(group.path_name)
            return False, None

        if enable_property_checksum:
            archive.read_bit()  # do_checksum

        export_group = self.net_field_parser.create_type(group.path_name)
        if export_group is None:
            logger.warning("エクスポートグループを生成できません: %s", group.path_name)
            return False, None

        has_data = False
        while True:
            handle = archive.read_int_packed()
            if handle == 0:
                break

            # 0 を終端に使うため保存時に 1 加算されている
            handle -= 1

            if not group.is_valid_index(handle):
                logger.warning(
                    "ハンドルが範囲外です (group=%s, length=%s, handle=%s)",
                    group.path_name,
                    group.net_field_exports_length,
                    handle,
                )
                return False, None

            export = group.net_field_exports[handle]
            num_bits = archive.read_int_packed()
            if num_bits == 0:
                continue

            if export is None:
                logger.debug(
                    "ハンドル %s (group=%s) が見つかりません。%s ビットを読み飛ばします。",
                    handle,
                    group.path_name,
                    num_bits,
                )
                archive.skip_bits(num_bits)
                continue

            if export.incompatible:
                archive.skip_bits(num_bits)
                continue

            has_data = True
            try:
                self._cmd_reader.fill_buffer(archive.read_bits(num_bits), num_bits)
                if not self.net_field_parser.read_field(
                    export_group, export, handle, group, self._cmd_reader
                ):
                    export.incompatible = True
                if self._cmd_reader.is_error:
                    logger.debug(
                        "プロパティ %s (handle=%s, path=%s) の読み取りでエラーが発生しました",
                        export.name,
                        handle,
                        group.path_name,
                    )
                    export.incompatible = True
                    continue
                if not self._cmd_reader.at_end():
                    logger.debug(
                        "プロパティ %s (handle=%s, path=%s) のビット数が一致しません",
                        export.name,
                        handle,
                        group.path_name,
                    )
                    export.incompatible = True
                    continue
            except Exception:  # noqa: BLE001 - 1 プロパティの失敗で全体を止めない
                logger.exception(
                    "プロパティ %s (path=%s) の解析中に例外が発生しました",
                    export.name,
                    group.path_name,
                )

        if not net_delta_update and has_data:
            self.on_export_read(channel_index, export_group)

        return True, export_group

    def read_field_header_and_payload(
        self, archive: BitReader, group: NetFieldExportGroup
    ) -> tuple[bool, NetFieldExport | None, int | None]:
        """フィールドヘッダーとペイロードのビット数を読み取る。"""
        if archive.at_end():
            return False, None, None

        net_field_export_handle = archive.read_serialized_int(
            max(group.net_field_exports_length, 2)
        )
        if archive.is_error:
            logger.warning("NetFieldExportHandle の読み取りに失敗しました。")
            return False, None, None

        out_field = (
            group.net_field_exports[net_field_export_handle]
            if group.is_valid_index(net_field_export_handle)
            else None
        )
        payload = archive.read_int_packed()
        if archive.is_error:
            logger.warning("ペイロードのビット数の読み取りに失敗しました。")
            return False, None, None

        if not archive.can_read(payload):
            return False, out_field, None

        return True, out_field, payload

    def read_content_block_payload(
        self, bunch: DataBunch
    ) -> tuple[int | None, bool, bool, int | None]:
        """コンテンツブロックのヘッダーとペイロード長を読み取る。

        戻り値は ``(オブジェクト, 削除されたか, RepLayout を持つか, ペイロード長)``。
        """
        rep_object, has_rep_layout, object_deleted = self.read_content_block_header(bunch)
        if object_deleted:
            return rep_object, object_deleted, has_rep_layout, None
        payload = bunch.archive.read_int_packed()
        return rep_object, object_deleted, has_rep_layout, payload

    def read_content_block_header(self, bunch: DataBunch) -> tuple[int | None, bool, bool]:
        """コンテンツブロックのヘッダーを読み取る。"""
        object_deleted = False
        has_rep_layout = bunch.archive.read_bit()
        is_actor = bunch.archive.read_bit()

        channel = self.channels[bunch.ch_index]
        if is_actor:
            if channel is None:
                return None, has_rep_layout, object_deleted
            return (channel.archetype_id or channel.actor_id), has_rep_layout, object_deleted

        net_guid = self.internal_load_object(bunch.archive, False)
        stably_named = bunch.archive.read_bit()
        if stably_named:
            return net_guid.value, has_rep_layout, object_deleted

        delete_sub_object = False
        serialize_class = True

        if (
            bunch.archive.engine_network_version
            >= EngineNetworkVersionHistory.HISTORY_SUBOBJECT_DESTROY_FLAG
        ):
            is_destroy_message = bunch.archive.read_bit()
            if is_destroy_message:
                delete_sub_object = True
                serialize_class = False
                bunch.archive.read_byte()  # destroy_flags

        class_net_guid = NetworkGUID()
        if serialize_class:
            class_net_guid = self.internal_load_object(bunch.archive, False)
            delete_sub_object = not class_net_guid.is_valid()

        if delete_sub_object:
            object_deleted = True
            return None, has_rep_layout, object_deleted

        if (
            bunch.archive.engine_network_version
            >= EngineNetworkVersionHistory.HISTORY_SUBOBJECT_OUTER_CHAIN
        ):
            actor_is_outer = bunch.archive.at_end() or bunch.archive.read_bit()
            if not actor_is_outer:
                self.internal_load_object(bunch.archive, False)  # outer_object

        return class_net_guid.value, has_rep_layout, object_deleted

    # -- 拡張ポイント -------------------------------------------------------

    def on_export_read(self, channel_index: int, export_group: Any) -> None:
        """プロパティ群を読み終えたときに呼ばれる。"""

    def on_external_data_read(self, channel_index: int, external_data: Any) -> None:
        """外部データを読み終えたときに呼ばれる。"""

    def on_net_delta_read(self, channel_index: int, update: NetDeltaUpdate) -> None:
        """FastArray の差分を読み終えたときに呼ばれる。"""

    def on_channel_opened(self, channel_index: int, actor: NetworkGUID | None) -> None:
        """チャンネルが開かれたときに呼ばれる。"""

    def on_channel_closed(self, channel_index: int, actor: NetworkGUID | None) -> None:
        """チャンネルが閉じられたときに呼ばれる。"""

    # -- 復号・展開 ---------------------------------------------------------

    def decrypt_buffer(self, archive: FArchive, size: int) -> FArchive:
        """暗号化されたチャンクを復号する。"""
        if not self.replay.info.is_encrypted:
            return archive
        raise NotImplementedError(
            "暗号化されたリプレイです。decrypt_buffer を実装してください。"
        )

    def decompress(self, archive: FArchive) -> FArchive:
        """圧縮されたチャンクを展開する。"""
        if not self.replay.info.is_compressed:
            return archive
        raise NotImplementedError(
            "圧縮されたリプレイです。decompress を実装してください。"
        )


def _from_dotnet_binary(value: int) -> Any:
    """.NET の ``DateTime.FromBinary`` 相当の変換を行う。"""
    from datetime import datetime, timedelta

    ticks = value & _TICKS_MASK
    try:
        return datetime(1, 1, 1) + timedelta(microseconds=ticks // 10)
    except (OverflowError, ValueError):
        return None
