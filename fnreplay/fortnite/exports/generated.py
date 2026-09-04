"""Fortnite のネットフィールドエクスポート定義。

このファイルは ``tools/gen_exports.py`` により
Shiqan/FortniteReplayDecompressor の C# 定義から生成されている。
手で編集せず、ジェネレーターを更新すること。
"""

# ruff: noqa: E501
from __future__ import annotations

from ...unreal.enums import ParseMode, RepLayoutCmdType
from ...unreal.export_registry import (
    ExportGroup,
    RepMovementSpec,
    class_net_cache,
    export_group,
    export_subgroup,
    field,
    handle_field,
    player_controller,
    rpc,
)
from ...unreal.enums import RotatorQuantization, VectorQuantization
from ...unreal.models import (
    ActorGuid,
    FDateTime,
    FGameplayAbilityRepAnimMontage,
    FGameplayCueParameters,
    FGameplayEffectContextHandle,
    FGameplayTag,
    FGameplayTagContainer,
    FHitResult,
    FName,
    FPredictionKey,
    FQuat,
    FStaticName,
    FText,
    ItemDefinition,
    NetworkGUID,
)
from .handwritten import (
    DebuggingObject,
    FAthenaPawnReplayData,
    FQuantizedBuildingAttribute,
    PlaylistInfo,
)


@export_group("/Script/FortniteGame.ActiveGameplayModifier", ParseMode.Minimal)
class ActiveGameplayModifier(ExportGroup):
    """/Script/FortniteGame.ActiveGameplayModifier (ActiveGameplayModifier.cs)。"""

    FIELDS = [
        field("ModifierDef", "modifier_def", RepLayoutCmdType.Property, prop_type=ItemDefinition),
    ]


