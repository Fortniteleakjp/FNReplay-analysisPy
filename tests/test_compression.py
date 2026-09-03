"""Oodle (Mermaid) 展開器のテスト。

C# 版のテストデータ (``OozSharp.Test/CompressedChunk``) を使う。
環境変数 ``FNREPLAY_TEST_DATA`` にディレクトリを指定した場合のみ実行される。
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fnreplay.compression import kraken
from fnreplay.unreal.exceptions import DecoderException

_TEST_DATA = os.environ.get("FNREPLAY_TEST_DATA")
requires_data = pytest.mark.skipif(
    not _TEST_DATA, reason="FNREPLAY_TEST_DATA が設定されていません"
)


@pytest.mark.parametrize(
    "name,expected_size",
    [("mermaid-fortnite.dump", 405273), ("mermaid-fortnite2.dump", 262151)],
)
@requires_data
def test_mermaid_decompress(name: str, expected_size: int) -> None:
    path = Path(_TEST_DATA) / name
    if not path.exists():
        pytest.skip(f"{path} がありません")
    data = path.read_bytes()
    result = kraken.decompress(data, expected_size)
    assert len(result) == expected_size


@pytest.mark.parametrize(
    "raw,message",
    [(b"\x8C\x01", "LZH"), (b"\x8C\x09", "Kraken")],
)
def test_unsupported_decoder(raw: bytes, message: str) -> None:
    with pytest.raises(DecoderException) as error:
        kraken.decompress(raw, 393294)
    assert message in str(error.value)


@pytest.mark.parametrize(
    "raw,decoder_type,restart,uncompressed,checksums",
    [
        (b"\x8C\x0A", 10, True, False, False),
        (b"\x8C\x08", 8, True, False, False),
        (b"\x8C\x0B", 11, True, False, False),
    ],
)
def test_kraken_header(
    raw: bytes, decoder_type: int, restart: bool, uncompressed: bool, checksums: bool
) -> None:
    header = kraken.KrakenHeader(raw[0], raw[1])
    assert header.decoder_type == decoder_type
    assert header.restart_decoder is restart
    assert header.uncompressed is uncompressed
    assert header.use_checksums is checksums


@pytest.mark.parametrize("raw", [b"\x2C\x0A", b"\x8D\x0A"])
def test_kraken_header_invalid(raw: bytes) -> None:
    with pytest.raises(DecoderException):
        kraken.KrakenHeader(raw[0], raw[1])
