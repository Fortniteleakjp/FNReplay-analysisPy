"""コマンドラインインターフェース。

使い方::

    python -m fnreplay match.replay
    python -m fnreplay match.replay --mode full --json out.json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from . import __version__
from .compression import use_native_oodle
from .fortnite import FortniteReplay, FortniteReplayReader
from .unreal.enums import ParseMode

_MODES = {
    "events": ParseMode.EventsOnly,
    "minimal": ParseMode.Minimal,
    "normal": ParseMode.Normal,
    "full": ParseMode.Full,
    "debug": ParseMode.Debug,
}


def to_jsonable(value: Any) -> Any:
    """解析結果を JSON にできる形へ変換する。"""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {k: to_jsonable(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return to_jsonable(to_dict())
    if hasattr(value, "__dict__"):
        return {k: to_jsonable(v) for k, v in vars(value).items() if not k.startswith("_")}
    return str(value)


def print_summary(replay: FortniteReplay, elapsed: float) -> None:
    """解析結果の概要を表示する。"""
    info = replay.info
    header = replay.header
    game = replay.game_data

    print(f"解析時間        : {elapsed:.1f} 秒")
    print(f"リプレイ名      : {info.friendly_name}")
    print(f"録画日時        : {info.timestamp}")
    print(f"試合の長さ      : {info.length_in_ms / 1000:.1f} 秒")
    print(f"暗号化 / 圧縮   : {info.is_encrypted} / {info.is_compressed}")
    print(f"ブランチ        : {header.branch}")
    engine_version = header.engine_network_version
    engine_version_name = (
        engine_version.name
        if isinstance(engine_version, Enum)
        else f"未対応 ({engine_version})"
    )
    print(f"エンジンバージョン: {engine_version_name}")
    print(f"プレイリスト    : {game.current_playlist}")
    print(f"セッション ID   : {game.game_session_id}")
    print(f"プレイヤー数    : {len(replay.player_data)} (チーム {len(replay.team_data)})")
    print(f"撃破イベント    : {len(replay.eliminations)} 件")
    print(f"キルフィード    : {len(replay.kill_feed)} 件")

    if replay.stats is not None:
        stats = replay.stats
        print(
            "自分の成績      : "
            f"撃破 {stats.eliminations} / アシスト {stats.assists} / "
            f"与ダメージ {stats.damage_to_players} / 被ダメージ {stats.damage_taken}"
        )
    if replay.team_stats is not None:
        print(
            f"チーム成績      : 順位 {replay.team_stats.position} / "
            f"参加者 {replay.team_stats.total_players}"
        )

    owner = next((p for p in replay.player_data if p.is_replay_owner), None)
    if owner is not None:
        print(f"リプレイ所有者  : {owner.player_name or owner.player_id}")

    if replay.eliminations:
        print("\n撃破イベント (先頭 10 件):")
        for elimination in replay.eliminations[:10]:
            arrow = "自滅" if elimination.is_self_elimination else "->"
            distance = (
                f" ({elimination.distance / 100:.0f}m)"
                if elimination.distance is not None
                else ""
            )
            print(
                f"  {elimination.time}  {elimination.eliminator} {arrow} "
                f"{elimination.eliminated}{distance}"
                f"{' [ノック]' if elimination.knocked else ''}"
            )


def build_parser() -> argparse.ArgumentParser:
    """コマンドライン引数の定義を作る。"""
    parser = argparse.ArgumentParser(
        prog="fnreplay", description="Fortnite のリプレイファイルを解析する"
    )
    parser.add_argument("replay", type=Path, help="解析する .replay ファイル")
    parser.add_argument(
        "--mode",
        choices=sorted(_MODES),
        default="minimal",
        help="解析の深さ (既定: minimal)",
    )
    parser.add_argument("--json", type=Path, help="解析結果を JSON として保存する")
    parser.add_argument(
        "--oodle",
        nargs="?",
        const="",
        metavar="PATH",
        help="ネイティブ Oodle ライブラリを使う (パス省略時は自動探索)",
    )
    parser.add_argument("--verbose", "-v", action="count", default=0, help="ログを詳しく出す")
    parser.add_argument("--version", action="version", version=f"fnreplay {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """コマンドラインのエントリポイント。"""
    args = build_parser().parse_args(argv)

    level = logging.WARNING
    if args.verbose == 1:
        level = logging.INFO
    elif args.verbose >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")

    if args.oodle is not None:
        if use_native_oodle(args.oodle or None):
            print("ネイティブの Oodle ライブラリを使用します", file=sys.stderr)
        else:
            print(
                "ネイティブの Oodle ライブラリが見つかりません。純 Python 実装を使用します",
                file=sys.stderr,
            )

    reader = FortniteReplayReader(parse_mode=_MODES[args.mode])
    start = time.perf_counter()
    replay = reader.read_replay_file(args.replay)
    elapsed = time.perf_counter() - start

    print_summary(replay, elapsed)

    if args.json:
        args.json.write_text(
            json.dumps(to_jsonable(replay), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nJSON を書き出しました: {args.json}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