@export_group("/Game/Athena/PlayerPawn_Athena.PlayerPawn_Athena_C", ParseMode.Minimal)
class PlayerPawn(ExportGroup):
    """/Game/Athena/PlayerPawn_Athena.PlayerPawn_Athena_C (PlayerPawn.cs)。"""

    FIELDS = [
        field("Owner", "owner", RepLayoutCmdType.Property, prop_type=ActorGuid),
        field("bHidden", "b_hidden", RepLayoutCmdType.Ignore),
        field("bReplicateMovement", "b_replicate_movement", RepLayoutCmdType.Ignore),
        field("bTearOff", "b_tear_off", RepLayoutCmdType.Ignore),
        field("bCanBeDamaged", "b_can_be_damaged", RepLayoutCmdType.PropertyBool),
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("ReplicatedMovement", "replicated_movement", RepLayoutCmdType.RepMovement, parse_mode=ParseMode.Full),
        field("AttachParent", "attach_parent", RepLayoutCmdType.Ignore),
        field("LocationOffset", "location_offset", RepLayoutCmdType.PropertyVector100),
        field("RelativeScale3D", "relative_scale3d", RepLayoutCmdType.PropertyVector100),
        field("RotationOffset", "rotation_offset", RepLayoutCmdType.PropertyRotator),
        field("AttachSocket", "attach_socket", RepLayoutCmdType.Property, prop_type=FName),
        field("ExitSocketIndex", "exit_socket_index", RepLayoutCmdType.PropertyByte),
        field("AttachComponent", "attach_component", RepLayoutCmdType.PropertyObject),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("Instigator", "instigator", RepLayoutCmdType.PropertyObject),
        field("RemoteViewPitch", "remote_view_pitch", RepLayoutCmdType.PropertyByte),
        field("PlayerState", "player_state", RepLayoutCmdType.PropertyObject),
        field("Controller", "controller", RepLayoutCmdType.PropertyObject),
        field("MovementBase", "movement_base", RepLayoutCmdType.PropertyObject),
        field("BoneName", "bone_name", RepLayoutCmdType.Property, prop_type=FName),
        field("Location", "location", RepLayoutCmdType.PropertyVector100),
        field("Rotation", "rotation", RepLayoutCmdType.PropertyRotator),
        field("bServerHasBaseComponent", "b_server_has_base_component", RepLayoutCmdType.PropertyBool),
        field("bRelativeRotation", "b_relative_rotation", RepLayoutCmdType.PropertyBool),
        field("bServerHasVelocity", "b_server_has_velocity", RepLayoutCmdType.PropertyBool),
        field("ReplayLastTransformUpdateTimeStamp", "replay_last_transform_update_time_stamp", RepLayoutCmdType.PropertyFloat),
        field("ReplicatedMovementMode", "replicated_movement_mode", RepLayoutCmdType.PropertyByte),
        field("bIsCrouched", "b_is_crouched", RepLayoutCmdType.PropertyBool),
        field("bProxyIsJumpForceApplied", "b_proxy_is_jump_force_applied", RepLayoutCmdType.PropertyBool),
        field("bIsActive", "b_is_active", RepLayoutCmdType.PropertyBool),
        field("Position", "position", RepLayoutCmdType.PropertyFloat),
        field("Acceleration", "acceleration", RepLayoutCmdType.Ignore),
        field("LinearVelocity", "linear_velocity", RepLayoutCmdType.PropertyVector10),
        field("CurrentMovementStyle", "current_movement_style", RepLayoutCmdType.Enum),
        field("bIgnoreNextFallingDamage", "b_ignore_next_falling_damage", RepLayoutCmdType.PropertyBool),
        field("TeleportCounter", "teleport_counter", RepLayoutCmdType.PropertyByte),
        field("PawnUniqueID", "pawn_unique_id", RepLayoutCmdType.PropertyInt),
        field("bIsDying", "b_is_dying", RepLayoutCmdType.PropertyBool),
        field("CurrentWeapon", "current_weapon", RepLayoutCmdType.PropertyObject),
        field("bIsInvulnerable", "b_is_invulnerable", RepLayoutCmdType.PropertyBool),
        field("bMovingEmote", "b_moving_emote", RepLayoutCmdType.PropertyBool),
        field("bWeaponActivated", "b_weapon_activated", RepLayoutCmdType.PropertyBool),
        field("bIsDBNO", "b_is_dbno", RepLayoutCmdType.PropertyBool),
        field("bWasDBNOOnDeath", "b_was_dbno_on_death", RepLayoutCmdType.PropertyBool),
        field("JumpFlashCount", "jump_flash_count", RepLayoutCmdType.PropertyByte),
        field("bWeaponHolstered", "b_weapon_holstered", RepLayoutCmdType.PropertyBool),
        field("FeedbackAudioComponent", "feedback_audio_component", RepLayoutCmdType.Ignore),
        field("VocalChords", "vocal_chords", RepLayoutCmdType.Ignore, element=RepLayoutCmdType.Ignore),
        field("SpawnImmunityTime", "spawn_immunity_time", RepLayoutCmdType.PropertyFloat),
        field("JumpFlashCountPacked", "jump_flash_count_packed", RepLayoutCmdType.Ignore),
        field("LandingFlashCountPacked", "landing_flash_count_packed", RepLayoutCmdType.Ignore),
        field("bInterruptCurrentLine", "b_interrupt_current_line", RepLayoutCmdType.PropertyBool),
        field("LastReplicatedEmoteExecuted", "last_replicated_emote_executed", RepLayoutCmdType.PropertyObject),
        field("bCanBeInterrupted", "b_can_be_interrupted", RepLayoutCmdType.PropertyBool),
        field("bCanQue", "b_can_que", RepLayoutCmdType.PropertyBool),
        field("ForwardAlpha", "forward_alpha", RepLayoutCmdType.PropertyFloat),
        field("RightAlpha", "right_alpha", RepLayoutCmdType.PropertyFloat),
        field("TurnDelta", "turn_delta", RepLayoutCmdType.PropertyFloat),
        field("SteerAlpha", "steer_alpha", RepLayoutCmdType.PropertyFloat),
        field("GravityScale", "gravity_scale", RepLayoutCmdType.PropertyFloat),
        field("WorldLookDir", "world_look_dir", RepLayoutCmdType.PropertyVectorQ),
        field("bIgnoreForwardInAir", "b_ignore_forward_in_air", RepLayoutCmdType.PropertyBool),
        field("bIsHonking", "b_is_honking", RepLayoutCmdType.PropertyBool),
        field("bIsJumping", "b_is_jumping", RepLayoutCmdType.PropertyBool),
        field("bIsSprinting", "b_is_sprinting", RepLayoutCmdType.PropertyBool),
        field("Vehicle", "vehicle", RepLayoutCmdType.PropertyObject),
        field("VehicleApexZ", "vehicle_apex_z", RepLayoutCmdType.PropertyFloat),
        field("SeatIndex", "seat_index", RepLayoutCmdType.PropertyByte),
        field("bIsWaterJump", "b_is_water_jump", RepLayoutCmdType.PropertyBool),
        field("bIsWaterSprintBoost", "b_is_water_sprint_boost", RepLayoutCmdType.PropertyBool),
        field("bIsWaterSprintBoostPending", "b_is_water_sprint_boost_pending", RepLayoutCmdType.PropertyBool),
        field("StasisMode", "stasis_mode", RepLayoutCmdType.Ignore),
        field("BuildingState", "building_state", RepLayoutCmdType.Enum),
        field("bIsTargeting", "b_is_targeting", RepLayoutCmdType.PropertyBool),
        field("PawnMontage", "pawn_montage", RepLayoutCmdType.PropertyObject),
        field("bPlayBit", "b_play_bit", RepLayoutCmdType.PropertyBool),
        field("bIsPlayingEmote", "b_is_playing_emote", RepLayoutCmdType.PropertyBool),
        field("FootstepBankOverride", "footstep_bank_override", RepLayoutCmdType.PropertyObject),
        field("PackedReplicatedSlopeAngles", "packed_replicated_slope_angles", RepLayoutCmdType.PropertyUInt16),
        field("bStartedInteractSearch", "b_started_interact_search", RepLayoutCmdType.PropertyBool),
        field("AccelerationPack", "acceleration_pack", RepLayoutCmdType.PropertyUInt16),
        field("AccelerationZPack", "acceleration_z_pack", RepLayoutCmdType.PropertyByte),
        field("bIsWaitingForEmoteInteraction", "b_is_waiting_for_emote_interaction", RepLayoutCmdType.PropertyBool),
        field("GroupEmoteLookTarget", "group_emote_look_target", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("bIsSkydiving", "b_is_skydiving", RepLayoutCmdType.PropertyBool),
        field("bIsParachuteOpen", "b_is_parachute_open", RepLayoutCmdType.PropertyBool),
        field("bIsParachuteForcedOpen", "b_is_parachute_forced_open", RepLayoutCmdType.PropertyBool),
        field("bIsSkydivingFromBus", "b_is_skydiving_from_bus", RepLayoutCmdType.PropertyBool),
        field("bReplicatedIsInSlipperyMovement", "b_replicated_is_in_slippery_movement", RepLayoutCmdType.PropertyBool),
        field("MovementDir", "movement_dir", RepLayoutCmdType.Ignore),
        field("bIsInAnyStorm", "b_is_in_any_storm", RepLayoutCmdType.PropertyBool),
        field("bIsSlopeSliding", "b_is_slope_sliding", RepLayoutCmdType.PropertyBool),
        field("bIsProxySimulationTimedOut", "b_is_proxy_simulation_timed_out", RepLayoutCmdType.PropertyBool),
        field("bIsInsideSafeZone", "b_is_inside_safe_zone", RepLayoutCmdType.PropertyBool),
        field("bIsOutsideSafeZone", "b_is_outside_safe_zone", RepLayoutCmdType.PropertyBool),
        field("Zipline", "zipline", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("PetState", "pet_state", RepLayoutCmdType.PropertyObject),
        field("bIsZiplining", "b_is_ziplining", RepLayoutCmdType.PropertyBool),
        field("bJumped", "b_jumped", RepLayoutCmdType.PropertyBool),
        field("ParachuteAttachment", "parachute_attachment", RepLayoutCmdType.PropertyObject),
        field("AuthoritativeValue", "authoritative_value", RepLayoutCmdType.Ignore),
        field("AuthoritativeRootMotion", "authoritative_root_motion", RepLayoutCmdType.Ignore),
        field("SocketOffset", "socket_offset", RepLayoutCmdType.Ignore),
        field("RemoteViewData32", "remote_view_data32", RepLayoutCmdType.PropertyUInt32),
        field("bNetMovementPrioritized", "b_net_movement_prioritized", RepLayoutCmdType.PropertyBool),
        field("EntryTime", "entry_time", RepLayoutCmdType.PropertyUInt32),
        field("CapsuleRadiusAthena", "capsule_radius_athena", RepLayoutCmdType.PropertyFloat),
        field("CapsuleHalfHeightAthena", "capsule_half_height_athena", RepLayoutCmdType.PropertyFloat),
        field("WalkSpeed", "walk_speed", RepLayoutCmdType.PropertyFloat),
        field("RunSpeed", "run_speed", RepLayoutCmdType.PropertyFloat),
        field("SprintSpeed", "sprint_speed", RepLayoutCmdType.PropertyFloat),
        field("CrouchedRunSpeed", "crouched_run_speed", RepLayoutCmdType.PropertyFloat),
        field("CrouchedSprintSpeed", "crouched_sprint_speed", RepLayoutCmdType.PropertyFloat),
        field("AnimMontage", "anim_montage", RepLayoutCmdType.Ignore),
        field("AnimRootMotionTranslationScale", "anim_root_motion_translation_scale", RepLayoutCmdType.Ignore),
        field("PlayRate", "play_rate", RepLayoutCmdType.PropertyFloat),
        field("BlendTime", "blend_time", RepLayoutCmdType.PropertyFloat),
        field("ForcePlayBit", "force_play_bit", RepLayoutCmdType.PropertyBool),
        field("IsStopped", "is_stopped", RepLayoutCmdType.PropertyBool),
        field("SkipPositionCorrection", "skip_position_correction", RepLayoutCmdType.PropertyBool),
        field("RepAnimMontageStartSection", "rep_anim_montage_start_section", RepLayoutCmdType.PropertyInt),
        field("ReplayRepAnimMontageInfo", "replay_rep_anim_montage_info", RepLayoutCmdType.Ignore),
        field("RepAnimMontageInfo", "rep_anim_montage_info", RepLayoutCmdType.Ignore),
        field("SimulatedProxyGameplayCues", "simulated_proxy_gameplay_cues", RepLayoutCmdType.Enum),
        field("WeaponActivated", "weapon_activated", RepLayoutCmdType.PropertyBool),
        field("bIsInWaterVolume", "b_is_in_water_volume", RepLayoutCmdType.PropertyBool),
        field("BannerIconId", "banner_icon_id", RepLayoutCmdType.PropertyString),
        field("BannerColorId", "banner_color_id", RepLayoutCmdType.PropertyString),
        field("ItemWraps", "item_wraps", RepLayoutCmdType.DynamicArray, element=ItemDefinition),
        field("SkyDiveContrail", "sky_dive_contrail", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("Glider", "glider", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("Pickaxe", "pickaxe", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("bIsDefaultCharacter", "b_is_default_character", RepLayoutCmdType.PropertyBool),
        field("Character", "character", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("CharacterVariantChannels", "character_variant_channels", RepLayoutCmdType.Ignore, element=RepLayoutCmdType.PropertyUInt32),
        field("DBNOHoister", "dbno_hoister", RepLayoutCmdType.Property, prop_type=ActorGuid),
        field("DBNOCarryEvent", "dbno_carry_event", RepLayoutCmdType.Ignore),
        field("Backpack", "backpack", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("LoadingScreen", "loading_screen", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("Dances", "dances", RepLayoutCmdType.DynamicArray, element=ItemDefinition),
        field("MusicPack", "music_pack", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("PetSkin", "pet_skin", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("EncryptedPawnReplayData", "encrypted_pawn_replay_data", RepLayoutCmdType.Property, prop_type=FAthenaPawnReplayData),
        field("GravityFloorAltitude", "gravity_floor_altitude", RepLayoutCmdType.PropertyUInt32),
        field("GravityFloorWidth", "gravity_floor_width", RepLayoutCmdType.PropertyUInt32),
        field("GravityFloorGravityScalar", "gravity_floor_gravity_scalar", RepLayoutCmdType.PropertyUInt32),
        field("ReplicatedWaterBody", "replicated_water_body", RepLayoutCmdType.PropertyObject),
        field("DBNORevivalStacking", "dbno_revival_stacking", RepLayoutCmdType.PropertyByte),
        field("ServerWorldTimeRevivalTime", "server_world_time_revival_time", RepLayoutCmdType.PropertyUInt32),
        field("ItemSpecialActorID", "item_special_actor_id", RepLayoutCmdType.Ignore),
        field("FlySpeed", "fly_speed", RepLayoutCmdType.PropertyFloat),
        field("NextSectionID", "next_section_id", RepLayoutCmdType.Ignore),
        field("FastReplicationMinimalReplicationTags", "fast_replication_minimal_replication_tags", RepLayoutCmdType.Ignore),
        field("bIsCreativeGhostModeActivated", "b_is_creative_ghost_mode_activated", RepLayoutCmdType.Ignore),
        field("PlayRespawnFXOnSpawn", "play_respawn_fx_on_spawn", RepLayoutCmdType.Ignore),
        field("bIsSkydivingFromLaunchPad", "b_is_skydiving_from_launch_pad", RepLayoutCmdType.PropertyBool),
        field("bInGliderRedeploy", "b_in_glider_redeploy", RepLayoutCmdType.PropertyBool),
        field("bReplicatedIsInVortex", "b_replicated_is_in_vortex", RepLayoutCmdType.PropertyBool),
        field("bIsTacticalSprinting", "b_is_tactical_sprinting", RepLayoutCmdType.PropertyBool),
    ]


@export_group("/Game/Athena/AI/Phoebe/BP_PlayerPawn_Athena_Phoebe.BP_PlayerPawn_Athena_Phoebe_C", ParseMode.Full)
class PhoebePlayerPawn(PlayerPawn):
    """/Game/Athena/AI/Phoebe/BP_PlayerPawn_Athena_Phoebe.BP_PlayerPawn_Athena_Phoebe_C (PlayerPawnAI.cs)。"""

    FIELDS = PlayerPawn.FIELDS


@export_group("/Game/Athena/AI/MANG/BP_MangPlayerPawn_Default.BP_MangPlayerPawn_Default_C", ParseMode.Full)
class MangPlayerPawn(PlayerPawn):
    """/Game/Athena/AI/MANG/BP_MangPlayerPawn_Default.BP_MangPlayerPawn_Default_C (PlayerPawnAI.cs)。"""

    FIELDS = PlayerPawn.FIELDS + [
        field("AlertLevel", "alert_level", RepLayoutCmdType.Enum),
        field("bIsStaggered", "b_is_staggered", RepLayoutCmdType.PropertyBool),
        field("StealthMeterTarget_4_A61BD65840C63E1798329EAE84F4B5C7", "stealth_meter_target", RepLayoutCmdType.PropertyFloat),
        field("StealthMeterTargetTime_5_627E99734167FD2903748490D5FC2A57", "stealth_meter_target_time", RepLayoutCmdType.PropertyFloat),
    ]


@export_group("/Game/Athena/AI/MANG/BP_MangPlayerPawn_Boss_AdventureGirl.BP_MangPlayerPawn_Boss_AdventureGirl_C", ParseMode.Full)
class MangBossPlayerPawn(MangPlayerPawn):
    """/Game/Athena/AI/MANG/BP_MangPlayerPawn_Boss_AdventureGirl.BP_MangPlayerPawn_Boss_AdventureGirl_C (PlayerPawnAI.cs)。"""

    FIELDS = MangPlayerPawn.FIELDS


@export_group("/Game/Athena/AI/MANG/MangDataTracker.MangDataTracker_C", ParseMode.Full)
class MangDataTracker(ExportGroup):
    """/Game/Athena/AI/MANG/MangDataTracker.MangDataTracker_C (PlayerPawnAI.cs)。"""

    FIELDS = [
        field("BotPawn", "bot_pawn", RepLayoutCmdType.Property, prop_type=ActorGuid),
        field("CurrentBotAlertLevel", "current_bot_alert_level", RepLayoutCmdType.Enum),
    ]


@export_group("/Game/Athena/Aircraft/AthenaAircraft.AthenaAircraft_C", ParseMode.Ignore)
class Aircraft(ExportGroup):
    """/Game/Athena/Aircraft/AthenaAircraft.AthenaAircraft_C (Aircraft.cs)。"""

    FIELDS = [
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("JumpFlashCount", "jump_flash_count", RepLayoutCmdType.PropertyInt),
        field("FlightStartLocation", "flight_start_location", RepLayoutCmdType.PropertyVector100),
        field("FlightStartRotation", "flight_start_rotation", RepLayoutCmdType.PropertyRotator),
        field("FlightSpeed", "flight_speed", RepLayoutCmdType.PropertyFloat),
        field("TimeTillFlightEnd", "time_till_flight_end", RepLayoutCmdType.PropertyFloat),
        field("TimeTillDropStart", "time_till_drop_start", RepLayoutCmdType.PropertyFloat),
        field("TimeTillDropEnd", "time_till_drop_end", RepLayoutCmdType.PropertyFloat),
        field("FlightStartTime", "flight_start_time", RepLayoutCmdType.PropertyFloat),
        field("FlightEndTime", "flight_end_time", RepLayoutCmdType.PropertyFloat),
        field("DropStartTime", "drop_start_time", RepLayoutCmdType.PropertyFloat),
        field("DropEndTime", "drop_end_time", RepLayoutCmdType.PropertyFloat),
        field("ReplicatedFlightTimestamp", "replicated_flight_timestamp", RepLayoutCmdType.PropertyFloat),
        field("AircraftIndex", "aircraft_index", RepLayoutCmdType.PropertyUInt32),
    ]


class BaseBuild(ExportGroup):
    """BaseBuild (BaseBuild.cs)。"""

    FIELDS = [
        field("bHidden", "b_hidden", RepLayoutCmdType.Ignore),
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("OwnerPersistentID", "owner_persistent_id", RepLayoutCmdType.PropertyUInt32),
        field("bDestroyed", "b_destroyed", RepLayoutCmdType.PropertyBool),
        field("bPlayerPlaced", "b_player_placed", RepLayoutCmdType.PropertyBool),
        field("bInstantDeath", "b_instant_death", RepLayoutCmdType.PropertyBool),
        field("bCollisionBlockedByPawns", "b_collision_blocked_by_pawns", RepLayoutCmdType.PropertyBool),
        field("bIsInitiallyBuilding", "b_is_initially_building", RepLayoutCmdType.PropertyBool),
        field("TeamIndex", "team_index", RepLayoutCmdType.Enum),
        field("BuildingAnimation", "building_animation", RepLayoutCmdType.Enum),
        field("BuildTime", "build_time", RepLayoutCmdType.Ignore),
        field("RepairTime", "repair_time", RepLayoutCmdType.Ignore),
        field("Health", "health", RepLayoutCmdType.PropertyInt16),
        field("MaxHealth", "max_health", RepLayoutCmdType.PropertyInt16),
        field("EditingPlayer", "editing_player", RepLayoutCmdType.Property, prop_type=ActorGuid),
        field("ProxyGameplayCueDamagePhysicalMagnitude", "proxy_gameplay_cue_damage_physical_magnitude", RepLayoutCmdType.Ignore),
        field("EffectContext", "effect_context", RepLayoutCmdType.Ignore),
        field("bAttachmentPlacementBlockedFront", "b_attachment_placement_blocked_front", RepLayoutCmdType.PropertyBool),
        field("bAttachmentPlacementBlockedBack", "b_attachment_placement_blocked_back", RepLayoutCmdType.PropertyBool),
        field("bUnderConstruction", "b_under_construction", RepLayoutCmdType.PropertyBool),
        field("StaticMesh", "static_mesh", RepLayoutCmdType.Ignore),
        field("Gnomed", "gnomed", RepLayoutCmdType.PropertyBool),
        field("InitialOverlappingVehicles", "initial_overlapping_vehicles", RepLayoutCmdType.Property, prop_type=DebuggingObject),
    ]


@export_group("/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_Floor.PBWA_W1_Floor_C", ParseMode.Debug)
class WoodFloor(BaseBuild):
    """/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_Floor.PBWA_W1_Floor_C (Floor.cs)。"""

    FIELDS = BaseBuild.FIELDS


@export_group("/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_BalconyI.PBWA_W1_BalconyI_C", ParseMode.Debug)
class WoodBalconyIFloor(BaseBuild):
    """/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_BalconyI.PBWA_W1_BalconyI_C (Floor.cs)。"""

    FIELDS = BaseBuild.FIELDS


@export_group("/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_BalconyS.PBWA_W1_BalconyS_C", ParseMode.Debug)
class WoodBalconySFloor(BaseBuild):
    """/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_BalconyS.PBWA_W1_BalconyS_C (Floor.cs)。"""

    FIELDS = BaseBuild.FIELDS


@export_group("/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_RoofC.PBWA_W1_RoofC_C", ParseMode.Debug)
class WoodRoof(BaseBuild):
    """/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_RoofC.PBWA_W1_RoofC_C (Roof.cs)。"""

    FIELDS = BaseBuild.FIELDS


@export_group("/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_StairW.PBWA_W1_StairW_C", ParseMode.Debug)
class WoodStair(BaseBuild):
    """/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_StairW.PBWA_W1_StairW_C (Stair.cs)。"""

    FIELDS = BaseBuild.FIELDS


@export_group("/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_Solid.PBWA_W1_Solid_C", ParseMode.Debug)
class WoodWall(BaseBuild):
    """/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_Solid.PBWA_W1_Solid_C (Wall.cs)。"""

    FIELDS = BaseBuild.FIELDS


@export_group("/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_ArchwayLarge.PBWA_W1_ArchwayLarge_C", ParseMode.Debug)
class WoodArchwayWall(BaseBuild):
    """/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_ArchwayLarge.PBWA_W1_ArchwayLarge_C (Wall.cs)。"""

    FIELDS = BaseBuild.FIELDS


@export_group("/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_Brace.PBWA_W1_Brace_C", ParseMode.Debug)
class WoodBraceWall(BaseBuild):
    """/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_Brace.PBWA_W1_Brace_C (Wall.cs)。"""

    FIELDS = BaseBuild.FIELDS


@export_group("/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_DoorSide.PBWA_W1_DoorSide_C", ParseMode.Debug)
class WoodDoorSideWall(BaseBuild):
    """/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_DoorSide.PBWA_W1_DoorSide_C (Wall.cs)。"""

    FIELDS = BaseBuild.FIELDS + [
        field("bDoorOpen", "b_door_open", RepLayoutCmdType.PropertyBool),
        field("DoorDesiredRotOffset", "door_desired_rot_offset", RepLayoutCmdType.PropertyRotator),
    ]


@export_group("/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_DoorC.PBWA_W1_DoorC_C", ParseMode.Debug)
class WoodDoorWall(BaseBuild):
    """/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_DoorC.PBWA_W1_DoorC_C (Wall.cs)。"""

    FIELDS = BaseBuild.FIELDS


@export_group("/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_WindowSide.PBWA_W1_WindowSide_C", ParseMode.Debug)
class WoodWindowSideWall(BaseBuild):
    """/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_WindowSide.PBWA_W1_WindowSide_C (Wall.cs)。"""

    FIELDS = BaseBuild.FIELDS


@export_group("/Game/Building/ActorBlueprints/Player/Stone/L1/PBWA_S1_Solid.PBWA_S1_Solid_C", ParseMode.Debug)
class StoneWall(BaseBuild):
    """/Game/Building/ActorBlueprints/Player/Stone/L1/PBWA_S1_Solid.PBWA_S1_Solid_C (Wall.cs)。"""

    FIELDS = BaseBuild.FIELDS


@export_group("/Game/Building/ActorBlueprints/Player/Metal/L1/PBWA_M1_Solid.PBWA_M1_Solid_C", ParseMode.Debug)
class MetalWall(BaseBuild):
    """/Game/Building/ActorBlueprints/Player/Metal/L1/PBWA_M1_Solid.PBWA_M1_Solid_C (Wall.cs)。"""

    FIELDS = BaseBuild.FIELDS


class BaseConsumable(ExportGroup):
    """BaseConsumable (BaseConsumable.cs)。"""

    FIELDS = [
        field("bHidden", "b_hidden", RepLayoutCmdType.Ignore),
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("Owner", "owner", RepLayoutCmdType.Ignore),
        field("Instigator", "instigator", RepLayoutCmdType.PropertyObject),
        field("bIsEquippingWeapon", "b_is_equipping_weapon", RepLayoutCmdType.PropertyBool),
        field("WeaponData", "weapon_data", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("WeaponLevel", "weapon_level", RepLayoutCmdType.PropertyInt),
        field("A", "a", RepLayoutCmdType.PropertyUInt32),
        field("B", "b", RepLayoutCmdType.PropertyUInt32),
        field("C", "c", RepLayoutCmdType.PropertyUInt32),
        field("D", "d", RepLayoutCmdType.PropertyUInt32),
    ]


class Fish(BaseConsumable):
    """Fish (Fish.cs)。"""

    FIELDS = BaseConsumable.FIELDS


@export_group("/Game/Athena/Items/Consumables/Flopper/Small/B_FlopperSmall_Weap_Athena.B_FlopperSmall_Weap_Athena_C", ParseMode.Debug)
class SmallFry(Fish):
    """/Game/Athena/Items/Consumables/Flopper/Small/B_FlopperSmall_Weap_Athena.B_FlopperSmall_Weap_Athena_C (Fish.cs)。"""

    FIELDS = Fish.FIELDS


@export_group("/Game/Athena/Items/Consumables/Flopper/B_Flopper_Weap_Athena.B_Flopper_Weap_Athena_C", ParseMode.Debug)
class Flopper(Fish):
    """/Game/Athena/Items/Consumables/Flopper/B_Flopper_Weap_Athena.B_Flopper_Weap_Athena_C (Fish.cs)。"""

    FIELDS = Fish.FIELDS


@export_group("/Game/Athena/Items/Consumables/Flopper/Effective/B_EffectiveFlopper_Weap_Athena.B_EffectiveFlopper_Weap_Athena_C", ParseMode.Debug)
class SlurpFish(Fish):
    """/Game/Athena/Items/Consumables/Flopper/Effective/B_EffectiveFlopper_Weap_Athena.B_EffectiveFlopper_Weap_Athena_C (Fish.cs)。"""

    FIELDS = Fish.FIELDS


class Health(BaseConsumable):
    """Health (Health.cs)。"""

    FIELDS = BaseConsumable.FIELDS


@export_group("/Game/Abilities/Player/Generic/UtilityItems/B_ConsumableSmall_Bandages_Athena.B_ConsumableSmall_Bandages_Athena_C", ParseMode.Debug)
class Bandages(Health):
    """/Game/Abilities/Player/Generic/UtilityItems/B_ConsumableSmall_Bandages_Athena.B_ConsumableSmall_Bandages_Athena_C (Health.cs)。"""

    FIELDS = Health.FIELDS


@export_group("/Game/Abilities/Player/Generic/UtilityItems/B_ConsumableSmall_Medkit_Athena.B_ConsumableSmall_Medkit_Athena_C", ParseMode.Debug)
class Medkit(Health):
    """/Game/Abilities/Player/Generic/UtilityItems/B_ConsumableSmall_Medkit_Athena.B_ConsumableSmall_Medkit_Athena_C (Health.cs)。"""

    FIELDS = Health.FIELDS


class Shield(BaseConsumable):
    """Shield (Shield.cs)。"""

    FIELDS = BaseConsumable.FIELDS


@export_group("/Game/Abilities/Player/Generic/UtilityItems/B_ConsumableSmall_MiniShield_Athena.B_ConsumableSmall_MiniShield_Athena_C", ParseMode.Debug)
class MiniShield(Shield):
    """/Game/Abilities/Player/Generic/UtilityItems/B_ConsumableSmall_MiniShield_Athena.B_ConsumableSmall_MiniShield_Athena_C (Shield.cs)。"""

    FIELDS = Shield.FIELDS


@export_group("/Game/Abilities/Player/Generic/UtilityItems/B_ConsumableSmall_HalfShield_Athena.B_ConsumableSmall_HalfShield_Athena_C", ParseMode.Debug)
class HalfShield(Shield):
    """/Game/Abilities/Player/Generic/UtilityItems/B_ConsumableSmall_HalfShield_Athena.B_ConsumableSmall_HalfShield_Athena_C (Shield.cs)。"""

    FIELDS = Shield.FIELDS


@export_group("/Game/Abilities/Player/Generic/UtilityItems/B_UtilityItem_Generic_Athena.B_UtilityItem_Generic_Athena_C", ParseMode.Debug)
class ChugJug(Shield):
    """/Game/Abilities/Player/Generic/UtilityItems/B_UtilityItem_Generic_Athena.B_UtilityItem_Generic_Athena_C (Shield.cs)。"""

    FIELDS = Shield.FIELDS


@export_group("/Script/FortniteGame.FortClientObservedStat", ParseMode.Debug)
class FortClientObservedStat(ExportGroup):
    """/Script/FortniteGame.FortClientObservedStat (FortClientObservedStat.cs)。"""

    FIELDS = [
        field("StatName", "stat_name", RepLayoutCmdType.PropertyName),
        field("StatValue", "stat_value", RepLayoutCmdType.PropertyInt),
    ]


@export_subgroup("/Script/FortniteGame.FortPickupAthena", ParseMode.Ignore)
class FortItemEntryStateValue(ExportGroup):
    """/Script/FortniteGame.FortPickupAthena (FortItemEntryStateValue.cs)。"""

    FIELDS = [
        field("StateType", "state_type", RepLayoutCmdType.Enum),
        field("IntValue", "int_value", RepLayoutCmdType.PropertyInt),
        field("NameValue", "name_value", RepLayoutCmdType.Property, prop_type=FName),
    ]


@export_group("/Script/FortniteGame.FortInventory")
class FortInventory(ExportGroup):
    """/Script/FortniteGame.FortInventory (FortInventory.cs)。"""

    FIELDS = [
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Owner", "owner", RepLayoutCmdType.PropertyObject),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("Count", "count", RepLayoutCmdType.PropertyInt),
        field("ItemDefinition", "item_definition", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("OrderIndex", "order_index", RepLayoutCmdType.PropertyUInt16),
        field("Durability", "durability", RepLayoutCmdType.PropertyFloat),
        field("Level", "level", RepLayoutCmdType.PropertyInt),
        field("LoadedAmmo", "loaded_ammo", RepLayoutCmdType.PropertyInt),
        field("A", "a", RepLayoutCmdType.PropertyUInt32),
        field("B", "b", RepLayoutCmdType.PropertyUInt32),
        field("C", "c", RepLayoutCmdType.PropertyUInt32),
        field("D", "d", RepLayoutCmdType.PropertyUInt32),
        field("inventory_overflow_date", "inventory_overflow_date", RepLayoutCmdType.PropertyBool),
        field("bWasGifted", "b_was_gifted", RepLayoutCmdType.PropertyBool),
        field("bIsReplicatedCopy", "b_is_replicated_copy", RepLayoutCmdType.PropertyBool),
        field("bIsDirty", "b_is_dirty", RepLayoutCmdType.PropertyBool),
        field("bUpdateStatsOnCollection", "b_update_stats_on_collection", RepLayoutCmdType.PropertyBool),
        field("StateValues", "state_values", RepLayoutCmdType.DynamicArray, element=FortItemEntryStateValue),
        field("ParentInventory", "parent_inventory", RepLayoutCmdType.PropertyObject),
        field("Handle", "handle", RepLayoutCmdType.PropertyInt),
        field("WrapOverride", "wrap_override", RepLayoutCmdType.PropertyUInt32),
        field("AlterationInstances", "alteration_instances", RepLayoutCmdType.Ignore, element=DebuggingObject),
        field("GenericAttributeValues", "generic_attribute_values", RepLayoutCmdType.Ignore, element=DebuggingObject),
        field("ReplayPawn", "replay_pawn", RepLayoutCmdType.PropertyObject),
    ]


@export_group("/Script/FortniteGame.FortPickupAthena", ParseMode.Normal)
class FortPickup(ExportGroup):
    """/Script/FortniteGame.FortPickupAthena (FortPickup.cs)。"""

    FIELDS = [
        field("bReplicateMovement", "b_replicate_movement", RepLayoutCmdType.PropertyBool),
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("ReplicatedMovement", "replicated_movement", RepLayoutCmdType.RepMovement),
        field("AttachParent", "attach_parent", RepLayoutCmdType.Ignore),
        field("LocationOffset", "location_offset", RepLayoutCmdType.PropertyVector100),
        field("RelativeScale3D", "relative_scale3d", RepLayoutCmdType.PropertyVector100),
        field("RotationOffset", "rotation_offset", RepLayoutCmdType.PropertyRotator),
        field("AttachComponent", "attach_component", RepLayoutCmdType.PropertyObject),
        field("Owner", "owner", RepLayoutCmdType.PropertyObject),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("bRandomRotation", "b_random_rotation", RepLayoutCmdType.PropertyBool),
        field("Count", "count", RepLayoutCmdType.PropertyInt),
        field("ItemDefinition", "item_definition", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("Durability", "durability", RepLayoutCmdType.PropertyFloat),
        field("Level", "level", RepLayoutCmdType.PropertyInt),
        field("LoadedAmmo", "loaded_ammo", RepLayoutCmdType.PropertyInt),
        field("A", "a", RepLayoutCmdType.PropertyUInt32),
        field("B", "b", RepLayoutCmdType.PropertyUInt32),
        field("C", "c", RepLayoutCmdType.PropertyUInt32),
        field("D", "d", RepLayoutCmdType.PropertyUInt32),
        field("bUpdateStatsOnCollection", "b_update_stats_on_collection", RepLayoutCmdType.PropertyBool),
        field("bIsDirty", "b_is_dirty", RepLayoutCmdType.PropertyBool),
        field("StateValues", "state_values", RepLayoutCmdType.DynamicArray, element=FortItemEntryStateValue),
        field("GenericAttributeValues", "generic_attribute_values", RepLayoutCmdType.DynamicArray, element=RepLayoutCmdType.PropertyFloat),
        field("CombineTarget", "combine_target", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("PickupTarget", "pickup_target", RepLayoutCmdType.PropertyObject),
        field("ItemOwner", "item_owner", RepLayoutCmdType.PropertyObject),
        field("LootInitialPosition", "loot_initial_position", RepLayoutCmdType.PropertyVector10),
        field("LootFinalPosition", "loot_final_position", RepLayoutCmdType.PropertyVector10),
        field("FlyTime", "fly_time", RepLayoutCmdType.PropertyFloat),
        field("StartDirection", "start_direction", RepLayoutCmdType.PropertyVectorNormal),
        field("FinalTossRestLocation", "final_toss_rest_location", RepLayoutCmdType.PropertyVector10),
        field("TossState", "toss_state", RepLayoutCmdType.Enum),
        field("bCombinePickupsWhenTossCompletes", "b_combine_pickups_when_toss_completes", RepLayoutCmdType.PropertyBool),
        field("OptionalOwnerID", "optional_owner_id", RepLayoutCmdType.PropertyInt),
        field("bPickedUp", "b_picked_up", RepLayoutCmdType.PropertyBool),
        field("bTossedFromContainer", "b_tossed_from_container", RepLayoutCmdType.PropertyBool),
        field("bServerStoppedSimulation", "b_server_stopped_simulation", RepLayoutCmdType.PropertyBool),
        field("ServerImpactSoundFlash", "server_impact_sound_flash", RepLayoutCmdType.PropertyByte),
        field("PawnWhoDroppedPickup", "pawn_who_dropped_pickup", RepLayoutCmdType.PropertyObject),
        field("OrderIndex", "order_index", RepLayoutCmdType.PropertyUInt16),
    ]


@export_group("/Script/FortniteGame.FortPlayerStateAthena", ParseMode.Minimal)
class FortPlayerState(ExportGroup):
    """/Script/FortniteGame.FortPlayerStateAthena (FortPlayerState.cs)。"""

    FIELDS = [
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Owner", "owner", RepLayoutCmdType.Ignore),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("Instigator", "instigator", RepLayoutCmdType.PropertyObject),
        field("Score", "score", RepLayoutCmdType.PropertyUInt32),
        field("PlayerID", "player_id_legacy", RepLayoutCmdType.PropertyInt),
        field("PlayerId", "player_id", RepLayoutCmdType.PropertyUInt32),
        field("Ping", "ping", RepLayoutCmdType.Ignore),
        field("bIsABot", "b_is_a_bot", RepLayoutCmdType.PropertyBool),
        field("bIsSpectator", "b_is_spectator", RepLayoutCmdType.PropertyBool),
        field("bOnlySpectator", "b_only_spectator", RepLayoutCmdType.PropertyBool),
        field("StartTime", "start_time", RepLayoutCmdType.PropertyInt),
        field("UniqueId", "unique_id", RepLayoutCmdType.PropertyNetId),
        field("UniqueID", "unique_id_legacy", RepLayoutCmdType.PropertyNetId),
        field("PlayerNamePrivate", "player_name_private", RepLayoutCmdType.Ignore),
        field("bIsGameSessionOwner", "b_is_game_session_owner", RepLayoutCmdType.PropertyBool),
        field("bHasFinishedLoading", "b_has_finished_loading", RepLayoutCmdType.PropertyBool),
        field("bHasStartedPlaying", "b_has_started_playing", RepLayoutCmdType.PropertyBool),
        field("PlayerRole", "player_role", RepLayoutCmdType.Enum),
        field("PartyOwnerUniqueId", "party_owner_unique_id", RepLayoutCmdType.PropertyNetId),
        field("WorldPlayerId", "world_player_id", RepLayoutCmdType.PropertyInt16),
        field("HeroType", "hero_type", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("Platform", "platform", RepLayoutCmdType.PropertyString),
        field("CharacterGender", "character_gender", RepLayoutCmdType.Enum),
        field("CharacterBodyType", "character_body_type", RepLayoutCmdType.Enum),
        field("WasReplicatedFlags", "was_replicated_flags", RepLayoutCmdType.Ignore),
        field("Parts", "parts", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("WasPartReplicatedFlags", "was_part_replicated_flags", RepLayoutCmdType.Ignore),
        field("RequiredVariantPartFlags", "required_variant_part_flags", RepLayoutCmdType.PropertyUInt32),
        field("VariantRequiredCharacterParts", "variant_required_character_parts", RepLayoutCmdType.DynamicArray, element=ItemDefinition),
        field("PlayerTeamPrivate", "player_team_private", RepLayoutCmdType.PropertyObject),
        field("PlatformUniqueNetId", "platform_unique_net_id", RepLayoutCmdType.PropertyNetId),
        field("TeamIndex", "team_index", RepLayoutCmdType.Enum),
        field("Place", "place", RepLayoutCmdType.PropertyInt),
        field("ReplicatedTeamMemberState", "replicated_team_member_state", RepLayoutCmdType.Enum),
        field("bHasEverSkydivedFromBus", "b_has_ever_skydived_from_bus", RepLayoutCmdType.PropertyBool),
        field("bHasEverSkydivedFromBusAndLanded", "b_has_ever_skydived_from_bus_and_landed", RepLayoutCmdType.PropertyBool),
        field("SquadListUpdateValue", "squad_list_update_value", RepLayoutCmdType.PropertyInt),
        field("SquadId", "squad_id", RepLayoutCmdType.PropertyByte),
        field("bInAircraft", "b_in_aircraft", RepLayoutCmdType.PropertyBool),
        field("bThankedBusDriver", "b_thanked_bus_driver", RepLayoutCmdType.PropertyBool),
        field("bDidNotThankBusDriver", "b_did_not_thank_bus_driver", RepLayoutCmdType.PropertyBool),
        field("TeamKillScore", "team_kill_score", RepLayoutCmdType.PropertyUInt32),
        field("bUsingStreamerMode", "b_using_streamer_mode", RepLayoutCmdType.PropertyBool),
        field("StreamerModeName", "streamer_mode_name", RepLayoutCmdType.Property, prop_type=FText),
        field("PlayerNameCustomOverride", "player_name_custom_override", RepLayoutCmdType.Property, prop_type=FText),
        field("TeamScorePlacement", "team_score_placement", RepLayoutCmdType.PropertyUInt32),
        field("IconId", "icon_id", RepLayoutCmdType.PropertyString),
        field("TeamScore", "team_score", RepLayoutCmdType.PropertyUInt32),
        field("ColorId", "color_id", RepLayoutCmdType.PropertyString),
        field("Level", "level", RepLayoutCmdType.PropertyInt),
        field("MapIndicatorPos", "map_indicator_pos", RepLayoutCmdType.PropertyVector2D),
        field("KillScore", "kill_score", RepLayoutCmdType.PropertyUInt32),
        field("FinisherOrDowner", "finisher_or_downer", RepLayoutCmdType.PropertyObject),
        field("SeasonLevelUIDisplay", "season_level_ui_display", RepLayoutCmdType.PropertyUInt32),
        field("bInitialized", "b_initialized", RepLayoutCmdType.PropertyBool),
        field("DeathCircumstance", "death_circumstance", RepLayoutCmdType.PropertyInt),
        field("bUsingAnonymousMode", "b_using_anonymous_mode", RepLayoutCmdType.PropertyBool),
        field("bIsDisconnected", "b_is_disconnected", RepLayoutCmdType.PropertyBool),
        field("bDBNO", "b_dbno", RepLayoutCmdType.PropertyBool),
        field("DeathCause", "death_cause", RepLayoutCmdType.Enum),
        field("Distance", "distance", RepLayoutCmdType.PropertyFloat),
        field("DeathTags", "death_tags", RepLayoutCmdType.Property, prop_type=FGameplayTagContainer),
        field("VictimTags", "victim_tags", RepLayoutCmdType.Property, prop_type=FGameplayTagContainer),
        field("FinisherOrDownerTags", "finisher_or_downer_tags", RepLayoutCmdType.Property, prop_type=FGameplayTagContainer),
        field("bResurrectionChipAvailable", "b_resurrection_chip_available", RepLayoutCmdType.PropertyBool),
        field("ResurrectionExpirationTime", "resurrection_expiration_time", RepLayoutCmdType.PropertyFloat),
        field("ResurrectionExpirationLength", "resurrection_expiration_length", RepLayoutCmdType.PropertyFloat),
        field("WorldLocation", "world_location", RepLayoutCmdType.Ignore),
        field("bResurrectingNow", "b_resurrecting_now", RepLayoutCmdType.PropertyBool),
        field("RebootCounter", "reboot_counter", RepLayoutCmdType.PropertyUInt32),
        field("bHoldsRebootVanLock", "b_holds_reboot_van_lock", RepLayoutCmdType.PropertyBool),
        field("BotUniqueId", "bot_unique_id", RepLayoutCmdType.PropertyNetId),
        field("DeathLocation", "death_location", RepLayoutCmdType.PropertyVector),
        field("SimulatedAttributes", "simulated_attributes", RepLayoutCmdType.Ignore),
        field("KickedFromSessionReason", "kicked_from_session_reason", RepLayoutCmdType.Enum),
        field("NumRejoins", "num_rejoins", RepLayoutCmdType.PropertyInt),
        field("bIsAnAthenaGameParticipant", "b_is_an_athena_game_participant", RepLayoutCmdType.PropertyBool),
        field("bHidden", "b_hidden", RepLayoutCmdType.Ignore),
    ]


@export_group("/Script/FortniteGame.FortPoiManager", ParseMode.Full)
class FortPoiManager(ExportGroup):
    """/Script/FortniteGame.FortPoiManager (FortPoiManager.cs)。"""

    FIELDS = [
        field("WorldGridStart", "world_grid_start", RepLayoutCmdType.PropertyVector2D),
        field("WorldGridEnd", "world_grid_end", RepLayoutCmdType.PropertyVector2D),
        field("WorldGridSpacing", "world_grid_spacing", RepLayoutCmdType.PropertyVector2D),
        field("GridCountX", "grid_count_x", RepLayoutCmdType.PropertyInt),
        field("GridCountY", "grid_count_y", RepLayoutCmdType.PropertyInt),
        field("WorldGridTotalSize", "world_grid_total_size", RepLayoutCmdType.PropertyVector2D),
        field("PoiTagContainerTable", "poi_tag_container_table", RepLayoutCmdType.DynamicArray, element=FGameplayTagContainer),
        field("PoiTagContainerTableSize", "poi_tag_container_table_size", RepLayoutCmdType.PropertyInt),
    ]


@export_group("/Script/FortniteGame.FortTeamPrivateInfo", ParseMode.Debug)
class FortTeamPrivateInfo(ExportGroup):
    """/Script/FortniteGame.FortTeamPrivateInfo (FortTeamPrivateInfo.cs)。"""

    FIELDS = [
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("Owner", "owner", RepLayoutCmdType.PropertyObject),
        field("Value", "value", RepLayoutCmdType.PropertyFloat),
        field("PlayerId", "player_id", RepLayoutCmdType.PropertyNetId),
        field("PlayerID", "player_id_legacy", RepLayoutCmdType.PropertyNetId),
        field("PlayerState", "player_state", RepLayoutCmdType.Property, prop_type=ActorGuid),
        field("LastRepLocation", "last_rep_location", RepLayoutCmdType.PropertyVector100),
        field("LastRepYaw", "last_rep_yaw", RepLayoutCmdType.PropertyFloat),
        field("PawnStateMask", "pawn_state_mask", RepLayoutCmdType.Enum),
    ]


@export_group("/Script/FortniteGame.GameMemberInfo", ParseMode.Ignore)
class GameMemberInfo(ExportGroup):
    """/Script/FortniteGame.GameMemberInfo (GameMemberInfo.cs)。"""

    FIELDS = [
        field("SquadId", "squad_id", RepLayoutCmdType.PropertyByte),
        field("TeamIndex", "team_index", RepLayoutCmdType.Enum),
        field("MemberUniqueId", "member_unique_id", RepLayoutCmdType.PropertyNetId),
    ]


@export_group("/Game/Athena/Athena_GameState.Athena_GameState_C", ParseMode.Minimal)
class GameState(ExportGroup):
    """/Game/Athena/Athena_GameState.Athena_GameState_C (GameState.cs)。"""

    FIELDS = [
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("GameModeClass", "game_mode_class", RepLayoutCmdType.Ignore),
        field("SpectatorClass", "spectator_class", RepLayoutCmdType.Ignore),
        field("FortTimeOfDayManager", "fort_time_of_day_manager", RepLayoutCmdType.Ignore),
        field("PoiManager", "poi_manager", RepLayoutCmdType.Ignore),
        field("FeedbackManager", "feedback_manager", RepLayoutCmdType.Ignore),
        field("MissionManager", "mission_manager", RepLayoutCmdType.Ignore),
        field("AnnouncementManager", "announcement_manager", RepLayoutCmdType.Ignore),
        field("WorldManager", "world_manager", RepLayoutCmdType.Ignore),
        field("MusicManagerSubclass", "music_manager_subclass", RepLayoutCmdType.Ignore),
        field("MusicManagerBank", "music_manager_bank", RepLayoutCmdType.Ignore),
        field("PawnForReplayRelevancy", "pawn_for_replay_relevancy", RepLayoutCmdType.Ignore),
        field("RecorderPlayerState", "recorder_player_state", RepLayoutCmdType.Property, prop_type=ActorGuid),
        field("GlobalEnvironmentAbilityActor", "global_environment_ability_actor", RepLayoutCmdType.Ignore),
        field("UIMapManager", "ui_map_manager", RepLayoutCmdType.Ignore),
        field("CreativePlotManager", "creative_plot_manager", RepLayoutCmdType.Ignore),
        field("PlayspaceManager", "playspace_manager", RepLayoutCmdType.Ignore),
        field("ItemCollector", "item_collector", RepLayoutCmdType.Ignore),
        field("SpecialActorData", "special_actor_data", RepLayoutCmdType.Ignore),
        field("SupplyDropWaveStartedSoundCue", "supply_drop_wave_started_sound_cue", RepLayoutCmdType.Ignore),
        field("TeamXPlayersLeft", "team_x_players_left", RepLayoutCmdType.Ignore),
        field("SafeZoneIndicator", "safe_zone_indicator", RepLayoutCmdType.Ignore),
        field("MapInfo", "map_info", RepLayoutCmdType.Ignore),
        field("GoldenPoiLocationTags", "golden_poi_location_tags", RepLayoutCmdType.Property, prop_type=FGameplayTagContainer),
        field("DefaultBattleBus", "default_battle_bus", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("bReplicatedHasBegunPlay", "b_replicated_has_begun_play", RepLayoutCmdType.PropertyBool),
        field("ReplicatedWorldTimeSeconds", "replicated_world_time_seconds", RepLayoutCmdType.PropertyFloat),
        field("ReplicatedWorldTimeSecondsDouble", "replicated_world_time_seconds_double", RepLayoutCmdType.PropertyDouble),
        field("ReplicatedWorldRealTimeSecondsDouble", "replicated_world_real_time_seconds_double", RepLayoutCmdType.PropertyDouble),
        field("MatchState", "match_state", RepLayoutCmdType.Property, prop_type=FName),
        field("ElapsedTime", "elapsed_time", RepLayoutCmdType.PropertyInt),
        field("WorldLevel", "world_level", RepLayoutCmdType.PropertyInt),
        field("CraftingBonus", "crafting_bonus", RepLayoutCmdType.PropertyInt),
        field("TeamCount", "team_count", RepLayoutCmdType.PropertyInt),
        field("TeamSize", "team_size", RepLayoutCmdType.PropertyInt),
        field("GameFlagData", "game_flag_data", RepLayoutCmdType.PropertyInt),
        field("AdditionalPlaylistLevelsStreamed", "additional_playlist_levels_streamed", RepLayoutCmdType.DynamicArray, element=FName),
        field("WorldDaysElapsed", "world_days_elapsed", RepLayoutCmdType.PropertyInt),
        field("GameplayState", "gameplay_state", RepLayoutCmdType.Enum),
        field("GameSessionId", "game_session_id", RepLayoutCmdType.PropertyString),
        field("SpawnPointsCap", "spawn_points_cap", RepLayoutCmdType.PropertyInt),
        field("SpawnPointsAllocated", "spawn_points_allocated", RepLayoutCmdType.PropertyInt),
        field("PlayerSharedMaxTrapAttributes", "player_shared_max_trap_attributes", RepLayoutCmdType.DynamicArray, element=RepLayoutCmdType.PropertyFloat),
        field("TotalPlayerStructures", "total_player_structures", RepLayoutCmdType.PropertyInt),
        field("ServerGameplayTagIndexHash", "server_gameplay_tag_index_hash", RepLayoutCmdType.PropertyUInt32),
        field("GameDifficulty", "game_difficulty", RepLayoutCmdType.PropertyFloat),
        field("bAllowLayoutRequirementsFeature", "b_allow_layout_requirements_feature", RepLayoutCmdType.PropertyBool),
        field("ServerStability", "server_stability", RepLayoutCmdType.Enum),
        field("RoundTimeAccumulated", "round_time_accumulated", RepLayoutCmdType.PropertyInt),
        field("RoundTimeCriticalThreshold", "round_time_critical_threshold", RepLayoutCmdType.PropertyInt),
        field("ServerChangelistNumber", "server_changelist_number", RepLayoutCmdType.PropertyInt),
        field("CreativeRealEstatePlotManager", "creative_real_estate_plot_manager", RepLayoutCmdType.Ignore),
        field("WarmupCountdownStartTime", "warmup_countdown_start_time", RepLayoutCmdType.PropertyFloat),
        field("WarmupCountdownEndTime", "warmup_countdown_end_time", RepLayoutCmdType.PropertyFloat),
        field("bSafeZonePaused", "b_safe_zone_paused", RepLayoutCmdType.PropertyBool),
        field("AircraftStartTime", "aircraft_start_time", RepLayoutCmdType.PropertyFloat),
        field("bSkyTubesShuttingDown", "b_sky_tubes_shutting_down", RepLayoutCmdType.PropertyBool),
        field("SafeZonesStartTime", "safe_zones_start_time", RepLayoutCmdType.PropertyFloat),
        field("bSkyTubesDisabled", "b_sky_tubes_disabled", RepLayoutCmdType.PropertyBool),
        field("PlayersLeft", "players_left", RepLayoutCmdType.PropertyInt),
        field("ReplOverrideData", "repl_override_data", RepLayoutCmdType.Ignore),
        field("EndGameStartTime", "end_game_start_time", RepLayoutCmdType.PropertyFloat),
        field("TeamsLeft", "teams_left", RepLayoutCmdType.PropertyInt),
        field("EndGameKickPlayerTime", "end_game_kick_player_time", RepLayoutCmdType.PropertyFloat),
        field("ServerToClientPreloadList", "server_to_client_preload_list", RepLayoutCmdType.Ignore, element=ItemDefinition),
        field("ClientVehicleClassesToLoad", "client_vehicle_classes_to_load", RepLayoutCmdType.Ignore, element=ItemDefinition),
        field("bAllowUserPickedCosmeticBattleBus", "b_allow_user_picked_cosmetic_battle_bus", RepLayoutCmdType.PropertyBool),
        field("TeamFlightPaths", "team_flight_paths", RepLayoutCmdType.DynamicArray, element=Aircraft),
        field("StormCapState", "storm_cap_state", RepLayoutCmdType.Enum),
        field("FlightStartLocation", "flight_start_location", RepLayoutCmdType.PropertyVector100),
        field("FlightStartRotation", "flight_start_rotation", RepLayoutCmdType.PropertyRotator),
        field("FlightSpeed", "flight_speed", RepLayoutCmdType.PropertyFloat),
        field("TimeTillFlightEnd", "time_till_flight_end", RepLayoutCmdType.PropertyFloat),
        field("TimeTillDropStart", "time_till_drop_start", RepLayoutCmdType.PropertyFloat),
        field("TimeTillDropEnd", "time_till_drop_end", RepLayoutCmdType.PropertyFloat),
        field("UtcTimeStartedMatch", "utc_time_started_match", RepLayoutCmdType.Property, prop_type=FDateTime),
        field("SafeZonePhase", "safe_zone_phase", RepLayoutCmdType.PropertyByte),
        field("GamePhase", "game_phase", RepLayoutCmdType.Enum),
        field("Aircrafts", "aircrafts", RepLayoutCmdType.DynamicArray, element=ItemDefinition),
        field("bAircraftIsLocked", "b_aircraft_is_locked", RepLayoutCmdType.PropertyBool),
        field("LobbyAction", "lobby_action", RepLayoutCmdType.PropertyInt),
        field("WinningPlayerState", "winning_player_state", RepLayoutCmdType.Property, prop_type=ActorGuid),
        field("WinningPlayerList", "winning_player_list", RepLayoutCmdType.DynamicArray, element=RepLayoutCmdType.PropertyInt),
        field("WinningTeam", "winning_team", RepLayoutCmdType.PropertyUInt32),
        field("WinningScore", "winning_score", RepLayoutCmdType.PropertyUInt32),
        field("CurrentHighScore", "current_high_score", RepLayoutCmdType.PropertyUInt32),
        field("CurrentHighScoreTeam", "current_high_score_team", RepLayoutCmdType.PropertyUInt32),
        field("bStormReachedFinalPosition", "b_storm_reached_final_position", RepLayoutCmdType.PropertyBool),
        field("SpectateAPartyMemberAvailable", "spectate_a_party_member_available", RepLayoutCmdType.PropertyBool),
        field("HopRockDuration", "hop_rock_duration", RepLayoutCmdType.PropertyFloat),
        field("bIsLargeTeamGame", "b_is_large_team_game", RepLayoutCmdType.PropertyBool),
        field("ActiveTeamNums", "active_team_nums", RepLayoutCmdType.DynamicArray, element=NetworkGUID),
        field("AirCraftBehavior", "air_craft_behavior", RepLayoutCmdType.Enum),
        field("DefaultGliderRedeployCanRedeploy", "default_glider_redeploy_can_redeploy", RepLayoutCmdType.PropertyFloat),
        field("DefaultRedeployGliderLateralVelocityMult", "default_redeploy_glider_lateral_velocity_mult", RepLayoutCmdType.PropertyFloat),
        field("DefaultRedeployGliderHeightLimit", "default_redeploy_glider_height_limit", RepLayoutCmdType.PropertyFloat),
        field("EventTournamentRound", "event_tournament_round", RepLayoutCmdType.Enum),
        field("EventId", "event_id", RepLayoutCmdType.PropertyInt),
        field("PlayerBotsLeft", "player_bots_left", RepLayoutCmdType.PropertyInt),
        field("DefaultParachuteDeployTraceForGroundDistance", "default_parachute_deploy_trace_for_ground_distance", RepLayoutCmdType.PropertyFloat),
        field("DefaultRebootMachineHotfix", "default_reboot_machine_hotfix", RepLayoutCmdType.PropertyFloat),
        field("SignalInStormRegenSpeed", "signal_in_storm_regen_speed", RepLayoutCmdType.PropertyFloat),
        field("MutatorGenericInt", "mutator_generic_int", RepLayoutCmdType.PropertyUInt32),
        field("SignalInStormLostSpeed", "signal_in_storm_lost_speed", RepLayoutCmdType.PropertyFloat),
        field("StormCNDamageVulnerabilityLevel0", "storm_cn_damage_vulnerability_level0", RepLayoutCmdType.PropertyFloat),
        field("StormCNDamageVulnerabilityLevel1", "storm_cn_damage_vulnerability_level1", RepLayoutCmdType.PropertyFloat),
        field("StormCNDamageVulnerabilityLevel2", "storm_cn_damage_vulnerability_level2", RepLayoutCmdType.PropertyFloat),
        field("StormCNDamageVulnerabilityLevel3", "storm_cn_damage_vulnerability_level3", RepLayoutCmdType.PropertyFloat),
        field("bEnabled", "b_enabled", RepLayoutCmdType.PropertyBool),
        field("bConnectedToRoot", "b_connected_to_root", RepLayoutCmdType.PropertyBool),
        field("GameServerNodeType", "game_server_node_type", RepLayoutCmdType.Enum),
        field("VolumeManager", "volume_manager", RepLayoutCmdType.Ignore),
        field("TrackedCosmetics", "tracked_cosmetics", RepLayoutCmdType.DynamicArray, element=ItemDefinition),
        field("VariantUsageByCosmetic", "variant_usage_by_cosmetic", RepLayoutCmdType.DynamicArray, element=ItemDefinition),
        field("PrioritizedCosmeticIndices", "prioritized_cosmetic_indices", RepLayoutCmdType.DynamicArray, element=ItemDefinition),
        field("Mappings", "mappings", RepLayoutCmdType.DynamicArray, element=ItemDefinition),
        field("PlayersLoaded", "players_loaded", RepLayoutCmdType.PropertyFloat),
        field("bIsCustomMatch", "b_is_custom_match", RepLayoutCmdType.PropertyBool),
        field("bCraftingEnabled", "b_crafting_enabled", RepLayoutCmdType.PropertyBool),
        field("MatchStartTime", "match_start_time", RepLayoutCmdType.PropertyFloat),
        field("RealMatchStartTime", "real_match_start_time", RepLayoutCmdType.PropertyDouble),
    ]


@export_group("/Script/FortniteGame.FortRegenHealthSet", ParseMode.Full)
class HealthSet(ExportGroup):
    """/Script/FortniteGame.FortRegenHealthSet (HealthSet.cs)。"""

    FIELDS = [
        handle_field(0, "health_base_value", RepLayoutCmdType.PropertyFloat),
        handle_field(1, "health_current_value", RepLayoutCmdType.PropertyFloat),
        handle_field(3, "health_max_value", RepLayoutCmdType.PropertyFloat),
        handle_field(7, "health_unclamped_base_value", RepLayoutCmdType.PropertyFloat),
        handle_field(8, "health_unclamped_current_value", RepLayoutCmdType.PropertyFloat),
        handle_field(18, "shield_base_value", RepLayoutCmdType.PropertyFloat),
        handle_field(19, "shield_current_value", RepLayoutCmdType.PropertyFloat),
        handle_field(21, "shield_max_value", RepLayoutCmdType.PropertyFloat),
    ]


class BaseContainer(ExportGroup):
    """BaseContainer (BaseContainer.cs)。"""

    FIELDS = [
        field("bHidden", "b_hidden", RepLayoutCmdType.Ignore),
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("ForceMetadataRelevant", "force_metadata_relevant", RepLayoutCmdType.Ignore),
        field("bDestroyed", "b_destroyed", RepLayoutCmdType.PropertyBool),
        field("bInstantDeath", "b_instant_death", RepLayoutCmdType.PropertyBool),
        field("StaticMesh", "static_mesh", RepLayoutCmdType.Ignore),
        field("AltMeshIdx", "alt_mesh_idx", RepLayoutCmdType.Ignore),
        field("WeaponData", "weapon_data", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("BuildTime", "build_time", RepLayoutCmdType.Ignore),
        field("RepairTime", "repair_time", RepLayoutCmdType.Ignore),
        field("Health", "health", RepLayoutCmdType.PropertyUInt16),
        field("MaxHealth", "max_health", RepLayoutCmdType.PropertyUInt16),
        field("SearchedMesh", "searched_mesh", RepLayoutCmdType.Ignore),
        field("ReplicatedLootTier", "replicated_loot_tier", RepLayoutCmdType.PropertyInt),
        field("bAlreadySearched", "b_already_searched", RepLayoutCmdType.PropertyBool),
        field("BounceNormal", "bounce_normal", RepLayoutCmdType.PropertyVector),
        field("SearchAnimationCount", "search_animation_count", RepLayoutCmdType.PropertyUInt32),
        field("ChosenRandomUpgrade", "chosen_random_upgrade", RepLayoutCmdType.PropertyInt),
        field("bMirrored", "b_mirrored", RepLayoutCmdType.PropertyBool),
        field("ReplicatedDrawScale3D", "replicated_draw_scale3d", RepLayoutCmdType.PropertyVector100),
        field("bIsInitiallyBuilding", "b_is_initially_building", RepLayoutCmdType.PropertyBool),
        field("bForceReplayRollback", "b_force_replay_rollback", RepLayoutCmdType.PropertyBool),
    ]


@export_group("/Game/Building/ActorBlueprints/Containers/Tiered_Ammo_Athena.Tiered_Ammo_Athena_C", ParseMode.Debug)
class AmmoBox(BaseContainer):
    """/Game/Building/ActorBlueprints/Containers/Tiered_Ammo_Athena.Tiered_Ammo_Athena_C (AmmoBox.cs)。"""

    FIELDS = BaseContainer.FIELDS


@export_group("/Game/Building/ActorBlueprints/Containers/Tiered_Short_Ammo_3_Parent.Tiered_Short_Ammo_3_Parent_C", ParseMode.Debug)
class ShortAmmoBox(BaseContainer):
    """/Game/Building/ActorBlueprints/Containers/Tiered_Short_Ammo_3_Parent.Tiered_Short_Ammo_3_Parent_C (AmmoBox.cs)。"""

    FIELDS = BaseContainer.FIELDS


@export_group("/Game/Building/ActorBlueprints/Containers/Tiered_Chest_Athena.Tiered_Chest_Athena_C", ParseMode.Debug)
class Chest(BaseContainer):
    """/Game/Building/ActorBlueprints/Containers/Tiered_Chest_Athena.Tiered_Chest_Athena_C (Chest.cs)。"""

    FIELDS = BaseContainer.FIELDS + [
        field("bDestroyOnPlayerBuildingPlacement", "b_destroy_on_player_building_placement", RepLayoutCmdType.PropertyBool),
        field("ResourceType", "resource_type", RepLayoutCmdType.Enum),
        field("ProxyGameplayCueDamagePhysicalMagnitude", "proxy_gameplay_cue_damage_physical_magnitude", RepLayoutCmdType.Ignore),
        field("EffectContext", "effect_context", RepLayoutCmdType.Ignore),
    ]


@export_group("/Game/Building/ActorBlueprints/Containers/Creative_Tiered_Chest.Creative_Tiered_Chest_C", ParseMode.Debug)
class CreativeChest(Chest):
    """/Game/Building/ActorBlueprints/Containers/Creative_Tiered_Chest.Creative_Tiered_Chest_C (Chest.cs)。"""

    FIELDS = Chest.FIELDS + [
        field("SpawnItems", "spawn_items", RepLayoutCmdType.Property, prop_type=DebuggingObject),
        field("PrimaryAssetName", "primary_asset_name", RepLayoutCmdType.Property, prop_type=DebuggingObject),
        field("Quantity", "quantity", RepLayoutCmdType.Property, prop_type=DebuggingObject),
    ]


@export_group("/Game/Building/ActorBlueprints/Containers/Tiered_Chest_Athena_FactionChest_NoLocks.Tiered_Chest_Athena_FactionChest_NoLocks_C", ParseMode.Debug)
class FactionChest(BaseContainer):
    """/Game/Building/ActorBlueprints/Containers/Tiered_Chest_Athena_FactionChest_NoLocks.Tiered_Chest_Athena_FactionChest_NoLocks_C (Chest.cs)。"""

    FIELDS = BaseContainer.FIELDS + [
        field("bDestroyOnPlayerBuildingPlacement", "b_destroy_on_player_building_placement", RepLayoutCmdType.PropertyBool),
        field("T_Faction", "faction", RepLayoutCmdType.Enum),
    ]


@export_group("/Game/Building/ActorBlueprints/Containers/Barrel_FishingRod_Container_Athena.Barrel_FishingRod_Container_Athena_C", ParseMode.Debug)
class FishingBarrel(BaseContainer):
    """/Game/Building/ActorBlueprints/Containers/Barrel_FishingRod_Container_Athena.Barrel_FishingRod_Container_Athena_C (FishingBarrel.cs)。"""

    FIELDS = BaseContainer.FIELDS


@export_group("/Game/Abilities/Player/Generic/UtilityItems/B_Grenade_Tower_GIftBox_Athena", ParseMode.Debug)
class GiftBox(BaseContainer):
    """/Game/Abilities/Player/Generic/UtilityItems/B_Grenade_Tower_GIftBox_Athena (GiftBox.cs)。"""

    FIELDS = BaseContainer.FIELDS


@export_group("/Script/FortniteGame.FortMutatorListComponent", ParseMode.Ignore)
class MutatorList(ExportGroup):
    """/Script/FortniteGame.FortMutatorListComponent (MutatorList.cs)。"""

    FIELDS = [
        field("OverrideMode", "override_mode", RepLayoutCmdType.Property, prop_type=DebuggingObject),
    ]


@export_group("/Game/Spectating/BP_ReplayPC_Athena.BP_ReplayPC_Athena_C", ParseMode.Minimal)
@player_controller("BP_ReplayPC_Athena_C")
class ReplayPC(ExportGroup):
    """/Game/Spectating/BP_ReplayPC_Athena.BP_ReplayPC_Athena_C (ReplayPC.cs)。"""

    FIELDS = [
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("PlayerState", "player_state", RepLayoutCmdType.PropertyObject),
        field("SpawnLocation", "spawn_location", RepLayoutCmdType.PropertyVector),
    ]


@export_group("/Script/FortniteGame.FortPawn:NetMulticast_Athena_BatchedDamageCues", ParseMode.Full)
class BatchedDamageCues(ExportGroup):
    """/Script/FortniteGame.FortPawn:NetMulticast_Athena_BatchedDamageCues (BatchedDamageCues.cs)。"""

    FIELDS = [
        field("HitActor", "hit_actor", RepLayoutCmdType.PropertyObject),
        field("Location", "location", RepLayoutCmdType.PropertyVector100),
        field("Normal", "normal", RepLayoutCmdType.PropertyVectorNormal),
        field("Magnitude", "magnitude", RepLayoutCmdType.PropertyFloat),
        field("bWeaponActivate", "b_weapon_activate", RepLayoutCmdType.PropertyBool),
        field("bIsFatal", "b_is_fatal", RepLayoutCmdType.PropertyBool),
        field("bIsCritical", "b_is_critical", RepLayoutCmdType.PropertyBool),
        field("bIsShield", "b_is_shield", RepLayoutCmdType.PropertyBool),
        field("bIsShieldDestroyed", "b_is_shield_destroyed", RepLayoutCmdType.PropertyBool),
        field("bIsShieldApplied", "b_is_shield_applied", RepLayoutCmdType.PropertyBool),
        field("bIsBallistic", "b_is_ballistic", RepLayoutCmdType.PropertyBool),
        field("NonPlayerHitActor", "non_player_hit_actor", RepLayoutCmdType.PropertyObject),
        field("NonPlayerLocation", "non_player_location", RepLayoutCmdType.PropertyVector10),
        field("NonPlayerNormal", "non_player_normal", RepLayoutCmdType.PropertyVectorNormal),
        field("NonPlayerMagnitude", "non_player_magnitude", RepLayoutCmdType.PropertyFloat),
        field("NonPlayerbIsFatal", "non_playerb_is_fatal", RepLayoutCmdType.PropertyBool),
        field("NonPlayerbIsCritical", "non_playerb_is_critical", RepLayoutCmdType.PropertyBool),
        field("bIsValid", "b_is_valid", RepLayoutCmdType.PropertyBool),
    ]


@export_group("/Script/FortniteGame.FortGameplayEffectDeliveryActor:BroadcastExplosion", ParseMode.Debug)
class BroadcastExplosion(ExportGroup):
    """/Script/FortniteGame.FortGameplayEffectDeliveryActor:BroadcastExplosion (BroadcastExplosion.cs)。"""

    FIELDS = [
        field("HitActors", "hit_actors", RepLayoutCmdType.DynamicArray, element=RepLayoutCmdType.PropertyUInt32),
        field("HitResults", "hit_results", RepLayoutCmdType.DynamicArray, element=FHitResult),
    ]


@export_group("/Script/FortniteGame.FortBroadcastRemoteClientInfo:ClientRemotePlayerAddMapMarker", ParseMode.Debug)
class AddMapMarker(ExportGroup):
    """/Script/FortniteGame.FortBroadcastRemoteClientInfo:ClientRemotePlayerAddMapMarker (ClientRemote.cs)。"""

    FIELDS = [
        field("PlayerID", "player_id", RepLayoutCmdType.PropertyInt),
        field("InstanceID", "instance_id", RepLayoutCmdType.PropertyInt),
        field("Owner", "owner", RepLayoutCmdType.Ignore),
        field("WorldPosition", "world_position", RepLayoutCmdType.PropertyVector),
        field("WorldPositionOffset", "world_position_offset", RepLayoutCmdType.PropertyVector),
        field("WorldNormal", "world_normal", RepLayoutCmdType.PropertyVector),
        field("ItemDefinition", "item_definition", RepLayoutCmdType.PropertyObject),
        field("ItemCount", "item_count", RepLayoutCmdType.PropertyInt),
        field("MarkedActor", "marked_actor", RepLayoutCmdType.PropertyObject),
        field("bHasCustomDisplayInfo", "b_has_custom_display_info", RepLayoutCmdType.PropertyBool),
        field("DisplayName", "display_name", RepLayoutCmdType.Property, prop_type=FText),
        field("Icon", "icon", RepLayoutCmdType.PropertyString),
        field("R", "r", RepLayoutCmdType.PropertyFloat),
        field("G", "g", RepLayoutCmdType.PropertyFloat),
        field("B", "b", RepLayoutCmdType.PropertyFloat),
        field("A", "a", RepLayoutCmdType.PropertyFloat),
    ]


@export_group("/Script/FortniteGame.FortBroadcastRemoteClientInfo:ClientRemotePlayerRemoveMapMarker", ParseMode.Debug)
class RemoveMapMarker(ExportGroup):
    """/Script/FortniteGame.FortBroadcastRemoteClientInfo:ClientRemotePlayerRemoveMapMarker (ClientRemote.cs)。"""

    FIELDS = [
        field("PlayerID", "player_id", RepLayoutCmdType.PropertyInt),
        field("InstanceID", "instance_id", RepLayoutCmdType.PropertyInt),
    ]


@export_group("/Script/FortniteGame.FortBroadcastRemoteClientInfo:ClientRemotePlayerDamagedResourceBuilding", ParseMode.Debug)
class PlayerDamagedResourceBuilding(ExportGroup):
    """/Script/FortniteGame.FortBroadcastRemoteClientInfo:ClientRemotePlayerDamagedResourceBuilding (ClientRemote.cs)。"""

    FIELDS = [
        field("BuildingSMActor", "building_sm_actor", RepLayoutCmdType.PropertyInt),
        field("PotentialResourceType", "potential_resource_type", RepLayoutCmdType.Enum),
        field("PotentialResourceCount", "potential_resource_count", RepLayoutCmdType.PropertyInt),
        field("bDestroyed", "b_destroyed", RepLayoutCmdType.PropertyBool),
        field("bJustHitWeakspot", "b_just_hit_weakspot", RepLayoutCmdType.PropertyBool),
    ]


@export_group("/Script/FortniteGame.FortPlayerPawnAthena:FastSharedReplication", ParseMode.Debug)
class FastSharedReplication(ExportGroup):
    """/Script/FortniteGame.FortPlayerPawnAthena:FastSharedReplication (FastSharedReplication.cs)。"""

    FIELDS = [
        field("SharedRepMovement", "shared_rep_movement", RepLayoutCmdType.RepMovement),
    ]


class GameplayCue(ExportGroup):
    """GameplayCue (GameplayCue.cs)。"""

    FIELDS = [
        field("GameplayCueTag", "gameplay_cue_tag", RepLayoutCmdType.Property, prop_type=FGameplayTag),
        field("Parameters", "parameters", RepLayoutCmdType.Property, prop_type=FGameplayCueParameters),
        field("PredictionKey", "prediction_key", RepLayoutCmdType.Property, prop_type=FPredictionKey),
    ]


@export_group("/Script/FortniteGame.FortPawn:NetMulticast_InvokeGameplayCueAdded_WithParams", ParseMode.Ignore)
class GameplayCueAdded(GameplayCue):
    """/Script/FortniteGame.FortPawn:NetMulticast_InvokeGameplayCueAdded_WithParams (GameplayCue.cs)。"""

    FIELDS = GameplayCue.FIELDS


@export_group("/Script/FortniteGame.FortPawn:NetMulticast_InvokeGameplayCueExecuted_WithParams", ParseMode.Ignore)
class GameplayCueExecuted(GameplayCue):
    """/Script/FortniteGame.FortPawn:NetMulticast_InvokeGameplayCueExecuted_WithParams (GameplayCue.cs)。"""

    FIELDS = GameplayCue.FIELDS


@export_group("/Script/FortniteGame.FortPlayerStateAthena:Client_OnNewLevel", ParseMode.Debug)
class OnNewLevel(ExportGroup):
    """/Script/FortniteGame.FortPlayerStateAthena:Client_OnNewLevel (OnNewLevel.cs)。"""

    FIELDS = [
        field("NewLevel", "new_level", RepLayoutCmdType.PropertyInt),
    ]


@export_group("/Game/Athena/SafeZone/SafeZoneIndicator.SafeZoneIndicator_C", ParseMode.Normal)
class SafeZoneIndicator(ExportGroup):
    """/Game/Athena/SafeZone/SafeZoneIndicator.SafeZoneIndicator_C (SafeZoneIndicator.cs)。"""

    FIELDS = [
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("LastRadius", "last_radius", RepLayoutCmdType.PropertyFloat),
        field("NextRadius", "next_radius", RepLayoutCmdType.PropertyFloat),
        field("NextNextRadius", "next_next_radius", RepLayoutCmdType.PropertyFloat),
        field("LastCenter", "last_center", RepLayoutCmdType.PropertyVector100),
        field("NextCenter", "next_center", RepLayoutCmdType.PropertyVector100),
        field("NextNextCenter", "next_next_center", RepLayoutCmdType.PropertyVector100),
        field("SafeZoneStartShrinkTime", "safe_zone_start_shrink_time", RepLayoutCmdType.PropertyFloat),
        field("SafeZoneFinishShrinkTime", "safe_zone_finish_shrink_time", RepLayoutCmdType.PropertyFloat),
        field("bPausedForPreview", "b_paused_for_preview", RepLayoutCmdType.PropertyBool),
        field("MegaStormDelayTimeBeforeDestruction", "mega_storm_delay_time_before_destruction", RepLayoutCmdType.PropertyFloat),
        field("Radius", "radius", RepLayoutCmdType.PropertyFloat),
        field("PreviousRadius", "previous_radius", RepLayoutCmdType.PropertyFloat),
        field("CurrentPhase", "current_phase", RepLayoutCmdType.PropertyFloat),
        field("PreviousCenter", "previous_center", RepLayoutCmdType.PropertyVector100),
        field("Damage", "damage", RepLayoutCmdType.PropertyFloat),
        field("PhaseCount", "phase_count", RepLayoutCmdType.PropertyFloat),
        field("TimeRemainingWhenPhasePaused", "time_remaining_when_phase_paused", RepLayoutCmdType.PropertyFloat),
    ]


@export_group("/Script/FortniteGame.SpawnMachineRepData", ParseMode.Full)
class SpawnMachineRepData(ExportGroup):
    """/Script/FortniteGame.SpawnMachineRepData (SpawnMachineRepData.cs)。"""

    FIELDS = [
        field("Location", "location", RepLayoutCmdType.PropertyVector),
        field("SpawnMachineState", "spawn_machine_state", RepLayoutCmdType.Enum),
        field("SpawnMachineCooldownStartTime", "spawn_machine_cooldown_start_time", RepLayoutCmdType.PropertyFloat),
        field("SpawnMachineCooldownEndTime", "spawn_machine_cooldown_end_time", RepLayoutCmdType.PropertyFloat),
        field("SpawnMachineRepDataHandle", "spawn_machine_rep_data_handle", RepLayoutCmdType.PropertyInt),
    ]


@export_group("/Game/Athena/SupplyDrops/AthenaSupplyDrop.AthenaSupplyDrop_C", ParseMode.Full)
class SupplyDrop(ExportGroup):
    """/Game/Athena/SupplyDrops/AthenaSupplyDrop.AthenaSupplyDrop_C (SupplyDrop.cs)。"""

    FIELDS = [
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("ReplicatedMovement", "replicated_movement", RepLayoutCmdType.RepMovement, movement=RepMovementSpec(VectorQuantization.RoundWholeNumber, RotatorQuantization.ByteComponents, VectorQuantization.RoundWholeNumber)),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("bDestroyed", "b_destroyed", RepLayoutCmdType.PropertyBool),
        field("bEditorPlaced", "b_editor_placed", RepLayoutCmdType.PropertyBool),
        field("bInstantDeath", "b_instant_death", RepLayoutCmdType.PropertyBool),
        field("bHasSpawnedPickups", "b_has_spawned_pickups", RepLayoutCmdType.PropertyBool),
        field("Opened", "opened", RepLayoutCmdType.PropertyBool),
        field("BalloonPopped", "balloon_popped", RepLayoutCmdType.PropertyBool),
        field("FallSpeed", "fall_speed", RepLayoutCmdType.PropertyDouble),
        field("LandingLocation", "landing_location", RepLayoutCmdType.PropertyVector),
        field("FallHeight", "fall_height", RepLayoutCmdType.PropertyDouble),
    ]


@export_group("/Game/Athena/SupplyDrops/AthenaSupplyDropBalloon.AthenaSupplyDropBalloon_C", ParseMode.Ignore)
class SupplyDropBalloon(ExportGroup):
    """/Game/Athena/SupplyDrops/AthenaSupplyDropBalloon.AthenaSupplyDropBalloon_C (SupplyDropBalloon.cs)。"""

    FIELDS = [
        field("bHidden", "b_hidden", RepLayoutCmdType.PropertyBool),
        field("bCanBeDamaged", "b_can_be_damaged", RepLayoutCmdType.PropertyBool),
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("AttachParent", "attach_parent", RepLayoutCmdType.PropertyObject),
        field("LocationOffset", "location_offset", RepLayoutCmdType.Ignore),
        field("RelativeScale3D", "relative_scale3d", RepLayoutCmdType.PropertyVector100),
        field("AttachComponent", "attach_component", RepLayoutCmdType.PropertyObject),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("A", "a", RepLayoutCmdType.PropertyUInt32),
        field("B", "b", RepLayoutCmdType.PropertyUInt32),
        field("C", "c", RepLayoutCmdType.PropertyUInt32),
        field("D", "d", RepLayoutCmdType.PropertyUInt32),
        field("ReplicatedBuildingAttributeSet", "replicated_building_attribute_set", RepLayoutCmdType.PropertyObject),
        field("ReplicatedAbilitySystemComponent", "replicated_ability_system_component", RepLayoutCmdType.PropertyObject),
        field("bDestroyed", "b_destroyed", RepLayoutCmdType.PropertyBool),
        field("bEditorPlaced", "b_editor_placed", RepLayoutCmdType.PropertyBool),
        field("bInstantDeath", "b_instant_death", RepLayoutCmdType.PropertyBool),
        field("AttachmentPlacementBlockingActors", "attachment_placement_blocking_actors", RepLayoutCmdType.Ignore, element=RepLayoutCmdType.Ignore),
    ]


@export_group("/Game/Athena/Deimos/Spawners/RiftSpawners/AthenaSupplyDrop_DeimosSpawner.AthenaSupplyDrop_DeimosSpawner_C", ParseMode.Ignore)
class SupplyDropDeimosSpawner(ExportGroup):
    """/Game/Athena/Deimos/Spawners/RiftSpawners/AthenaSupplyDrop_DeimosSpawner.AthenaSupplyDrop_DeimosSpawner_C (SupplyDropDeimosSpawner.cs)。"""

    FIELDS = [
        field("ReplicatedMovement", "replicated_movement", RepLayoutCmdType.RepMovement),
        field("bEditorPlaced", "b_editor_placed", RepLayoutCmdType.PropertyBool),
    ]


@export_group("/Game/Athena/SupplyDrops/Llama/AthenaSupplyDrop_Llama.AthenaSupplyDrop_Llama_C", ParseMode.Full)
class SupplyDropLlama(ExportGroup):
    """/Game/Athena/SupplyDrops/Llama/AthenaSupplyDrop_Llama.AthenaSupplyDrop_Llama_C (SupplyDropLlama.cs)。"""

    FIELDS = [
        field("bHidden", "b_hidden", RepLayoutCmdType.PropertyBool),
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("ReplicatedMovement", "replicated_movement", RepLayoutCmdType.RepMovement),
        field("bDestroyed", "b_destroyed", RepLayoutCmdType.Ignore),
        field("bEditorPlaced", "b_editor_placed", RepLayoutCmdType.Ignore),
        field("bInstantDeath", "b_instant_death", RepLayoutCmdType.Ignore),
        field("bHasSpawnedPickups", "b_has_spawned_pickups", RepLayoutCmdType.PropertyBool),
        field("Looted", "looted", RepLayoutCmdType.PropertyBool),
        field("FinalDestination", "final_destination", RepLayoutCmdType.PropertyVector),
    ]


@export_group("/Script/FortniteGame.FortVehicleSeatComponent", ParseMode.Ignore)
class SeatComponent(ExportGroup):
    """/Script/FortniteGame.FortVehicleSeatComponent (BaseVehicle.cs)。"""

    FIELDS = [
        field("PlayerSlots", "player_slots", RepLayoutCmdType.Property, prop_type=DebuggingObject),
        field("PlayerEntryTime", "player_entry_time", RepLayoutCmdType.Property, prop_type=DebuggingObject),
        field("WeaponComponent", "weapon_component", RepLayoutCmdType.Property, prop_type=DebuggingObject),
    ]


@export_group("/Script/FortniteGame.FortVehicleSeatWeaponComponent", ParseMode.Ignore)
class WeaponSeatComponent(ExportGroup):
    """/Script/FortniteGame.FortVehicleSeatWeaponComponent (BaseVehicle.cs)。"""

    FIELDS = [
        field("bWeaponEquipped", "b_weapon_equipped", RepLayoutCmdType.PropertyBool),
        field("AmmoInClip", "ammo_in_clip", RepLayoutCmdType.Property, prop_type=DebuggingObject),
        field("LastFireTime", "last_fire_time", RepLayoutCmdType.PropertyFloat),
        field("bHasPrevious", "b_has_previous", RepLayoutCmdType.PropertyBool),
    ]


@export_group("/Game/Athena/DrivableVehicles/Meatball/Meatball_Large/MeatballVehicle_L.MeatballVehicle_L_C", ParseMode.Debug)
class Boat(ExportGroup):
    """/Game/Athena/DrivableVehicles/Meatball/Meatball_Large/MeatballVehicle_L.MeatballVehicle_L_C (Boat.cs)。"""

    FIELDS = [
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("Instigator", "instigator", RepLayoutCmdType.PropertyObject),
        field("ReplicatedMovement", "replicated_movement", RepLayoutCmdType.RepMovement, movement=RepMovementSpec(VectorQuantization.RoundWholeNumber, RotatorQuantization.ShortComponents, VectorQuantization.RoundTwoDecimals)),
        field("Location", "location", RepLayoutCmdType.PropertyVector),
        field("UpVector", "up_vector", RepLayoutCmdType.PropertyVector),
        field("ForwardVector", "forward_vector", RepLayoutCmdType.PropertyVector),
        field("SurfaceTypeVehicleOn", "surface_type_vehicle_on", RepLayoutCmdType.Enum),
        field("InitialOverlappingVehicles", "initial_overlapping_vehicles", RepLayoutCmdType.Property, prop_type=DebuggingObject),
    ]


class BaseExplosion(ExportGroup):
    """BaseExplosion (BaseExplosion.cs)。"""

    RPCS = [
        rpc("BroadcastExplosion", "/Script/FortniteGame.FortGameplayEffectDeliveryActor:BroadcastExplosion", attr="broadcast_explosion", prop_type=BroadcastExplosion, is_function=True),
    ]


class BaseProjectile(ExportGroup):
    """BaseProjectile (BaseProjectile.cs)。"""

    FIELDS = [
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("Owner", "owner", RepLayoutCmdType.Ignore),
        field("Instigator", "instigator", RepLayoutCmdType.PropertyObject),
        field("Team", "team", RepLayoutCmdType.PropertyByte),
        field("ReplicatedMovement", "replicated_movement", RepLayoutCmdType.RepMovement, movement=RepMovementSpec(VectorQuantization.RoundWholeNumber, RotatorQuantization.ByteComponents, VectorQuantization.RoundWholeNumber)),
        field("ReplicatedMaxSpeed", "replicated_max_speed", RepLayoutCmdType.PropertyFloat),
        field("GravityScale", "gravity_scale", RepLayoutCmdType.PropertyFloat),
    ]


class BaseRocketLauncherProjectile(BaseProjectile):
    """BaseRocketLauncherProjectile (BaseProjectile.cs)。"""

    FIELDS = BaseProjectile.FIELDS + [
        field("StopLocation", "stop_location", RepLayoutCmdType.PropertyVector),
        field("DecalLocation", "decal_location", RepLayoutCmdType.PropertyVector),
        field("PawnHitResult", "pawn_hit_result", RepLayoutCmdType.Property, prop_type=FHitResult),
        field("bHasExploded", "b_has_exploded", RepLayoutCmdType.PropertyBool),
        field("bIsBeingKilled", "b_is_being_killed", RepLayoutCmdType.PropertyBool),
    ]


class BaseWeapon(ExportGroup):
    """BaseWeapon (BaseWeapon.cs)。"""

    FIELDS = [
        field("bHidden", "b_hidden", RepLayoutCmdType.Ignore),
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("Owner", "owner", RepLayoutCmdType.Property, prop_type=ActorGuid),
        field("Instigator", "instigator", RepLayoutCmdType.PropertyObject),
        field("bIsEquippingWeapon", "b_is_equipping_weapon", RepLayoutCmdType.PropertyBool),
        field("bIsReloadingWeapon", "b_is_reloading_weapon", RepLayoutCmdType.PropertyBool),
        field("WeaponData", "weapon_data", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("LastFireTimeVerified", "last_fire_time_verified", RepLayoutCmdType.PropertyFloat),
        field("A", "a", RepLayoutCmdType.PropertyUInt32),
        field("B", "b", RepLayoutCmdType.PropertyUInt32),
        field("C", "c", RepLayoutCmdType.PropertyUInt32),
        field("D", "d", RepLayoutCmdType.PropertyUInt32),
        field("WeaponLevel", "weapon_level", RepLayoutCmdType.PropertyInt),
        field("AmmoCount", "ammo_count", RepLayoutCmdType.PropertyInt),
        field("AppliedAlterations", "applied_alterations", RepLayoutCmdType.DynamicArray, element=ItemDefinition),
        field("bIsMuzzleTraceNearWall", "b_is_muzzle_trace_near_wall", RepLayoutCmdType.PropertyBool),
    ]


@export_group("/Game/Weapons/FORT_BuildingTools/Blueprints/DefaultBuildingTool.DefaultBuildingTool_C", ParseMode.Debug)
class BuildingTool(BaseWeapon):
    """/Game/Weapons/FORT_BuildingTools/Blueprints/DefaultBuildingTool.DefaultBuildingTool_C (BuildingTool.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_BuildingTools/Blueprints/DefaultEditingTool.DefaultEditingTool_C", ParseMode.Debug)
class EditingTool(BaseWeapon):
    """/Game/Weapons/FORT_BuildingTools/Blueprints/DefaultEditingTool.DefaultEditingTool_C (BuildingTool.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Crossbows/Blueprints/B_TnTinaBow_Athena.B_TnTinaBow_Athena_C", ParseMode.Debug)
class Crossbow(BaseWeapon):
    """/Game/Weapons/FORT_Crossbows/Blueprints/B_TnTinaBow_Athena.B_TnTinaBow_Athena_C (Crossbow.cs)。"""

    FIELDS = BaseWeapon.FIELDS + [
        field("ChargeStatusPack", "charge_status_pack", RepLayoutCmdType.PropertyUInt16),
        field("bIsChargingWeapon", "b_is_charging_weapon", RepLayoutCmdType.PropertyBool),
    ]


@export_group("/Game/Weapons/FORT_Crossbows/Blueprints/B_Valentine_Crossbow_Athena.B_Valentine_Crossbow_Athena_C", ParseMode.Debug)
class ValentineCrossbow(Crossbow):
    """/Game/Weapons/FORT_Crossbows/Blueprints/B_Valentine_Crossbow_Athena.B_Valentine_Crossbow_Athena_C (Crossbow.cs)。"""

    FIELDS = Crossbow.FIELDS


@export_group("/Game/Weapons/FORT_Crossbows/Blueprints/B_DemonHunter_Crossbow_Athena.B_DemonHunter_Crossbow_Athena_C", ParseMode.Debug)
class DemonHunterCrossbow(Crossbow):
    """/Game/Weapons/FORT_Crossbows/Blueprints/B_DemonHunter_Crossbow_Athena.B_DemonHunter_Crossbow_Athena_C (Crossbow.cs)。"""

    FIELDS = Crossbow.FIELDS


@export_group("/Game/Athena/Items/Consumables/FloppingRabbit/B_FloppingRabbit_Weap_Athena.B_FloppingRabbit_Weap_Athena_C", ParseMode.Debug)
class FishingRod(BaseWeapon):
    """/Game/Athena/Items/Consumables/FloppingRabbit/B_FloppingRabbit_Weap_Athena.B_FloppingRabbit_Weap_Athena_C (FishingRod.cs)。"""

    FIELDS = BaseWeapon.FIELDS + [
        field("Projectile", "projectile", RepLayoutCmdType.Property, prop_type=NetworkGUID),
        field("Wire", "wire", RepLayoutCmdType.Property, prop_type=NetworkGUID),
        field("HideBobber", "hide_bobber", RepLayoutCmdType.PropertyBool),
        field("OneHandGrip", "one_hand_grip", RepLayoutCmdType.PropertyBool),
    ]


@export_group("/Game/Athena/Items/Consumables/FloppingRabbit/B_Athena_FloppingRabbit_Wire.B_Athena_FloppingRabbit_Wire_C", ParseMode.Debug)
class FishingRodWire(BaseWeapon):
    """/Game/Athena/Items/Consumables/FloppingRabbit/B_Athena_FloppingRabbit_Wire.B_Athena_FloppingRabbit_Wire_C (FishingRod.cs)。"""

    FIELDS = BaseWeapon.FIELDS + [
        field("ReplicatedMovement", "replicated_movement", RepLayoutCmdType.RepMovement, movement=RepMovementSpec(VectorQuantization.RoundWholeNumber, RotatorQuantization.ByteComponents, VectorQuantization.RoundWholeNumber)),
        field("Projectile", "projectile", RepLayoutCmdType.Property, prop_type=NetworkGUID),
        field("Projectile Actor", "projectile_actor", RepLayoutCmdType.Property, prop_type=NetworkGUID),
        field("PlayerPawn", "player_pawn", RepLayoutCmdType.Property, prop_type=NetworkGUID),
        field("CatchParticleOn", "catch_particle_on", RepLayoutCmdType.PropertyBool),
        field("Weapon", "weapon", RepLayoutCmdType.Property, prop_type=NetworkGUID),
    ]


@export_group("/Game/Athena/Items/Consumables/HappyGhost/B_HappyGhost_Athena.B_HappyGhost_Athena_C", ParseMode.Debug)
class Harpoon(BaseWeapon):
    """/Game/Athena/Items/Consumables/HappyGhost/B_HappyGhost_Athena.B_HappyGhost_Athena_C (FishingRod.cs)。"""

    FIELDS = BaseWeapon.FIELDS + [
        field("HideProj", "hide_proj", RepLayoutCmdType.PropertyBool),
    ]


@export_group("/Game/Athena/Items/Gameplay/Lotus/Mustache/B_Ranged_Lotus_Mustache.B_Ranged_Lotus_Mustache_C", ParseMode.Debug)
class BandageBazooka(BaseWeapon):
    """/Game/Athena/Items/Gameplay/Lotus/Mustache/B_Ranged_Lotus_Mustache.B_Ranged_Lotus_Mustache_C (Healing.cs)。"""

    FIELDS = BaseWeapon.FIELDS + [
        field("OverheatState", "overheat_state", RepLayoutCmdType.Enum),
    ]


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Minigun_Athena.B_Minigun_Athena_C", ParseMode.Debug)
class Minigun(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Minigun_Athena.B_Minigun_Athena_C (MachineGun.cs)。"""

    FIELDS = BaseWeapon.FIELDS + [
        field("ChargeStatusPack", "charge_status_pack", RepLayoutCmdType.Property, prop_type=DebuggingObject),
        field("CurrentSpinAudioComponent", "current_spin_audio_component", RepLayoutCmdType.Property, prop_type=NetworkGUID),
        field("bIsChargingWeapon", "b_is_charging_weapon", RepLayoutCmdType.PropertyBool),
        field("SpinVolumeMultiplier", "spin_volume_multiplier", RepLayoutCmdType.PropertyFloat),
        field("bPlayedSpinUpAudio", "b_played_spin_up_audio", RepLayoutCmdType.PropertyBool),
        field("bPlayedSpinDownAudio", "b_played_spin_down_audio", RepLayoutCmdType.PropertyBool),
        field("OverheatValue", "overheat_value", RepLayoutCmdType.PropertyUInt32),
        field("OverheatState", "overheat_state", RepLayoutCmdType.Enum),
    ]


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_LMG_SAW_Athena.B_Assault_LMG_SAW_Athena_C", ParseMode.Debug)
class LightMachineGun(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_LMG_SAW_Athena.B_Assault_LMG_SAW_Athena_C (MachineGun.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_MidasDrum_Athena.B_Assault_MidasDrum_Athena_C", ParseMode.Debug)
class MidasDrumGun(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_MidasDrum_Athena.B_Assault_MidasDrum_Athena_C (MachineGun.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Melee/Blueprints/B_Athena_Pickaxe_Generic.B_Athena_Pickaxe_Generic_C", ParseMode.Debug)
class Pickaxe(BaseWeapon):
    """/Game/Weapons/FORT_Melee/Blueprints/B_Athena_Pickaxe_Generic.B_Athena_Pickaxe_Generic_C (Melee.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Melee/Blueprints/B_Athena_Pickaxe_DualWield_Generic.B_Athena_Pickaxe_DualWield_Generic_C", ParseMode.Debug)
class DualWieldPickaxe(BaseWeapon):
    """/Game/Weapons/FORT_Melee/Blueprints/B_Athena_Pickaxe_DualWield_Generic.B_Athena_Pickaxe_DualWield_Generic_C (Melee.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_Light_PDW_Athena.B_Pistol_Light_PDW_Athena_C", ParseMode.Debug)
class LightPWD(BaseWeapon):
    """/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_Light_PDW_Athena.B_Pistol_Light_PDW_Athena_C (PDW.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_PDW_Athena_HighTier.B_Pistol_PDW_Athena_HighTier_C", ParseMode.Debug)
class HighTierPWD(BaseWeapon):
    """/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_PDW_Athena_HighTier.B_Pistol_PDW_Athena_HighTier_C (PDW.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_RapidFireSMG_Athena.B_Pistol_RapidFireSMG_Athena_C", ParseMode.Debug)
class RapidFireSMG(BaseWeapon):
    """/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_RapidFireSMG_Athena.B_Pistol_RapidFireSMG_Athena_C (PDW.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_PDW_Athena.B_Pistol_PDW_Athena_C", ParseMode.Debug)
class PistolPDW(BaseWeapon):
    """/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_PDW_Athena.B_Pistol_PDW_Athena_C (PDW.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_AutoHeavy_Athena_Supp_Child.B_Pistol_AutoHeavy_Athena_Supp_Child_C", ParseMode.Debug)
class SuppressedSMG(BaseWeapon):
    """/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_AutoHeavy_Athena_Supp_Child.B_Pistol_AutoHeavy_Athena_Supp_Child_C (PDW.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_Vigilante_Athena.B_Pistol_Vigilante_Athena_C", ParseMode.Debug)
class Pistol(BaseWeapon):
    """/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_Vigilante_Athena.B_Pistol_Vigilante_Athena_C (Pistol.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_Vigilante_Athena_HighTier.B_Pistol_Vigilante_Athena_HighTier_C", ParseMode.Debug)
class HighTierPistol(BaseWeapon):
    """/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_Vigilante_Athena_HighTier.B_Pistol_Vigilante_Athena_HighTier_C (Pistol.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_Vigilante_Supp_Athena.B_Pistol_Vigilante_Supp_Athena_C", ParseMode.Debug)
class SuppressedPistol(BaseWeapon):
    """/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_Vigilante_Supp_Athena.B_Pistol_Vigilante_Supp_Athena_C (Pistol.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_SingleActionRevolver_Athena.B_Pistol_SingleActionRevolver_Athena_C", ParseMode.Debug)
class Revolver(BaseWeapon):
    """/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_SingleActionRevolver_Athena.B_Pistol_SingleActionRevolver_Athena_C (Pistol.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_Revolver_Futuristic_Athena.B_Pistol_Revolver_Futuristic_Athena_C", ParseMode.Debug)
class RevolverHighTier(BaseWeapon):
    """/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_Revolver_Futuristic_Athena.B_Pistol_Revolver_Futuristic_Athena_C (Pistol.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Pistols/Blueprints/B_DualPistol_Athena.B_DualPistol_Athena_C", ParseMode.Debug)
class DualPistols(BaseWeapon):
    """/Game/Weapons/FORT_Pistols/Blueprints/B_DualPistol_Athena.B_DualPistol_Athena_C (Pistol.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_Handcannon_Athena.B_Pistol_Handcannon_Athena_C", ParseMode.Debug)
class HandCannon(BaseWeapon):
    """/Game/Weapons/FORT_Pistols/Blueprints/B_Pistol_Handcannon_Athena.B_Pistol_Handcannon_Athena_C (Pistol.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Auto_Athena.B_Assault_Auto_Athena_C", ParseMode.Debug)
class AutoAssaultRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Auto_Athena.B_Assault_Auto_Athena_C (Rifles.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_BurstBullpup_Athena.B_Assault_BurstBullpup_Athena_C", ParseMode.Debug)
class BurstAssaultRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_BurstBullpup_Athena.B_Assault_BurstBullpup_Athena_C (Rifles.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_BurstBullpup_Athena_HighTier.B_Assault_BurstBullpup_Athena_HighTier_C", ParseMode.Debug)
class HighTierBurstAssaultRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_BurstBullpup_Athena_HighTier.B_Assault_BurstBullpup_Athena_HighTier_C (Rifles.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Heavy_Athena.B_Assault_Heavy_Athena_C", ParseMode.Debug)
class HeavyAssaultRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Heavy_Athena.B_Assault_Heavy_Athena_C (Rifles.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Heavy_SR_Athena.B_Assault_Heavy_SR_Athena_C", ParseMode.Debug)
class HighTierHeavyAssaultRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Heavy_SR_Athena.B_Assault_Heavy_SR_Athena_C (Rifles.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Auto_Zoom_SR_Child_Athena.B_Assault_Auto_Zoom_SR_Child_Athena_C", ParseMode.Debug)
class AutoZoomAssaultRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Auto_Zoom_SR_Child_Athena.B_Assault_Auto_Zoom_SR_Child_Athena_C (Rifles.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Suppressed_Athena.B_Assault_Suppressed_Athena_C", ParseMode.Debug)
class SuppressedAssaultRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Suppressed_Athena.B_Assault_Suppressed_Athena_C (Rifles.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_PistolCaliber_AR_Athena.B_Assault_PistolCaliber_AR_Athena_C", ParseMode.Debug)
class TacticalAssaultRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_PistolCaliber_AR_Athena.B_Assault_PistolCaliber_AR_Athena_C (Rifles.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Surgical_Thermal_Athena.B_Assault_Surgical_Thermal_Athena_C", ParseMode.Debug)
class ThermalAssaultRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Surgical_Thermal_Athena.B_Assault_Surgical_Thermal_Athena_C (Rifles.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_InfantryRifle_Athena.B_Assault_InfantryRifle_Athena_C", ParseMode.Debug)
class InfantryAssaultRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_InfantryRifle_Athena.B_Assault_InfantryRifle_Athena_C (Rifles.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_InfantryRifle_SR_Athena.B_Assault_InfantryRifle_SR_Athena_C", ParseMode.Debug)
class HighTierInfantryAssaultRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_InfantryRifle_SR_Athena.B_Assault_InfantryRifle_SR_Athena_C (Rifles.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Surgical_Athena.B_Assault_Surgical_Athena_C", ParseMode.Debug)
class ScopedAssaultRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/Assault/B_Assault_Surgical_Athena.B_Assault_Surgical_Athena_C (Rifles.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_RocketLauncher_Generic_Athena.B_RocketLauncher_Generic_Athena_C", ParseMode.Debug)
class RocketLauncher(BaseWeapon):
    """/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_RocketLauncher_Generic_Athena.B_RocketLauncher_Generic_Athena_C (RocketLauncher.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_RocketLauncher_Generic_Athena_HighTier.B_RocketLauncher_Generic_Athena_HighTier_C", ParseMode.Debug)
class HighTierRocketLauncher(BaseWeapon):
    """/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_RocketLauncher_Generic_Athena_HighTier.B_RocketLauncher_Generic_Athena_HighTier_C (RocketLauncher.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_Prj_Pumpkin_RPG_Athena_LowTier.B_Prj_Pumpkin_RPG_Athena_LowTier_C", ParseMode.Debug)
class PumpkinLauncher(BaseWeapon):
    """/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_Prj_Pumpkin_RPG_Athena_LowTier.B_Prj_Pumpkin_RPG_Athena_LowTier_C (RocketLauncher.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_Launcher_Pumpkin_RPG_Athena.B_Launcher_Pumpkin_RPG_Athena_C", ParseMode.Debug)
class HighTierPumpkinLauncher(BaseWeapon):
    """/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_Launcher_Pumpkin_RPG_Athena.B_Launcher_Pumpkin_RPG_Athena_C (RocketLauncher.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_RocketLauncher_Military_Athena.B_RocketLauncher_Military_Athena_C", ParseMode.Debug)
class QuadLauncher(BaseWeapon):
    """/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_RocketLauncher_Military_Athena.B_RocketLauncher_Military_Athena_C (RocketLauncher.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_GrenadeLaunchers/Blueprints/B_GrenadeLauncher_Prox_Athena.B_GrenadeLauncher_Prox_Athena_C", ParseMode.Debug)
class ProximityLauncher(BaseWeapon):
    """/Game/Weapons/FORT_GrenadeLaunchers/Blueprints/B_GrenadeLauncher_Prox_Athena.B_GrenadeLauncher_Prox_Athena_C (RocketLauncher.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_Prj_Ranged_Rocket_Athena.B_Prj_Ranged_Rocket_Athena_C", ParseMode.Debug)
class RocketLauncherProjectile(BaseRocketLauncherProjectile):
    """/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_Prj_Ranged_Rocket_Athena.B_Prj_Ranged_Rocket_Athena_C (RocketLauncher.cs)。"""

    FIELDS = BaseRocketLauncherProjectile.FIELDS


@export_group("/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_Prj_Ranged_Rocket_Athena_LowTier.B_Prj_Ranged_Rocket_Athena_LowTier_C", ParseMode.Debug)
class LowTierRocketLauncherProjectile(BaseRocketLauncherProjectile):
    """/Game/Weapons/FORT_RocketLaunchers/Blueprints/B_Prj_Ranged_Rocket_Athena_LowTier.B_Prj_Ranged_Rocket_Athena_LowTier_C (RocketLauncher.cs)。"""

    FIELDS = BaseRocketLauncherProjectile.FIELDS


@export_group("/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_Heavy_Athena.B_Shotgun_Heavy_Athena_C", ParseMode.Debug)
class HeavyShotgun(BaseWeapon):
    """/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_Heavy_Athena.B_Shotgun_Heavy_Athena_C (Shotgun.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_Standard_Athena.B_Shotgun_Standard_Athena_C", ParseMode.Debug)
class StandardShotgun(BaseWeapon):
    """/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_Standard_Athena.B_Shotgun_Standard_Athena_C (Shotgun.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_Standard_TopTier_Athena.B_Shotgun_Standard_TopTier_Athena_C", ParseMode.Debug)
class HightTierStandardShotgun(BaseWeapon):
    """/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_Standard_TopTier_Athena.B_Shotgun_Standard_TopTier_Athena_C (Shotgun.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_HighSemiAuto_Athena.B_Shotgun_HighSemiAuto_Athena_C", ParseMode.Debug)
class HighSemiAutoShotgun(BaseWeapon):
    """/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_HighSemiAuto_Athena.B_Shotgun_HighSemiAuto_Athena_C (Shotgun.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_Combat_Athena.B_Shotgun_Combat_Athena_C", ParseMode.Debug)
class CombatShotgun(BaseWeapon):
    """/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_Combat_Athena.B_Shotgun_Combat_Athena_C (Shotgun.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_AutoDrum_Athena.B_Shotgun_AutoDrum_Athena_C", ParseMode.Debug)
class DrumShotgun(BaseWeapon):
    """/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_AutoDrum_Athena.B_Shotgun_AutoDrum_Athena_C (Shotgun.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_Break_Athena.B_Shotgun_Break_Athena_C", ParseMode.Debug)
class DoubleBarrelShotgun(BaseWeapon):
    """/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_Break_Athena.B_Shotgun_Break_Athena_C (Shotgun.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/B_Rifle_Sniper_Athena.B_Rifle_Sniper_Athena_C", ParseMode.Debug)
class SniperRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/B_Rifle_Sniper_Athena.B_Rifle_Sniper_Athena_C (Sniper.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/B_Rifle_Sniper_Athena_HighTier.B_Rifle_Sniper_Athena_HighTier_C", ParseMode.Debug)
class HighTierSniperRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/B_Rifle_Sniper_Athena_HighTier.B_Rifle_Sniper_Athena_HighTier_C (Sniper.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/B_Rifle_NoScope_Athena.B_Rifle_NoScope_Athena_C", ParseMode.Debug)
class NoScopeSniperRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/B_Rifle_NoScope_Athena.B_Rifle_NoScope_Athena_C (Sniper.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/B_Rifle_Sniper_Suppressed_Athena.B_Rifle_Sniper_Suppressed_Athena_C", ParseMode.Debug)
class SuppressedSniperRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/B_Rifle_Sniper_Suppressed_Athena.B_Rifle_Sniper_Suppressed_Athena_C (Sniper.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Rifles/Blueprints/B_Rifle_Sniper_Heavy_Athena.B_Rifle_Sniper_Heavy_Athena_C", ParseMode.Debug)
class HeavySniperRifle(BaseWeapon):
    """/Game/Weapons/FORT_Rifles/Blueprints/B_Rifle_Sniper_Heavy_Athena.B_Rifle_Sniper_Heavy_Athena_C (Sniper.cs)。"""

    FIELDS = BaseWeapon.FIELDS


@export_group("/Game/Weapons/FORT_Sniper/Blueprints/B_Prj_Bullet_Sniper.B_Prj_Bullet_Sniper_C", ParseMode.Debug)
class SniperRifleBullet(BaseProjectile):
    """/Game/Weapons/FORT_Sniper/Blueprints/B_Prj_Bullet_Sniper.B_Prj_Bullet_Sniper_C (Sniper.cs)。"""

    FIELDS = BaseProjectile.FIELDS + [
        field("FireStartLoc", "fire_start_loc", RepLayoutCmdType.PropertyVector10),
        field("PawnHitResult", "pawn_hit_result", RepLayoutCmdType.Property, prop_type=FHitResult),
    ]


@export_group("/Game/Athena/Items/Traps/TrapTool_ContextTrap_Athena.TrapTool_ContextTrap_Athena_C", ParseMode.Debug)
class Trap(BaseWeapon):
    """/Game/Athena/Items/Traps/TrapTool_ContextTrap_Athena.TrapTool_ContextTrap_Athena_C (Trap.cs)。"""

    FIELDS = BaseWeapon.FIELDS + [
        field("ItemDefinition", "item_definition", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("ContextTrapItemDefinition", "context_trap_item_definition", RepLayoutCmdType.Property, prop_type=ItemDefinition),
    ]


@export_group("/Game/Athena/Items/Traps/Launchpad/BluePrint/Trap_Floor_Player_Launch_Pad.Trap_Floor_Player_Launch_Pad_C", ParseMode.Debug)
class LaunchPad(ExportGroup):
    """/Game/Athena/Items/Traps/Launchpad/BluePrint/Trap_Floor_Player_Launch_Pad.Trap_Floor_Player_Launch_Pad_C (Trap.cs)。"""

    FIELDS = [
        field("RemoteRole", "remote_role", RepLayoutCmdType.Ignore),
        field("Role", "role", RepLayoutCmdType.Ignore),
        field("OwnerPersistentID", "owner_persistent_id", RepLayoutCmdType.PropertyUInt32),
        field("bPlayerPlaced", "b_player_placed", RepLayoutCmdType.PropertyBool),
        field("TeamIndex", "team_index", RepLayoutCmdType.Enum),
        field("TrapData", "trap_data", RepLayoutCmdType.Property, prop_type=ItemDefinition),
        field("AttachedTo", "attached_to", RepLayoutCmdType.PropertyInt),
    ]


@class_net_cache("FortBroadcastRemoteClientInfo_ClassNetCache", ParseMode.Ignore)
class FortBroadcastRemoteClientInfoCache(object):
    """FortBroadcastRemoteClientInfo_ClassNetCache (FortBroadcastRemoteClientInfo.cs)。"""

    RPCS = [
        rpc("ClientRemotePlayerAddMapMarker", "/Script/FortniteGame.FortBroadcastRemoteClientInfo:ClientRemotePlayerAddMapMarker", attr="add_map_marker", prop_type=AddMapMarker, is_function=True),
        rpc("ClientRemotePlayerRemoveMapMarker", "/Script/FortniteGame.FortBroadcastRemoteClientInfo:ClientRemotePlayerRemoveMapMarker", attr="remove_map_marker", prop_type=RemoveMapMarker, is_function=True),
        rpc("ClientRemotePlayerDamagedResourceBuilding", "/Script/FortniteGame.FortBroadcastRemoteClientInfo:ClientRemotePlayerDamagedResourceBuilding", attr="player_damaged_resource_building", prop_type=PlayerDamagedResourceBuilding, is_function=True),
    ]


@class_net_cache("FortInventory_ClassNetCache")
class FortInventoryCache(object):
    """FortInventory_ClassNetCache (FortInventory.cs)。"""

    RPCS = [
        rpc("Inventory", "/Script/FortniteGame.FortInventory", attr="inventory", prop_type=FortInventory),
    ]


@class_net_cache("FortPlayerStateAthena_ClassNetCache", ParseMode.Debug)
class FortPlayerStateCache(object):
    """FortPlayerStateAthena_ClassNetCache (FortPlayerState.cs)。"""

    RPCS = [
        rpc("Client_OnNewLevel", "/Script/FortniteGame.FortPlayerStateAthena:Client_OnNewLevel", attr="client_on_new_level", prop_type=OnNewLevel, is_function=True),
    ]


@class_net_cache("FortTeamPrivateInfo_ClassNetCache", ParseMode.Debug)
class FortTeamPrivateInfoCache(object):
    """FortTeamPrivateInfo_ClassNetCache (FortTeamPrivateInfo.cs)。"""

    RPCS = [
        rpc("LatentTeamRepData", "/Script/FortniteGame.FortTeamPrivateInfo", attr="latent_team_rep_data"),
        rpc("RepData", "/Script/FortniteGame.FortTeamPrivateInfo", attr="rep_data"),
    ]


@class_net_cache("Athena_GameState_C_ClassNetCache", ParseMode.Minimal)
class GameStateCache(object):
    """Athena_GameState_C_ClassNetCache (GameState.cs)。"""

    RPCS = [
        rpc("ActiveGameplayModifiers", "/Script/FortniteGame.ActiveGameplayModifier", attr="active_gameplay_modifiers", prop_type=ActiveGameplayModifier, enable_property_checksum=False),
        rpc("GameMemberInfoArray", "/Script/FortniteGame.GameMemberInfo", attr="game_member_info_array", prop_type=GameMemberInfo, enable_property_checksum=False),
        rpc("CurrentPlaylistInfo", "CurrentPlaylistInfo", attr="current_playlist_info", prop_type=PlaylistInfo, is_custom_struct=True),
        rpc("SpawnMachineRepData", "/Script/FortniteGame.SpawnMachineRepData", attr="spawn_machine_rep_data", prop_type=SpawnMachineRepData, enable_property_checksum=False),
    ]


@class_net_cache("PlayerPawn_Athena_C_ClassNetCache", ParseMode.Full)
class PlayerPawnCache(object):
    """PlayerPawn_Athena_C_ClassNetCache (PlayerPawn.cs)。"""

    RPCS = [
        rpc("ClientObservedStats", "/Script/FortniteGame.FortClientObservedStat", attr="client_observed_stats", prop_type=FortClientObservedStat, enable_property_checksum=False),
        rpc("NetMulticast_Athena_BatchedDamageCues", "/Script/FortniteGame.FortPawn:NetMulticast_Athena_BatchedDamageCues", attr="damage_cues", prop_type=BatchedDamageCues, is_function=True),
        rpc("NetMulticast_InvokeGameplayCueAdded_WithParams", "/Script/FortniteGame.FortPawn:NetMulticast_InvokeGameplayCueAdded_WithParams", attr="invoke_gameplay_cue_added", prop_type=GameplayCue, is_function=True),
    ]


@class_net_cache("B_Prj_Meatball_Missile_C_ClassNetCache", ParseMode.Debug)
class BoatMissleClassNetCache(BaseExplosion):
    """B_Prj_Meatball_Missile_C_ClassNetCache (Boat.cs)。"""

    RPCS = BaseExplosion.RPCS


@class_net_cache("B_Prj_Athena_FragGrenade_C_ClassNetCache", ParseMode.Debug)
class FragGrenadeCache(BaseExplosion):
    """B_Prj_Athena_FragGrenade_C_ClassNetCache (FragGrenade.cs)。"""

    RPCS = BaseExplosion.RPCS


@class_net_cache("B_Prj_Ranged_Rocket_Athena_C_ClassNetCache", ParseMode.Debug)
class RocketLauncherProjectileClassNetCache(BaseExplosion):
    """B_Prj_Ranged_Rocket_Athena_C_ClassNetCache (RocketLauncher.cs)。"""

    RPCS = BaseExplosion.RPCS


@class_net_cache("B_Prj_Ranged_Rocket_Athena_LowTier_C_ClassNetCache", ParseMode.Debug)
class LowTierRocketLauncherProjectileClassNetCache(BaseExplosion):
    """B_Prj_Ranged_Rocket_Athena_LowTier_C_ClassNetCache (RocketLauncher.cs)。"""

    RPCS = BaseExplosion.RPCS

