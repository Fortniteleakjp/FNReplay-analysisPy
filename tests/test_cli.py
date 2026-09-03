"""CLI のテスト。"""

from fnreplay.cli import print_summary
from fnreplay.fortnite.models import FortniteReplay
from fnreplay.unreal.enums import EngineNetworkVersionHistory


def test_print_summary_accepts_unknown_engine_network_version(capsys) -> None:
    """未対応のエンジンネットワークバージョンでも概要を表示できる。"""
    replay = FortniteReplay()
    replay.header.engine_network_version = 44

    print_summary(replay, elapsed=0.1)

    output = capsys.readouterr().out
    assert "エンジンバージョン: 未対応 (44)" in output


def test_print_summary_uses_enum_name_for_known_engine_network_version(capsys) -> None:
    """対応済みのエンジンネットワークバージョンは従来どおり名前を表示する。"""
    replay = FortniteReplay()
    replay.header.engine_network_version = EngineNetworkVersionHistory.CustomExports

    print_summary(replay, elapsed=0.1)

    output = capsys.readouterr().out
    assert "エンジンバージョン: CustomExports" in output
