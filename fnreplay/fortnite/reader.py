"""Fortnite のリプレイ (.replay) を解析するリーダー。

C# 版の ``FortniteReplayReader.ReplayReader`` に対応する。
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import IO, Any

from .. import crypto
from ..compression import decompress_replay_data
from ..unreal.archives import BinaryReader, FArchive
from ..unreal.enums import ParseMode
from ..unreal.exceptions import PlayerEliminationException, UnknownEventException
from ..unreal.export_registry import REGISTRY, ExportRegistry
from ..unreal.models import EventInfo, ExternalData, NetDeltaUpdate, NetworkGUID
from ..unreal.replay_reader import ReplayReader as BaseReplayReader
from . import exports  # noqa: F401  エクスポート定義を登録するために読み込む
from .builder import FortniteReplayBuilder
from .events import (
    EncryptionKey,
    PlayerElimination,
    PlayerEliminationInfo,
    PlayerTypes,
    ReplayEventTypes,
    Stats,
    TeamStats,
)
from .exports.generated import (
    ActiveGameplayModifier,
    BaseWeapon,
    FortPlayerState,
    FortPoiManager,
    GameState,
    PlayerPawn,
    SafeZoneIndicator,
    SpawnMachineRepData,
    SupplyDrop,
    SupplyDropLlama,
)
from .exports.handwritten import PlayerNameData, PlaylistInfo
from .models import FortniteReplay

logger = logging.getLogger(__name__)

_BRANCH_RE = re.compile(r"\+\+Fortnite\+Release\-(?P<major>\d+)\.(?P<minor>\d*)")


def milliseconds_to_timestamp(milliseconds: int) -> str:
    """ミリ秒を ``分:秒`` の文字列にする。"""
    total_seconds = milliseconds // 1000
    return f"{(total_seconds // 60) % 60:02d}:{total_seconds % 60:02d}"


class FortniteReplayReader(BaseReplayReader):
    """Fortnite のリプレイを解析する。"""

    replay_factory = FortniteReplay

    def __init__(
        self,
        parse_mode: ParseMode = ParseMode.Minimal,
        registry: ExportRegistry = REGISTRY,
    ) -> None:
        super().__init__(parse_mode, registry)
        self.builder = FortniteReplayBuilder()
        self.major = 0
        self.minor = 0
        self._branch = ""

    # -- エントリポイント ---------------------------------------------------

    def read_replay_file(self, path: str | Path) -> FortniteReplay:
        """リプレイファイルを読み込んで解析する。"""
        with open(path, "rb") as stream:
            return self.read_replay_stream(stream)

    def read_replay_stream(self, stream: IO[bytes]) -> FortniteReplay:
        """ストリームから読み込んで解析する。"""
        return self.read_replay_bytes(stream.read())

    def read_replay_bytes(self, data: bytes) -> FortniteReplay:
        """バイト列を解析する。"""
        archive = BinaryReader(data)
        self.builder = FortniteReplayBuilder()
        replay = self.read_replay(archive)
        return self.builder.build(replay)

    @property
    def branch(self) -> str:
        """リプレイを記録したブランチ名。"""
        return self._branch

    @branch.setter
    def branch(self, value: str) -> None:
        match = _BRANCH_RE.match(value or "")
        if match:
            self.major = int(match.group("major") or 0)
            self.minor = int(match.group("minor") or 0)
        self._branch = value

    def read_replay_header(self, archive: FArchive) -> None:
        super().read_replay_header(archive)
        self.branch = self.replay.header.branch

    # -- コールバック -------------------------------------------------------

    def on_channel_opened(self, channel_index: int, actor: NetworkGUID | None) -> None:
        if actor is not None:
            self.builder.add_actor_channel(channel_index, actor.value)

    def on_channel_closed(self, channel_index: int, actor: NetworkGUID | None) -> None:
        if actor is not None:
            self.builder.remove_channel(channel_index)

    def on_net_delta_read(self, channel_index: int, update: NetDeltaUpdate) -> None:
        export = update.export
        if isinstance(export, ActiveGameplayModifier):
            self.builder.update_gameplay_modifiers(export)
        elif isinstance(export, SpawnMachineRepData):
            self.builder.update_reboot_van(channel_index, export)

    def on_export_read(self, channel_index: int, export_group: Any) -> None:
        if isinstance(export_group, GameState):
            self.builder.update_game_state(export_group)
        elif isinstance(export_group, PlaylistInfo):
            self.builder.update_playlist_info(export_group)
        elif isinstance(export_group, FortPlayerState):
            self.builder.update_player_state(channel_index, export_group)
        elif isinstance(export_group, PlayerPawn):
            self.builder.update_player_pawn(channel_index, export_group)
        elif isinstance(export_group, SafeZoneIndicator):
            self.builder.update_safe_zones(export_group)
        elif isinstance(export_group, SupplyDropLlama):
            self.builder.update_llama(channel_index, export_group)
        elif isinstance(export_group, SupplyDrop):
            self.builder.update_supply_drop(channel_index, export_group)
        elif isinstance(export_group, FortPoiManager):
            self.builder.update_poi_manager(export_group)
        elif isinstance(export_group, BaseWeapon):
            self.builder.update_weapon(channel_index, export_group)

    def on_external_data_read(self, channel_index: int, external_data: Any) -> None:
        if external_data is None or not isinstance(external_data, ExternalData):
            return
        try:
            self.builder.update_private_name(
                channel_index, PlayerNameData(external_data.archive)
            )
        except (IndexError, ValueError, UnicodeDecodeError):
            logger.debug("外部データの解析に失敗しました (channel=%s)", channel_index)

    # -- イベント -----------------------------------------------------------

    def read_event(self, archive: FArchive) -> None:
        """イベントチャンクを解析する。"""
        info = EventInfo(
            id=archive.read_fstring(),
            group=archive.read_fstring(),
            metadata=archive.read_fstring(),
            start_time=archive.read_uint32(),
            end_time=archive.read_uint32(),
            size_in_bytes=archive.read_int32(),
        )
        logger.debug(
            "イベント %s (%s) を検出しました (start=%s, size=%s)",
            info.group,
            info.metadata,
            info.start_time,
            info.size_in_bytes,
        )

        decrypted = self.decrypt_buffer(archive, info.size_in_bytes)

        if info.group == ReplayEventTypes.PLAYER_ELIMINATION:
            self.replay.eliminations.append(self.parse_elimination(decrypted, info))
            return
        if info.metadata == ReplayEventTypes.MATCH_STATS:
            self.replay.stats = self.parse_match_stats(decrypted, info)
            return
        if info.metadata == ReplayEventTypes.TEAM_STATS:
            self.replay.team_stats = self.parse_team_stats(decrypted, info)
            return
        if info.metadata == ReplayEventTypes.ENCRYPTION_KEY:
            self.replay.encryption_keys.append(
                self.parse_encryption_key_event(decrypted, info)
            )
            return

        logger.debug(
            "未知のイベント %s (%s) size=%s", info.group, info.metadata, info.size_in_bytes
        )
        if self.is_debug_mode:
            raise UnknownEventException(
                f"未知のイベント {info.group} ({info.metadata}) size={info.size_in_bytes}"
            )

    def parse_encryption_key_event(self, archive: FArchive, info: EventInfo) -> EncryptionKey:
        """暗号鍵イベントを解析する。"""
        return EncryptionKey(info=info, key=archive.read_bytes_to_string(32))

    def parse_team_stats(self, archive: FArchive, info: EventInfo) -> TeamStats:
        """チーム統計イベントを解析する。"""
        return TeamStats(
            info=info,
            unknown=archive.read_uint32(),
            position=archive.read_uint32(),
            total_players=archive.read_uint32(),
        )

    def parse_match_stats(self, archive: FArchive, info: EventInfo) -> Stats:
        """試合統計イベントを解析する。"""
        return Stats(
            info=info,
            unknown=archive.read_uint32(),
            accuracy=archive.read_single(),
            assists=archive.read_uint32(),
            eliminations=archive.read_uint32(),
            weapon_damage=archive.read_uint32(),
            other_damage=archive.read_uint32(),
            revives=archive.read_uint32(),
            damage_taken=archive.read_uint32(),
            damage_to_structures=archive.read_uint32(),
            materials_gathered=archive.read_uint32(),
            materials_used=archive.read_uint32(),
            total_traveled=archive.read_uint32(),
        )

    def parse_elimination(self, archive: FArchive, info: EventInfo) -> PlayerElimination:
        """撃破イベントを解析する。"""
        try:
            elimination = PlayerElimination(info=info)
            version = archive.read_int32()

            # エンジンバージョン 34 以降は transform が倍精度 (UE5 の LWC) になる。
            # 本家 C# は float として読んだ上で 80 バイト読み飛ばしているが、
            # ここでは実際の値として解析する (消費するバイト数は同じ)。
            use_double_transform = version >= 6 and int(archive.engine_network_version) >= 34

            if version >= 3:
                archive.skip_bytes(1)  # 用途不明
                if use_double_transform:
                    self.parse_transform(archive, elimination.eliminated_info, True)
                    self.parse_transform(archive, elimination.eliminator_info, True)
                else:
                    if version >= 6:
                        self.parse_transform(archive, elimination.eliminated_info, False)
                    self.parse_transform(archive, elimination.eliminator_info, False)
                    if int(archive.engine_network_version) >= 34:
                        archive.skip_bytes(80)
            else:
                if self.major <= 4 and self.minor < 2:
                    # バージョン int を含めて 12 バイト。常に 0
                    archive.skip_bytes(8)
                elif self.major == 4 and self.minor <= 2:
                    archive.skip_bytes(36)

                if int(archive.engine_network_version) >= 34:
                    archive.skip_bytes(80)

            self.parse_player(archive, elimination.eliminated_info, version)
            self.parse_player(archive, elimination.eliminator_info, version)

            elimination.gun_type = archive.read_byte()
            elimination.knocked = archive.read_uint32_as_boolean()
            elimination.time = milliseconds_to_timestamp(info.start_time)
            return elimination
        except Exception as error:  # noqa: BLE001 - 呼び出し側に文脈を伝える
            logger.error("撃破イベントの解析に失敗しました (start_time=%s)", info.start_time)
            raise PlayerEliminationException(
                f"撃破イベントの解析に失敗しました (start_time={info.start_time})"
            ) from error

    def parse_transform(
        self, archive: FArchive, info: PlayerEliminationInfo, use_double: bool
    ) -> None:
        """撃破イベントに含まれる位置・回転・スケールを読み取る。"""
        if use_double:
            info.rotation = archive.read_fquat_double()
            info.location = archive.read_fvector_double()
            info.scale = archive.read_fvector_double()
        else:
            info.rotation = archive.read_fquat()
            info.location = archive.read_fvector()
            info.scale = archive.read_fvector()

    def parse_player(self, archive: FArchive, info: PlayerEliminationInfo, version: int) -> None:
        """撃破イベント内のプレイヤー情報を解析する。"""
        if version < 6:
            info.id = archive.read_fstring()
            return

        player_type = archive.read_byte()
        try:
            info.player_type = PlayerTypes(player_type)
        except ValueError:
            info.player_type = player_type

        if info.player_type == PlayerTypes.BOT:
            info.id = "Bot"
        elif info.player_type == PlayerTypes.NAMED_BOT:
            info.id = archive.read_fstring()
        elif info.player_type == PlayerTypes.PLAYER:
            info.id = archive.read_guid(archive.read_byte())
        else:
            info.id = ""

    # -- 復号・展開 ---------------------------------------------------------

    def decrypt_buffer(self, archive: FArchive, size: int) -> FArchive:
        """暗号化されたチャンクを復号する。"""
        if not self.replay.info.is_encrypted:
            reader = BinaryReader(archive.read_bytes(size))
            reader.engine_network_version = self.replay.header.engine_network_version
            reader.network_version = self.replay.header.network_version
            reader.replay_header_flags = self.replay.header.flags
            reader.replay_version = self.replay.info.file_version
            return reader

        encrypted = archive.read_bytes(size)
        decrypted = crypto.aes_ecb_decrypt(self.replay.info.encryption_key, encrypted)
        reader = BinaryReader(decrypted)
        reader.copy_version_from(archive)
        return reader

    def decompress(self, archive: FArchive) -> FArchive:
        """Oodle で圧縮されたチャンクを展開する。"""
        if not self.replay.info.is_compressed:
            return archive

        decompressed_size = archive.read_int32()
        compressed_size = archive.read_int32()
        compressed = archive.read_bytes(compressed_size)
        logger.debug("チャンクを展開します (%s -> %s)", compressed_size, decompressed_size)

        output = decompress_replay_data(bytes(compressed), decompressed_size)
        reader = BinaryReader(output)
        reader.copy_version_from(archive)
        return reader


def read_replay(
    path: str | Path, parse_mode: ParseMode = ParseMode.Minimal
) -> FortniteReplay:
    """リプレイファイルを解析して結果を返す簡易 API。

    Args:
        path: ``.replay`` ファイルのパス。
        parse_mode: 解析の深さ。既定は ``ParseMode.Minimal``。
    """
    return FortniteReplayReader(parse_mode=parse_mode).read_replay_file(path)
