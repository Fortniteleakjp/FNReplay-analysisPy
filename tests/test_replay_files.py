"""実際のリプレイファイルを使ったエンドツーエンドのテスト。

環境変数 ``FNREPLAY_TEST_REPLAYS`` に ``.replay`` を含むディレクトリを指定すると実行される。
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import fnreplay
from fnreplay import ParseMode

_REPLAY_DIR = os.environ.get("FNREPLAY_TEST_REPLAYS")


def _replay_files() -> list[Path]:
    if not _REPLAY_DIR:
        return []
    return sorted(Path(_REPLAY_DIR).glob("*.replay"))


requires_replays = pytest.mark.skipif(
    not _replay_files(), reason="FNREPLAY_TEST_REPLAYS が設定されていません"
)


@requires_replays
@pytest.mark.parametrize("path", _replay_files(), ids=lambda p: p.name)
def test_read_replay_minimal(path: Path) -> None:
    replay = fnreplay.read_replay(path, parse_mode=ParseMode.Minimal)

    assert replay.info.length_in_ms > 0
    assert replay.header.branch.startswith("++Fortnite")
    assert replay.player_data, "プレイヤー情報が取得できていません"
    assert replay.eliminations, "撃破イベントが取得できていません"

    for elimination in replay.eliminations:
        assert elimination.time
        assert elimination.eliminated is not None
        assert elimination.eliminator is not None


@requires_replays
def test_read_replay_full() -> None:
    path = _replay_files()[0]
    replay = fnreplay.read_replay(path, parse_mode=ParseMode.Full)

    # Full では位置情報まで取得できる
    assert any(player.locations for player in replay.player_data)
