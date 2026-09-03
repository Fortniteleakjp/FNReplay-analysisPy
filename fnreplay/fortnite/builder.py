"""受信したエクスポートから解析結果を組み立てるビルダー。

C# 版の ``FortniteReplayBuilder`` に対応する。
"""

from __future__ import annotations

from typing import Any

from .exports.handwritten import PlayerNameData, PlaylistInfo
from .models import (
    BattleBus,
    Cosmetics,
    FortniteReplay,
    GameData,
    Inventory,
    InventoryItem,
    KillFeedEntry,
    Llama,
    MapData,
    PlayerData,
    PlayerMovement,
    RebootVan,
    SafeZone,
    SupplyDrop,
    TeamData,
    WeaponData,
)


def _name_of(value: Any) -> str | None:
    """``ItemDefinition`` や ``FName`` から名前を取り出す。"""
    if value is None:
        return None
    return getattr(value, "name", None)


def _names_of(values: Any) -> list[str] | None:
    """名前を持つオブジェクトのリストを名前のリストに変換する。"""
    if values is None:
        return None
    return [_name_of(v) for v in values if v is not None]


class FortniteReplayBuilder:
    """チャンネルごとの更新を受け取り、リプレイ全体の情報にまとめる。"""

    def __init__(self) -> None:
        self.game_data = GameData()
        self.map_data = MapData()
        self.kill_feed: list[KillFeedEntry] = []

        self._actor_to_channel: dict[int, int] = {}
        self._channel_to_actor: dict[int, int] = {}
        self._pawn_channel_to_state_channel: dict[int, int] = {}
        self._queued_player_pawns: dict[int, list[tuple[int, Any]]] = {}
        self._only_spectating_players: set[int] = set()
        self._players: dict[int, PlayerData] = {}
        self._teams: dict[int, TeamData] = {}
        self._llamas: dict[int, Llama] = {}
        self._reboot_vans: dict[int, RebootVan] = {}
        self._drops: dict[int, SupplyDrop] = {}
        self._inventories: dict[int, Inventory] = {}
        self._weapons: dict[int, WeaponData] = {}
        self._unknown_weapons: dict[int, WeaponData] = {}

        self.replicated_world_time_seconds: float | None = 0.0
        self.replicated_world_time_seconds_double: float | None = 0.0

    # -- チャンネル管理 -----------------------------------------------------

    def add_actor_channel(self, channel_index: int, guid: int) -> None:
        """アクターとチャンネルの対応を登録する。"""
        self._actor_to_channel[guid] = channel_index
        self._channel_to_actor[channel_index] = guid

    def remove_channel(self, channel_index: int) -> None:
        """チャンネルが閉じられたときの後始末。"""
        self._weapons.pop(channel_index, None)
        self._unknown_weapons.pop(channel_index, None)

    def build(self, replay: FortniteReplay) -> FortniteReplay:
        """収集した情報をリプレイオブジェクトに反映する。"""
        self.update_team_data()
        replay.game_data = self.game_data
        replay.map_data = self.map_data
        replay.kill_feed = self.kill_feed
        replay.team_data = list(self._teams.values())
        replay.player_data = list(self._players.values())
        return replay

    # -- 内部ヘルパー -------------------------------------------------------

    def _try_get_player_data_from_actor(self, guid: int) -> PlayerData | None:
        pawn_channel = self._actor_to_channel.get(guid)
        if pawn_channel is None:
            return None
        state_channel = self._pawn_channel_to_state_channel.get(pawn_channel)
        if state_channel is None:
            return None
        return self._players.get(state_channel)

    def _try_get_player_data_from_pawn(self, pawn: int) -> PlayerData | None:
        state_channel = self._pawn_channel_to_state_channel.get(pawn)
        if state_channel is None:
            return None
        return self._players.get(state_channel)

    def _handle_queued_player_pawns(self, state_channel_index: int) -> None:
        actor_id = self._channel_to_actor.get(state_channel_index)
        if actor_id is None:
            return
        queued = self._queued_player_pawns.pop(actor_id, None)
        if not queued:
            return
        for channel_id, player_pawn in queued:
            self.update_player_pawn(channel_id, player_pawn)

    # -- ゲーム全体 ---------------------------------------------------------

    def update_game_state(self, state: Any) -> None:
        """ゲームステートの更新を反映する。"""
        data = self.game_data
        if data.game_session_id is None:
            data.game_session_id = state.game_session_id
        if data.utc_time_started_match is None and state.utc_time_started_match is not None:
            data.utc_time_started_match = state.utc_time_started_match.time
        if data.match_end_time is None:
            data.match_end_time = state.end_game_start_time
        if data.map_info is None:
            data.map_info = _name_of(state.map_info)
        if data.is_large_team_game is None:
            data.is_large_team_game = state.b_is_large_team_game
        if data.tournament_round is None:
            data.tournament_round = state.event_tournament_round
        if not data.additional_playlist_levels and state.additional_playlist_levels_streamed:
            data.additional_playlist_levels = _names_of(
                state.additional_playlist_levels_streamed
            ) or []
        if data.max_players is None:
            data.max_players = state.team_count
        if data.team_size is None:
            data.team_size = state.team_size
        if data.team_size is None and state.active_team_nums is not None:
            data.team_size = len(state.active_team_nums)
        if state.player_bots_left is not None and (
            data.total_bots is None or state.player_bots_left > data.total_bots
        ):
            data.total_bots = state.player_bots_left
        if data.total_player_structures is None:
            data.total_player_structures = state.total_player_structures
        if data.aircraft_start_time is None:
            data.aircraft_start_time = state.aircraft_start_time
        if data.safe_zones_start_time is None:
            data.safe_zones_start_time = state.safe_zones_start_time

        if not self.map_data.battle_bus_flight_paths and state.team_flight_paths:
            skin = _name_of(state.default_battle_bus)
            self.map_data.battle_bus_flight_paths = [
                BattleBus(
                    aircraft_index=aircraft.aircraft_index,
                    skin=skin,
                    flight_start_location=aircraft.flight_start_location,
                    flight_start_rotation=aircraft.flight_start_rotation,
                    flight_speed=aircraft.flight_speed,
                    time_till_flight_end=aircraft.time_till_flight_end,
                    time_till_drop_start=aircraft.time_till_drop_start,
                    time_till_drop_end=aircraft.time_till_drop_end,
                    replicated_flight_timestamp=aircraft.replicated_flight_timestamp,
                )
                for aircraft in state.team_flight_paths
                if aircraft is not None
            ]

        if state.replicated_world_time_seconds is not None:
            self.replicated_world_time_seconds = state.replicated_world_time_seconds
        if state.replicated_world_time_seconds_double is not None:
            self.replicated_world_time_seconds_double = state.replicated_world_time_seconds_double

        if not data.winning_player_ids and state.winning_player_list:
            data.winning_player_ids = [i for i in state.winning_player_list if i is not None]
        if data.winning_team is None:
            data.winning_team = state.winning_team
        if data.recorder_id is None and state.recorder_player_state is not None:
            data.recorder_id = getattr(
                state.recorder_player_state, "value", state.recorder_player_state
            )

    def update_playlist_info(self, playlist: PlaylistInfo) -> None:
        """プレイリスト名を反映する。"""
        if self.game_data.current_playlist is None:
            self.game_data.current_playlist = playlist.name

    def update_gameplay_modifiers(self, modifier: Any) -> None:
        """有効なゲームプレイ修飾子を追加する。"""
        name = _name_of(modifier.modifier_def)
        if name is not None:
            self.game_data.active_gameplay_modifiers.append(name)

    def update_poi_manager(self, poi_manager: Any) -> None:
        """マップのグリッド情報を反映する。"""
        data = self.map_data
        if data.grid_count_x is None:
            data.grid_count_x = poi_manager.grid_count_x
        if data.grid_count_y is None:
            data.grid_count_y = poi_manager.grid_count_y
        if data.world_grid_start is None:
            data.world_grid_start = poi_manager.world_grid_start
        if data.world_grid_end is None:
            data.world_grid_end = poi_manager.world_grid_end
        if data.world_grid_spacing is None:
            data.world_grid_spacing = poi_manager.world_grid_spacing
        if data.world_grid_total_size is None:
            data.world_grid_total_size = poi_manager.world_grid_total_size

    # -- プレイヤー ---------------------------------------------------------

    def update_private_name(self, channel_index: int, name_data: PlayerNameData) -> None:
        """外部データから得たプレイヤー名を反映する。"""
        player = self._players.get(channel_index)
        if player is not None:
            player.player_name = name_data.decoded_name

    def update_team_data(self) -> None:
        """プレイヤー情報からチーム情報を組み立てる。"""
        for player in self._players.values():
            if player.team_index is None:
                continue

            team = self._teams.get(player.team_index)
            if team is None:
                self._teams[player.team_index] = TeamData(
                    team_index=player.team_index,
                    player_ids=[player.id],
                    player_names=[player.player_name or player.player_id],
                    placement=player.placement,
                    party_owner_id=player.id if player.is_party_leader else None,
                    team_kills=player.team_kills,
                )
                continue

            if team.placement is None:
                team.placement = player.placement
            if team.team_kills is None:
                team.team_kills = player.team_kills
            team.player_ids.append(player.id)
            team.player_names.append(player.player_name or player.player_id)
            if player.is_party_leader:
                team.party_owner_id = player.id

    def _create_player_data(self, state: Any) -> PlayerData:
        """プレイヤーステートから ``PlayerData`` を作る。"""
        epic_id = state.unique_id or state.unique_id_legacy
        player = PlayerData(
            id=state.player_id_legacy if state.player_id is None else int(state.player_id),
            epic_id=epic_id,
            bot_id=state.bot_unique_id,
            is_bot=state.b_is_a_bot is True,
            player_name_custom_override=getattr(state.player_name_custom_override, "text", None),
            is_game_session_owner=state.b_is_game_session_owner,
            player_number=(
                int(state.world_player_id) if state.world_player_id is not None else None
            ),
            streamer_mode_name=getattr(state.streamer_mode_name, "text", None),
            is_party_leader=(
                state.party_owner_unique_id is not None
                and state.party_owner_unique_id in (state.unique_id, state.unique_id_legacy)
            ),
            team_index=state.team_index,
            level=state.level,
            season_level_ui_display=state.season_level_ui_display,
            platform_unique_net_id=state.platform_unique_net_id,
            platform=state.platform,
            has_finished_loading=state.b_has_finished_loading,
            has_started_playing=state.b_has_started_playing,
            is_using_anonymous_mode=state.b_using_anonymous_mode,
            is_using_streamer_mode=state.b_using_streamer_mode,
            cosmetics=Cosmetics(
                character_body_type=state.character_body_type,
                hero_type=_name_of(state.hero_type),
                character_gender=state.character_gender,
            ),
        )
        return player

    def update_player_state(self, channel_index: int, state: Any) -> None:
        """プレイヤーステートの更新を反映する。"""
        if state.b_only_spectator is True:
            self._only_spectating_players.add(channel_index)
            return
        if channel_index in self._only_spectating_players:
            return

        player = self._players.get(channel_index)
        is_new_player = player is None
        if player is None:
            player = self._create_player_data(state)
            actor_id = self._channel_to_actor.get(channel_index)
            if actor_id is not None and actor_id == self.game_data.recorder_id:
                player.is_replay_owner = True
            self._players[channel_index] = player

        if state.reboot_counter and state.reboot_counter > (player.reboot_counter or 0):
            player.reboot_counter = state.reboot_counter

        if (
            (state.reboot_counter or 0) > 0
            or state.b_dbno is not None
            or state.death_cause is not None
            or state.death_location is not None
        ):
            self.update_kill_feed(channel_index, player, state)

        if state.team_index is not None and state.team_index > 0:
            player.team_index = state.team_index

        if player.placement is None:
            player.placement = state.place
        player.team_kills = (
            state.team_kill_score if state.team_kill_score is not None else player.team_kills
        )
        player.kills = state.kill_score if state.kill_score is not None else player.kills
        if player.has_thanked_bus_driver is None:
            player.has_thanked_bus_driver = state.b_thanked_bus_driver
        if player.disconnected is None:
            player.disconnected = state.b_is_disconnected
        if player.death_cause is None:
            player.death_cause = state.death_cause
        if player.death_location is None:
            player.death_location = state.death_location
        if player.death_circumstance is None:
            player.death_circumstance = state.death_circumstance
        if not player.death_tags and state.death_tags is not None:
            player.death_tags = [tag.tag_name for tag in state.death_tags.tags]

        if state.death_tags is not None:
            player.death_time = self.replicated_world_time_seconds
            player.death_time_double = self.replicated_world_time_seconds_double

        if player.cosmetics.parts is None:
            player.cosmetics.parts = _name_of(state.parts)
        if not player.cosmetics.variant_required_character_parts:
            names = _names_of(state.variant_required_character_parts)
            if names:
                player.cosmetics.variant_required_character_parts = names

        if is_new_player:
            self._handle_queued_player_pawns(channel_index)

    def update_kill_feed(self, channel_index: int, data: PlayerData, state: Any) -> None:
        """キルフィードに 1 行追加する。"""
        entry = KillFeedEntry(
            replicated_world_time_seconds=self.replicated_world_time_seconds,
            replicated_world_time_seconds_double=self.replicated_world_time_seconds_double,
        )

        if state.reboot_counter is not None:
            entry.is_revived = True
        if state.b_dbno is True:
            entry.is_downed = True

        actor_channel_index = self._actor_to_channel.get(state.finisher_or_downer or 0)
        if actor_channel_index is not None:
            finisher = self._players.get(actor_channel_index)
            if finisher is not None:
                entry.finisher_or_downer = finisher.id
                entry.finisher_or_downer_name = finisher.player_id
                entry.finisher_or_downer_is_bot = finisher.is_bot

        entry.player_id = data.id
        entry.player_name = data.player_id
        entry.player_is_bot = data.is_bot
        entry.distance = state.distance
        entry.death_cause = state.death_cause
        entry.death_location = state.death_location
        entry.death_circumstance = state.death_circumstance
        if state.death_tags is not None:
            entry.death_tags = [tag.tag_name for tag in state.death_tags.tags]

        self.kill_feed.append(entry)

    def update_player_pawn(self, channel_index: int, pawn: Any) -> None:
        """プレイヤーポーンの更新を反映する。"""
        if pawn.player_state is not None:
            # PlayerState を受信するたびに対応表を更新する
            actor_id = pawn.player_state
            state_channel_index = self._actor_to_channel.get(actor_id)
            if state_channel_index is None:
                # まだ PlayerState のチャンネルが判らないので保留する
                self._queued_player_pawns.setdefault(actor_id, []).append((channel_index, pawn))
                return
            self._pawn_channel_to_state_channel[channel_index] = state_channel_index
            player = self._players.get(state_channel_index)
            if player is None:
                return
        else:
            player = self._try_get_player_data_from_pawn(channel_index)
            if player is None:
                return

        cosmetics = player.cosmetics
        if cosmetics.character is None:
            cosmetics.character = _name_of(pawn.character)
        if cosmetics.banner_color_id is None:
            cosmetics.banner_color_id = pawn.banner_color_id
        if cosmetics.banner_icon_id is None:
            cosmetics.banner_icon_id = pawn.banner_icon_id
        if cosmetics.is_default_character is None:
            cosmetics.is_default_character = pawn.b_is_default_character
        if cosmetics.backpack is None:
            cosmetics.backpack = _name_of(pawn.backpack)
        if cosmetics.pet_skin is None:
            cosmetics.pet_skin = _name_of(pawn.pet_skin)
        if cosmetics.glider is None:
            cosmetics.glider = _name_of(pawn.glider)
        if cosmetics.loading_screen is None:
            cosmetics.loading_screen = _name_of(pawn.loading_screen)
        if cosmetics.music_pack is None:
            cosmetics.music_pack = _name_of(pawn.music_pack)
        if cosmetics.pickaxe is None:
            cosmetics.pickaxe = _name_of(pawn.pickaxe)
        if cosmetics.sky_dive_contrail is None:
            cosmetics.sky_dive_contrail = _name_of(pawn.sky_dive_contrail)
        if not cosmetics.dances:
            cosmetics.dances = _names_of(pawn.dances) or []
        if not cosmetics.item_wraps:
            cosmetics.item_wraps = _names_of(pawn.item_wraps) or []

        if pawn.current_weapon is not None:
            player.current_weapon = pawn.current_weapon

        if pawn.replicated_movement is not None:
            player.locations.append(
                PlayerMovement(
                    replicated_movement=pawn.replicated_movement,
                    replicated_world_time_seconds=self.replicated_world_time_seconds,
                    replicated_world_time_seconds_double=(
                        self.replicated_world_time_seconds_double
                    ),
                    last_update_time=pawn.replay_last_transform_update_time_stamp,
                    b_is_crouched=pawn.b_is_crouched,
                    b_is_in_any_storm=pawn.b_is_in_any_storm,
                    b_is_ziplining=pawn.b_is_ziplining,
                    b_is_targeting=pawn.b_is_targeting,
                    b_is_honking=pawn.b_is_honking,
                    b_is_jumping=pawn.b_is_jumping,
                    b_is_playing_emote=pawn.b_is_playing_emote,
                    b_is_sprinting=pawn.b_is_sprinting,
                    b_is_waiting_for_emote_interaction=pawn.b_is_waiting_for_emote_interaction,
                    b_is_slope_sliding=pawn.b_is_slope_sliding,
                    b_is_skydiving=pawn.b_is_skydiving,
                    b_is_skydiving_from_launch_pad=pawn.b_is_skydiving_from_launch_pad,
                    b_is_skydiving_from_bus=pawn.b_is_skydiving_from_bus,
                    b_is_parachute_open=pawn.b_is_parachute_open,
                    b_is_parachute_forced_open=pawn.b_is_parachute_forced_open,
                    b_is_dbno=pawn.b_is_dbno,
                    b_is_in_water_volume=pawn.b_is_in_water_volume,
                )
            )

    # -- インベントリ・武器 --------------------------------------------------

    def update_inventory(self, channel_index: int, fort_inventory: Any) -> None:
        """インベントリの更新を反映する。"""
        inventory = self._inventories.get(channel_index)
        if inventory is None:
            if fort_inventory.replay_pawn is None:
                return
            inventory = Inventory(id=channel_index, replay_pawn=fort_inventory.replay_pawn)
            self._inventories[channel_index] = inventory

        if fort_inventory.replay_pawn is not None and fort_inventory.replay_pawn > 0:
            inventory.replay_pawn = fort_inventory.replay_pawn

        if inventory.player_id is None:
            player = self._try_get_player_data_from_actor(inventory.replay_pawn or 0)
            if player is not None:
                inventory.player_id = player.id
                inventory.player_name = player.player_id
                player.inventory_id = inventory.id

        if fort_inventory.a is None:
            return

        inventory.items.append(
            InventoryItem(
                count=fort_inventory.count,
                item_definition=_name_of(fort_inventory.item_definition),
                order_index=fort_inventory.order_index,
                durability=fort_inventory.durability,
                level=fort_inventory.level,
                loaded_ammo=fort_inventory.loaded_ammo,
                a=fort_inventory.a,
                b=fort_inventory.b,
                c=fort_inventory.c,
                d=fort_inventory.d,
            )
        )

    def update_weapon(self, channel_index: int, weapon: Any) -> None:
        """武器の状態を反映する。"""
        new_weapon = self._weapons.get(channel_index)
        if new_weapon is None:
            new_weapon = self._unknown_weapons.pop(channel_index, None)
            if new_weapon is None:
                new_weapon = WeaponData()
            self._weapons[channel_index] = new_weapon

        if new_weapon.b_is_equipping_weapon is None:
            new_weapon.b_is_equipping_weapon = weapon.b_is_equipping_weapon
        if new_weapon.b_is_reloading_weapon is None:
            new_weapon.b_is_reloading_weapon = weapon.b_is_reloading_weapon
        if new_weapon.weapon_level is None:
            new_weapon.weapon_level = weapon.weapon_level
        if new_weapon.ammo_count is None:
            new_weapon.ammo_count = weapon.ammo_count
        if new_weapon.last_fire_time_verified is None:
            new_weapon.last_fire_time_verified = weapon.last_fire_time_verified
        if new_weapon.a is None:
            new_weapon.a = weapon.a
        if new_weapon.b is None:
            new_weapon.b = weapon.b
        if new_weapon.c is None:
            new_weapon.c = weapon.c
        if new_weapon.d is None:
            new_weapon.d = weapon.d
        if new_weapon.weapon_name is None:
            new_weapon.weapon_name = _name_of(weapon.weapon_data)

    # -- マップ上のオブジェクト ----------------------------------------------

    def update_safe_zones(self, safe_zone: Any) -> None:
        """安全地帯の更新を追加する。"""
        start = safe_zone.safe_zone_start_shrink_time or 0
        finish = safe_zone.safe_zone_finish_shrink_time or 0
        if start <= 0 and finish <= 0:
            return

        self.map_data.safe_zones.append(
            SafeZone(
                radius=safe_zone.radius,
                start_shrink_time=safe_zone.safe_zone_start_shrink_time,
                finish_shrink_time=safe_zone.safe_zone_finish_shrink_time,
                last_radius=safe_zone.last_radius,
                last_center=safe_zone.last_center,
                next_radius=safe_zone.next_radius,
                next_center=safe_zone.next_center,
                next_next_radius=safe_zone.next_next_radius,
                next_next_center=safe_zone.next_next_center,
            )
        )

    def update_llama(self, channel_index: int, supply_drop_llama: Any) -> None:
        """サプライラマの更新を反映する。"""
        llama = self._llamas.get(channel_index)
        if llama is None:
            movement = supply_drop_llama.replicated_movement
            llama = Llama(
                id=channel_index,
                looted=bool(supply_drop_llama.looted),
                landing_location=supply_drop_llama.final_destination,
                location=movement.location if movement is not None else None,
                has_spawned_pickups=bool(supply_drop_llama.b_has_spawned_pickups),
            )
            self.map_data.llamas.append(llama)
            self._llamas[channel_index] = llama
            return

        if llama.landing_location is None:
            llama.landing_location = supply_drop_llama.final_destination
        if supply_drop_llama.looted:
            llama.looted = True
            llama.looted_time = self.replicated_world_time_seconds
            llama.looted_time_double = self.replicated_world_time_seconds_double
        if supply_drop_llama.b_has_spawned_pickups:
            llama.has_spawned_pickups = True

    def update_supply_drop(self, channel_index: int, supply_drop: Any) -> None:
        """サプライドロップの更新を反映する。"""
        drop = self._drops.get(channel_index)
        if drop is None:
            drop = SupplyDrop(
                id=channel_index,
                fall_height=supply_drop.fall_height,
                fall_speed=supply_drop.fall_speed,
            )
            self.map_data.supply_drops.append(drop)
            self._drops[channel_index] = drop
            return

        if supply_drop.opened:
            drop.looted = True
            drop.looted_time = self.replicated_world_time_seconds
            drop.looted_time_double = self.replicated_world_time_seconds_double
        if supply_drop.balloon_popped:
            drop.balloon_popped = True
            drop.balloon_popped_time = self.replicated_world_time_seconds
            drop.balloon_popped_time_double = self.replicated_world_time_seconds_double
        if supply_drop.b_has_spawned_pickups:
            drop.has_spawned_pickups = True
        if supply_drop.landing_location is not None:
            drop.landing_location = supply_drop.landing_location

    def update_reboot_van(self, channel_index: int, spawn_machine: Any) -> None:
        """リブートバンの更新を反映する。"""
        handle = spawn_machine.spawn_machine_rep_data_handle
        if handle in self._reboot_vans:
            return

        reboot_van = RebootVan(
            id=handle,
            location=spawn_machine.location,
            spawn_machine_state=spawn_machine.spawn_machine_state,
            spawn_machine_cooldown_start_time=spawn_machine.spawn_machine_cooldown_start_time,
            spawn_machine_cooldown_end_time=spawn_machine.spawn_machine_cooldown_end_time,
        )
        self.map_data.reboot_vans.append(reboot_van)
        self._reboot_vans[handle] = reboot_van
