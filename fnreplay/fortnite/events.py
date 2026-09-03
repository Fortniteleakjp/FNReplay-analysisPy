"""リプレイのイベントチャンクから読み取るデータ。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

from ..unreal.models import EventInfo, FQuat, FVector


class PlayerTypes(IntEnum):
    """撃破イベントに含まれるプレイヤー種別。"""

    BOT = 0x03
    NAMED_BOT = 0x10
    PLAYER = 0x11


class ReplayEventTypes:
    """イベントのグループ名・メタデータ名。"""

    PLAYER_ELIMINATION = "playerElim"
    MATCH_STATS = "AthenaMatchStats"
    TEAM_STATS = "AthenaMatchTeamStats"
    ENCRYPTION_KEY = "PlayerStateEncryptionKey"
    CHARACTER_SAMPLE = "CharacterSampleMeta"
    ZONE_UPDATE = "ZoneUpdate"
    BATTLE_BUS = "BattleBusFlight"


@dataclass
class BaseEvent:
    """イベント共通の情報。"""

    info: EventInfo | None = None


@dataclass
class EncryptionKey(BaseEvent):
    """プレイヤーステートの暗号鍵。"""

    key: str = ""


@dataclass
class PlayerEliminationInfo:
    """撃破イベントに含まれる 1 人分の情報。"""

    id: str | None = None
    player_type: PlayerTypes | int | None = None
    rotation: FQuat | None = None
    location: FVector | None = None
    scale: FVector | None = None

    @property
    def is_bot(self) -> bool:
        """ボットかどうか。"""
        return self.player_type in (PlayerTypes.BOT, PlayerTypes.NAMED_BOT)


@dataclass
class PlayerElimination(BaseEvent):
    """撃破イベント。"""

    eliminated_info: PlayerEliminationInfo = field(default_factory=PlayerEliminationInfo)
    eliminator_info: PlayerEliminationInfo = field(default_factory=PlayerEliminationInfo)
    gun_type: int = 0
    time: str = ""
    knocked: bool = False

    @property
    def eliminated(self) -> str | None:
        """倒されたプレイヤーの ID。"""
        return self.eliminated_info.id if self.eliminated_info else None

    @property
    def eliminator(self) -> str | None:
        """倒したプレイヤーの ID。"""
        return self.eliminator_info.id if self.eliminator_info else None

    @property
    def is_self_elimination(self) -> bool:
        """自滅かどうか。"""
        return self.eliminated == self.eliminator

    @property
    def is_valid_location(self) -> bool:
        """位置情報が有効かどうか。"""
        location = self.eliminator_info.location
        return location is not None and location.size() != 0

    @property
    def distance(self) -> float | None:
        """撃破時の距離。位置情報が無い場合は None。"""
        if not self.is_valid_location or self.eliminated_info.location is None:
            return None
        return self.eliminator_info.location.distance_to(self.eliminated_info.location)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlayerElimination):
            return NotImplemented
        return (
            self.eliminated == other.eliminated
            and self.eliminator == other.eliminator
            and self.gun_type == other.gun_type
            and self.time == other.time
            and self.knocked == other.knocked
        )

    def __hash__(self) -> int:
        return hash((self.eliminated, self.eliminator, self.gun_type, self.time, self.knocked))


@dataclass
class Stats(BaseEvent):
    """試合の統計 (リプレイ所有者のもの)。"""

    unknown: int = 0
    accuracy: float = 0.0
    assists: int = 0
    eliminations: int = 0
    weapon_damage: int = 0
    other_damage: int = 0
    revives: int = 0
    damage_taken: int = 0
    damage_to_structures: int = 0
    materials_gathered: int = 0
    materials_used: int = 0
    total_traveled: int = 0

    @property
    def damage_to_players(self) -> int:
        """プレイヤーに与えたダメージの合計。"""
        return self.weapon_damage + self.other_damage


@dataclass
class TeamStats(BaseEvent):
    """チームの統計。"""

    unknown: int = 0
    position: int = 0
    total_players: int = 0
