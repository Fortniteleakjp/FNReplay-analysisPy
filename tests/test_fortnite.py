"""Fortnite 固有の解析処理のテスト (C# 版 FortniteReplayReader.Test からの移植)。"""

from __future__ import annotations

import pytest

from fnreplay.fortnite.exports.handwritten import PlayerNameData
from fnreplay.fortnite.reader import FortniteReplayReader, milliseconds_to_timestamp
from fnreplay.unreal.archives import BinaryReader
from fnreplay.unreal.enums import EngineNetworkVersionHistory
from fnreplay.unreal.models import EventInfo
from fnreplay.unreal.paths import clean_path_suffix, remove_all_path_prefixes, remove_path_prefix


# ---------------------------------------------------------------------------
# パス操作
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        ("LF_7x12_Parent2_2", "LF_7x12_Parent"),
        ("LF_Athena_POI_25x31_5", "LF_Athena_POI_25x"),
        ("Apollo_Tree_RedAlder248", "Apollo_Tree_RedAlder"),
        ("Apllo_Tree_Birch_Large175", "Apllo_Tree_Birch_Large"),
        ("FortTeamPrivateInfo_ClassNetCache", "FortTeamPrivateInfo_ClassNetCache"),
    ],
)
def test_clean_path_suffix(value: str, expected: str) -> None:
    assert clean_path_suffix(value) == expected


@pytest.mark.parametrize(
    "value,to_remove,expected",
    [
        ("Default__FortPickupAthena", "Default__", "FortPickupAthena"),
        ("Default__AthenaAircraft_C", "Default__", "AthenaAircraft_C"),
        ("FortTeamPrivateInfo_ClassNetCache", "Default__", "FortTeamPrivateInfo_ClassNetCache"),
        ("DamageSet", "Default__", "DamageSet"),
        ("FortTeamPrivateInfo_ClassNetCache", "FortTeamPrivateInfo", "_ClassNetCache"),
        ("DamageSet", "Damage", "Set"),
        ("DamageSet", "", "DamageSet"),
    ],
)
def test_remove_path_prefix(value: str, to_remove: str, expected: str) -> None:
    assert remove_path_prefix(value, to_remove) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (
            "/Game/Athena/Apollo/Environments/BuildingActors/Rocks/Prop_RockPile_06.Prop_RockPile_06_C",
            "Prop_RockPile_06_C",
        ),
        (
            "/Game/Building/ActorBlueprints/Player/Wood/L1/PBWA_W1_StairW.PBWA_W1_StairW_C",
            "PBWA_W1_StairW_C",
        ),
        (
            "/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_Standard_Athena/B_Shotgun_Standard_Athena_C",
            "/Game/Weapons/FORT_Shotguns/Blueprints/B_Shotgun_Standard_Athena/B_Shotgun_Standard_Athena_C",
        ),
    ],
)
def test_remove_all_path_prefixes(value: str, expected: str) -> None:
    assert remove_all_path_prefixes(value) == expected


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "milliseconds,expected", [(77321, "01:17"), (115119, "01:55"), (522640, "08:42")]
)
def test_milliseconds_to_timestamp(milliseconds: int, expected: str) -> None:
    assert milliseconds_to_timestamp(milliseconds) == expected


def test_branch_parsing() -> None:
    reader = FortniteReplayReader()
    reader.branch = "++PUBG+Release-11.11"
    assert (reader.major, reader.minor) == (0, 0)
    reader.branch = "++Fortnite+Release-5.41"
    assert (reader.major, reader.minor) == (5, 41)
    reader.branch = "++Fortnite+Release-7.10"
    assert (reader.major, reader.minor) == (7, 10)
    reader.branch = "++Fortnite+Release-11.11"
    assert (reader.major, reader.minor) == (11, 11)
    reader.branch = "++Fortnite+Release-999.999"
    assert (reader.major, reader.minor) == (999, 999)


# ---------------------------------------------------------------------------
# イベント
# ---------------------------------------------------------------------------


