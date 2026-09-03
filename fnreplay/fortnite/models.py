"""解析結果として組み立てられる Fortnite のデータモデル。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..unreal.models import FRepMovement, FRotator, FVector, FVector2D, Replay
from .events import PlayerElimination, Stats, TeamStats


@dataclass
class Cosmetics:
    """プレイヤーの外見設定。"""

    character_gender: int | None = None
    character_body_type: int | None = None
    parts: str | None = None
    variant_required_character_parts: list[str] = field(default_factory=list)
    hero_type: str | None = None
    banner_icon_id: str | None = None
    banner_color_id: str | None = None
    item_wraps: list[str] = field(default_factory=list)
    sky_dive_contrail: str | None = None
    glider: str | None = None
    pickaxe: str | None = None
    is_default_character: bool | None = None
    character: str | None = None
    backpack: str | None = None
    loading_screen: str | None = None
    dances: list[str] = field(default_factory=list)
    music_pack: str | None = None
    pet_skin: str | None = None


@dataclass
class PlayerMovement:
    """ある時点でのプレイヤーの状態。"""

    replicated_movement: FRepMovement | None = None
    replicated_world_time_seconds: float | None = None
    replicated_world_time_seconds_double: float | None = None
    last_update_time: float | None = None
    b_is_crouched: bool | None = None
    b_is_sprinting: bool | None = None
    b_is_jumping: bool | None = None
    b_is_slope_sliding: bool | None = None
    b_is_ziplining: bool | None = None
    b_is_targeting: bool | None = None
    b_is_dbno: bool | None = None
    b_is_honking: bool | None = None
    b_is_in_any_storm: bool | None = None
    b_is_waiting_for_emote_interaction: bool | None = None
    b_is_playing_emote: bool | None = None
    b_is_skydiving: bool | None = None
    b_is_skydiving_from_launch_pad: bool | None = None
    b_is_skydiving_from_bus: bool | None = None
    b_is_parachute_open: bool | None = None
    b_is_parachute_forced_open: bool | None = None
    b_is_in_water_volume: bool | None = None


@dataclass
class PlayerData:
    """1 プレイヤー分の情報。"""

    id: int | None = None
    epic_id: str | None = None
    platform_unique_net_id: str | None = None
    bot_id: str | None = None
    is_bot: bool = False
    player_name: str | None = None
    player_name_custom_override: str | None = None
    streamer_mode_name: str | None = None
    platform: str | None = None
    level: int | None = None
    season_level_ui_display: int | None = None
    inventory_id: int | None = None
    player_number: int | None = None
    team_index: int | None = None
    is_party_leader: bool = False
    is_replay_owner: bool = False
    is_game_session_owner: bool | None = None
    has_finished_loading: bool | None = None
    has_started_playing: bool | None = None
    has_thanked_bus_driver: bool | None = None
    is_using_streamer_mode: bool | None = None
    is_using_anonymous_mode: bool | None = None
    disconnected: bool | None = None
    reboot_counter: int | None = None
    placement: int | None = None
    kills: int | None = None
    team_kills: int | None = None
    death_cause: int | None = None
    death_circumstance: int | None = None
    death_tags: list[str] = field(default_factory=list)
    death_location: FVector | None = None
    death_time: float | None = None
    death_time_double: float | None = None
    cosmetics: Cosmetics = field(default_factory=Cosmetics)
    current_weapon: int | None = None
    locations: list[PlayerMovement] = field(default_factory=list)

    @property
    def player_id(self) -> str | None:
        """ボットなら bot_id、そうでなければ Epic ID (無ければプラットフォーム ID)。"""
        if self.is_bot:
            return self.bot_id
        return self.epic_id or self.platform_unique_net_id


@dataclass
class TeamData:
    """チーム単位の情報。"""

    team_index: int | None = None
    player_ids: list[int | None] = field(default_factory=list)
    player_names: list[str | None] = field(default_factory=list)
    party_owner_id: int | None = None
    placement: int | None = None
    team_kills: int | None = None


@dataclass
class GameData:
    """試合全体の情報。"""

    game_session_id: str | None = None
    utc_time_started_match: datetime | None = None
    match_end_time: float | None = None
    map_info: str | None = None
    current_playlist: str | None = None
    additional_playlist_levels: list[str] = field(default_factory=list)
    active_gameplay_modifiers: list[str] = field(default_factory=list)
    recorder_id: int | None = None
    max_players: int | None = None
    total_teams: int | None = None
    total_bots: int | None = None
    team_size: int | None = None
    total_player_structures: int | None = None
    tournament_round: int | None = None
    is_large_team_game: bool | None = None
    aircraft_start_time: float | None = None
    safe_zones_start_time: float | None = None
    winning_team: int | None = None
    winning_player_ids: list[int] = field(default_factory=list)

    @property
    def is_tournament_round(self) -> bool:
        """トーナメントかどうか。"""
        return bool(self.tournament_round and self.tournament_round > 0)


@dataclass
class KillFeedEntry:
    """キルフィードの 1 行。"""

    player_id: int | None = None
    player_name: str | None = None
    player_is_bot: bool = False
    finisher_or_downer: int | None = None
    finisher_or_downer_name: str | None = None
    finisher_or_downer_is_bot: bool = False
    replicated_world_time_seconds: float | None = None
    replicated_world_time_seconds_double: float | None = None
    distance: float | None = None
    death_cause: int | None = None
    death_location: FVector | None = None
    death_circumstance: int | None = None
    death_tags: list[str] = field(default_factory=list)
    is_downed: bool = False
    is_revived: bool = False


@dataclass
class BattleBus:
    """バトルバスの飛行経路。"""

    aircraft_index: int | None = None
    skin: str | None = None
    flight_start_location: FVector | None = None
    flight_start_rotation: FRotator | None = None
    flight_speed: float | None = None
    time_till_flight_end: float | None = None
    time_till_drop_start: float | None = None
    time_till_drop_end: float | None = None
    replicated_flight_timestamp: float | None = None


@dataclass
class SafeZone:
    """ストームの安全地帯。"""

    radius: float | None = None
    start_shrink_time: float | None = None
    finish_shrink_time: float | None = None
    last_radius: float | None = None
    last_center: FVector | None = None
    next_radius: float | None = None
    next_center: FVector | None = None
    next_next_radius: float | None = None
    next_next_center: FVector | None = None


@dataclass
class Llama:
    """サプライラマ。"""

    id: int = 0
    location: FVector | None = None
    has_spawned_pickups: bool = False
    looted: bool = False
    looted_time: float | None = None
    looted_time_double: float | None = None
    landing_location: FVector | None = None


@dataclass
class SupplyDrop:
    """サプライドロップ。"""

    id: int = 0
    has_spawned_pickups: bool = False
    looted: bool = False
    looted_time: float | None = None
    looted_time_double: float | None = None
    balloon_popped: bool = False
    balloon_popped_time: float | None = None
    balloon_popped_time_double: float | None = None
    fall_speed: float | None = None
    landing_location: FVector | None = None
    fall_height: float | None = None


@dataclass
class RebootVan:
    """リブートバン。"""

    id: int = 0
    location: FVector | None = None
    spawn_machine_state: int | None = None
    spawn_machine_cooldown_start_time: float | None = None
    spawn_machine_cooldown_end_time: float | None = None


@dataclass
class MapData:
    """マップ上のオブジェクト。"""

    battle_bus_flight_paths: list[BattleBus] = field(default_factory=list)
    safe_zones: list[SafeZone] = field(default_factory=list)
    llamas: list[Llama] = field(default_factory=list)
    supply_drops: list[SupplyDrop] = field(default_factory=list)
    reboot_vans: list[RebootVan] = field(default_factory=list)
    world_grid_start: FVector2D | None = None
    world_grid_end: FVector2D | None = None
    world_grid_spacing: FVector2D | None = None
    grid_count_x: int | None = None
    grid_count_y: int | None = None
    world_grid_total_size: FVector2D | None = None


@dataclass
class WeaponData:
    """武器の状態。"""

    b_is_equipping_weapon: bool | None = None
    b_is_reloading_weapon: bool | None = None
    weapon_name: str | None = None
    last_fire_time_verified: float | None = None
    weapon_level: int | None = None
    ammo_count: int | None = None
    a: int | None = None
    b: int | None = None
    c: int | None = None
    d: int | None = None


@dataclass
class InventoryItem:
    """インベントリの 1 アイテム。"""

    count: int | None = None
    item_definition: str | None = None
    order_index: int | None = None
    durability: float | None = None
    level: int | None = None
    loaded_ammo: int | None = None
    a: int | None = None
    b: int | None = None
    c: int | None = None
    d: int | None = None


@dataclass
class Inventory:
    """プレイヤーのインベントリ。"""

    id: int | None = None
    replay_pawn: int | None = None
    player_id: int | None = None
    player_name: str | None = None
    items: list[InventoryItem] = field(default_factory=list)


@dataclass
class FortniteReplay(Replay):
    """Fortnite のリプレイ解析結果。"""

    eliminations: list[PlayerElimination] = field(default_factory=list)
    stats: Stats | None = None
    team_stats: TeamStats | None = None
    game_data: GameData = field(default_factory=GameData)
    team_data: list[TeamData] = field(default_factory=list)
    player_data: list[PlayerData] = field(default_factory=list)
    kill_feed: list[KillFeedEntry] = field(default_factory=list)
    map_data: MapData = field(default_factory=MapData)
    encryption_keys: list[Any] = field(default_factory=list)
