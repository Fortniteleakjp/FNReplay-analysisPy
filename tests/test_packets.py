"""壊れたパケット/バンチで無限ループしないことのテスト。

Unreal Engine (UNetConnection::ReceivedPacket / UActorChannel::ProcessBunch) と同じく、
アーカイブがエラー状態になったらそのパケット・バンチを打ち切る。
"""

from __future__ import annotations

import pytest

from fnreplay.unreal.archives import BitReader
from fnreplay.unreal.enums import EngineNetworkVersionHistory
from fnreplay.unreal.replay_reader import MAX_PACKET_SIZE_IN_BITS, ReplayReader


class BitWriter:
    """Unreal と同じ並び (各バイトの LSB から) でビット列を作る。"""

    def __init__(self) -> None:
        self._bits: list[int] = []

    def bit(self, value: bool | int) -> "BitWriter":
        self._bits.append(1 if value else 0)
        return self

    def bits(self, value: int, count: int) -> "BitWriter":
        for index in range(count):
            self._bits.append((value >> index) & 1)
        return self

    def int_packed(self, value: int) -> "BitWriter":
        while True:
            chunk = (value & 0x7F) << 1
            value >>= 7
            if value:
                chunk |= 1
            self.bits(chunk, 8)
            if not value:
                return self

    def serialized_int(self, value: int, max_value: int) -> "BitWriter":
        """``read_serialized_int`` と同じ可変長で書き込む。"""
        accumulated = 0
        mask = 1
        while (accumulated + mask) < max_value:
            if value & mask:
                accumulated |= mask
                self.bit(1)
            else:
                self.bit(0)
            mask *= 2
        return self

    def build(self) -> tuple[bytes, int]:
        length = (len(self._bits) + 7) // 8
        data = bytearray(length)
        for index, value in enumerate(self._bits):
            if value:
                data[index >> 3] |= 1 << (index & 7)
        return bytes(data), len(self._bits)


class GuardedBitReader(BitReader):
    """``at_end`` の呼び出し回数を数えて、無限ループをテスト失敗に変えるリーダー。"""

    def __init__(self, data: bytes, bit_count: int, limit: int = 1000) -> None:
        super().__init__(data, bit_count)
        self._at_end_calls = 0
        self._at_end_limit = limit

    def at_end(self) -> bool:
        self._at_end_calls += 1
        if self._at_end_calls > self._at_end_limit:
            raise AssertionError("received_packet が終了しません (無限ループ)")
        return super().at_end()


def _bunch_header(*, partial: bool, bunch_data_bits: int) -> BitWriter:
    """バンチ 1 つぶんのヘッダーを書く (エンジンバージョンは最新を想定)。"""
    writer = BitWriter()
    writer.bit(0)  # bControl (bOpen / bClose は読まれない)
    writer.bit(0)  # bIsReplicationPaused
    writer.bit(0)  # bReliable
    writer.int_packed(0)  # ChIndex
    writer.bit(0)  # bHasPackageMapExports
    writer.bit(0)  # bHasMustBeMappedGUIDs
    writer.bit(1 if partial else 0)  # bPartial
    if partial:
        writer.bit(0)  # bPartialInitial
        writer.bit(0)  # bHasPartialCustomExportsFinalBit
        writer.bit(0)  # bPartialFinal
    writer.serialized_int(bunch_data_bits, MAX_PACKET_SIZE_IN_BITS)
    return writer


@pytest.mark.parametrize("partial", [False, True])
def test_received_packet_aborts_on_bunch_overflow(partial: bool) -> None:
    """バンチがパケットからはみ出していたら、そのパケットを打ち切る。"""
    data, bit_count = _bunch_header(partial=partial, bunch_data_bits=10000).build()
    reader = GuardedBitReader(data, bit_count)
    reader.engine_network_version = EngineNetworkVersionHistory.LATEST

    ReplayReader().received_packet(reader)

    assert reader.is_error