def test_parse_match_stats() -> None:
    raw = bytes([
        0x00, 0x00, 0x00, 0x00, 0xF1, 0xF0, 0x70, 0x3E, 0x02, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x3A, 0x01, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x52, 0x01, 0x00, 0x00, 0x02, 0x04, 0x00, 0x00,
        0x1C, 0x00, 0x00, 0x00, 0x0A, 0x00, 0x00, 0x00, 0xA5, 0x3D, 0x00, 0x00,
    ])
    archive = BinaryReader(raw)
    stats = FortniteReplayReader().parse_match_stats(archive, EventInfo())

    assert archive.at_end()
    assert not archive.is_error
    assert stats.eliminations == 0
    assert stats.assists == 2
    assert stats.revives == 0
    assert round(stats.accuracy * 100) == 24
    assert stats.weapon_damage == 314
    assert stats.other_damage == 14
    assert stats.damage_to_players == 328
    assert stats.damage_taken == 338
    assert stats.damage_to_structures == 1026
    assert stats.materials_gathered == 28
    assert stats.materials_used == 10
    assert stats.total_traveled == 15781


@pytest.mark.parametrize(
    "raw,position,total_players",
    [
        (
            bytes([0x00, 0x00, 0x00, 0x00, 0x23, 0x00, 0x00, 0x00, 0x60, 0x00, 0x00, 0x00]),
            35,
            96,
        ),
        (
            bytes([0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x63, 0x00, 0x00, 0x00]),
            2,
            99,
        ),
    ],
)
def test_parse_team_stats(raw: bytes, position: int, total_players: int) -> None:
    archive = BinaryReader(raw)
    stats = FortniteReplayReader().parse_team_stats(archive, EventInfo())
    assert archive.at_end()
    assert not archive.is_error
    assert stats.position == position
    assert stats.total_players == total_players


@pytest.mark.parametrize(
    "raw,is_player,player_name",
    [
        (bytes([0x19, 0xFB, 0x01, 0x00, 0x00, 0x00, 0x00]), True, ""),
        (bytes([0x19, 0xFB, 0x00, 0x00, 0x00, 0x00, 0x00]), False, ""),
        (
            bytes([
                0x19, 0xFB, 0x00, 0x0C, 0x00, 0x00, 0x00, 0x66, 0x69, 0x6C, 0x69, 0x70,
                0x69, 0x6E, 0x68, 0x30, 0x73, 0x70, 0x00,
            ]),
            False,
            "filipinh0sp",
        ),
        (
            bytes([
                0x19, 0xFB, 0x01, 0x07, 0x00, 0x00, 0x00, 0x4E, 0x68, 0x66, 0x6B, 0x60,
                0x6A, 0x00,
            ]),
            True,
            "Shiqan",
        ),
    ],
)
def test_player_name_data(raw: bytes, is_player: bool, player_name: str) -> None:
    archive = BinaryReader(raw)
    data = PlayerNameData(archive)
    assert archive.at_end()
    assert not archive.is_error
    assert data.handle == 25
    assert data.is_player is is_player
    assert data.decoded_name == player_name


@pytest.mark.parametrize(
    "raw,branch,eliminated,eliminator",
    [
        (
            bytes([
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x0D, 0x00, 0x00, 0x00, 0x53, 0x6F, 0x75, 0x74, 0x68, 0x48, 0x75, 0x6E,
                0x74, 0x65, 0x72, 0x5A, 0x00, 0x0A, 0x00, 0x00, 0x00, 0x49, 0x74, 0x5A,
                0x4D, 0x65, 0x65, 0x6E, 0x64, 0x59, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00,
            ]),
            "++Fortnite+Release-4.0",
            "SouthHunterZ",
            "ItZMeendY",
        ),
        (
            bytes([
                0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x3F, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80,
                0x3F, 0x00, 0x00, 0x80, 0x3F, 0x00, 0x00, 0x80, 0x3F, 0x0D, 0x00, 0x00,
                0x00, 0x73, 0x69, 0x6C, 0x76, 0x65, 0x72, 0x63, 0x72, 0x65, 0x73, 0x74,
                0x79, 0x00, 0x0A, 0x00, 0x00, 0x00, 0x46, 0x72, 0x65, 0x7A, 0x65, 0x72,
                0x33, 0x35, 0x33, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00,
            ]),
            "++Fortnite+Release-4.3",
            "silvercresty",
            "Frezer353",
        ),
    ],
)
def test_parse_elimination(
    raw: bytes, branch: str, eliminated: str, eliminator: str
) -> None:
    archive = BinaryReader(raw)
    archive.engine_network_version = (
        EngineNetworkVersionHistory.HISTORY_NETEXPORT_SERIALIZATION
    )
    reader = FortniteReplayReader()
    reader.branch = branch

    elimination = reader.parse_elimination(archive, EventInfo(start_time=77321))

    assert archive.at_end()
    assert not archive.is_error
    assert elimination.eliminated == eliminated
    assert elimination.eliminator == eliminator
    assert elimination.time == "01:17"
