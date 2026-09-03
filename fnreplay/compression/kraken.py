"""Oodle (Kraken コンテナ / Mermaid) 展開器の純 Python 実装。

C# 版 ``OozSharp`` (さらに元は https://github.com/powzix/ooz) の移植。
Fortnite のリプレイは Mermaid で圧縮されており、エントロピー符号化されていない
サブストリームのみを使うため、その範囲に絞って実装している。

ライセンス上の注意: 元実装 (ooz) は GPLv3 で公開されている。
"""

from __future__ import annotations

import sys
from array import array
from dataclasses import dataclass, field

from ..unreal.exceptions import DecoderException

#: 出力・入力バッファの末尾に付ける余白 (8 バイト単位のコピーで読み書きが溢れるため)
_PADDING = 64

_DECODER_MERMAID = 10
_DECODER_NAMES = {
    1: "LZH",
    2: "LZHLW",
    3: "LZNIB",
    4: "None",
    5: "LZB16",
    6: "LZBLW",
    7: "LZA",
    8: "LZNA",
    9: "Kraken",
    10: "Mermaid",
    11: "BitKnit",
    12: "Selkie",
    13: "Akkorokamui",
}

#: MermaidLzTable 構造体の大きさ (スクラッチ領域の計算に使う)
_LZ_TABLE_SIZE = 104


def _u16(data: bytes, pos: int) -> int:
    return data[pos] | (data[pos + 1] << 8)


class KrakenHeader:
    """Kraken コンテナのブロックヘッダー。"""

    __slots__ = ("decoder_type", "restart_decoder", "uncompressed", "use_checksums")

    def __init__(self, first_byte: int, second_byte: int) -> None:
        if (first_byte & 0xF) != 0xC:
            raise DecoderException("ヘッダーの解析に失敗しました ((source[0] & 0xF) != 0xC)")
        if ((first_byte >> 4) & 3) != 0:
            raise DecoderException("ヘッダーの解析に失敗しました (((source[0] >> 4) & 3) != 0)")
        self.restart_decoder = ((first_byte >> 7) & 1) == 1
        self.uncompressed = ((first_byte >> 6) & 1) == 1
        self.decoder_type = second_byte & 0x7F
        self.use_checksums = ((second_byte >> 7) & 1) == 1


class KrakenQuantumHeader:
    """量子 (最大 256KB) 単位のヘッダー。"""

    __slots__ = ("compressed_size", "checksum", "flag1", "flag2", "whole_match_distance", "size")

    def __init__(self, data: bytes, pos: int, use_checksums: bool) -> None:
        value = (data[pos] << 16) | (data[pos + 1] << 8) | data[pos + 2]
        size = value & 0x3FFFF
        self.checksum = 0
        self.whole_match_distance = 0

        if size != 0x3FFFF:
            self.compressed_size = size + 1
            self.flag1 = (value >> 18) & 1
            self.flag2 = (value >> 19) & 1
            if use_checksums:
                self.checksum = (data[pos + 3] << 16) | (data[pos + 4] << 8) | data[pos + 5]
                self.size = 6
            else:
                self.size = 3
            return

        value >>= 18
        if value == 1:
            self.checksum = data[pos + 3]
            self.compressed_size = 0
            self.flag1 = 0
            self.flag2 = 0
            self.size = 4
            return

        raise DecoderException("KrakenQuantumHeader の解析に失敗しました")


@dataclass
class _LzTable:
    """Mermaid の各ストリームの位置を保持する。"""

    cmd_stream: int = 0
    cmd_stream_end: int = 0
    length_stream: int = 0
    lit_stream: int = 0
    lit_stream_end: int = 0
    off16: array = field(default_factory=lambda: array("H"))
    off16_index: int = 0
    off16_end: int = 0
    off32: array = field(default_factory=lambda: array("I"))
    off32_index: int = 0
    off32_end: int = 0
    off32_1: array = field(default_factory=lambda: array("I"))
    off32_2: array = field(default_factory=lambda: array("I"))
    off32_1_size: int = 0
    off32_2_size: int = 0
    cmd_stream_2_offsets: int = 0
    cmd_stream_2_offsets_end: int = 0


def decompress(compressed: bytes, uncompressed_size: int) -> bytes:
    """Oodle で圧縮されたデータを展開する。

    Args:
        compressed: 圧縮済みデータ。
        uncompressed_size: 展開後のバイト数。

    Returns:
        展開されたバイト列。
    """
    src = bytes(compressed) + bytes(_PADDING)
    src_length = len(compressed)
    dst = bytearray(uncompressed_size + _PADDING)

    remaining = uncompressed_size
    src_pos = 0
    src_left = src_length
    dst_offset = 0
    header: KrakenHeader | None = None

    while remaining != 0:
        src_used, dst_used, header = _decode_step(
            dst, dst_offset, remaining, src, src_pos, src_left, header
        )
        if src_used == 0 and dst_used == 0:
            raise DecoderException("展開が進みませんでした (入力データが途中で終わっています)")
        src_pos += src_used
        src_left -= src_used
        dst_offset += dst_used
        remaining -= dst_used

    return bytes(dst[:uncompressed_size])


def _decode_step(
    dst: bytearray,
    dst_offset: int,
    remaining: int,
    src: bytes,
    src_pos: int,
    src_left: int,
    header: KrakenHeader | None,
) -> tuple[int, int, KrakenHeader]:
    """1 ブロック分を展開する。戻り値は ``(消費したバイト数, 出力したバイト数, ヘッダー)``。"""
    src_in = src_pos
    src_end = src_pos + src_left

    if (dst_offset & 0x3FFFF) == 0:
        header = KrakenHeader(src[src_pos], src[src_pos + 1])
        src_pos += 2

    if header is None:  # pragma: no cover - 到達しない
        raise DecoderException("ヘッダーがありません")

    is_mermaid = header.decoder_type == _DECODER_MERMAID
    dst_bytes_left = min(0x40000 if is_mermaid else 0x4000, remaining)

    if header.uncompressed:
        if src_end - src_pos < dst_bytes_left:
            raise DecoderException(
                f"入力が不足しています ({src_end - src_pos} < {dst_bytes_left})"
            )
        dst[dst_offset : dst_offset + dst_bytes_left] = src[src_pos : src_pos + dst_bytes_left]
        return (src_pos - src_in) + dst_bytes_left, dst_bytes_left, header

    if not is_mermaid:
        name = _DECODER_NAMES.get(header.decoder_type, str(header.decoder_type))
        raise DecoderException(f"デコーダー {name} は未対応です")

    quantum = KrakenQuantumHeader(src, src_pos, header.use_checksums)
    src_pos += quantum.size

    if src_pos > src_end:
        raise DecoderException("入力データの範囲を超えました")

    if src_end - src_pos < quantum.compressed_size:
        # まだ十分なバイトが揃っていない
        return 0, 0, header

    if quantum.compressed_size > remaining:
        raise DecoderException(
            f"圧縮サイズが残りの出力サイズを超えています ({quantum.compressed_size} > {remaining})"
        )

    if quantum.compressed_size == 0:
        if quantum.whole_match_distance != 0:
            raise DecoderException("WholeMatch ブロックは未対応です")
        # 1 バイトで埋められたブロック
        fill = quantum.checksum & 0xFF
        dst[dst_offset : dst_offset + dst_bytes_left] = bytes([fill]) * dst_bytes_left
        return src_pos - src_in, dst_bytes_left, header

    if quantum.compressed_size == dst_bytes_left:
        # 非圧縮の量子
        dst[dst_offset : dst_offset + dst_bytes_left] = src[src_pos : src_pos + dst_bytes_left]
        return (src_pos - src_in) + dst_bytes_left, dst_bytes_left, header

    num_bytes = _mermaid_decode_quantum(
        dst,
        dst_offset,
        dst_offset + dst_bytes_left,
        src,
        src_pos,
        src_pos + quantum.compressed_size,
    )

    if num_bytes != quantum.compressed_size:
        raise DecoderException(
            f"展開したバイト数が一致しません ({num_bytes} != {quantum.compressed_size})"
        )

    return (src_pos - src_in) + num_bytes, dst_bytes_left, header


def _decode_bytes(
    src: bytes, src_pos: int, src_end: int, output_size: int
) -> tuple[int, int, int]:
    """サブストリームの位置を求める。

    戻り値は ``(データ開始位置, データ長, 消費したバイト数)``。
    エントロピー符号化されたチャンクには対応しない。
    """
    src_org = src_pos

    if src_end - src_pos < 2:
        raise DecoderException(f"入力が不足しています ({src_end - src_pos} バイト)")

    chunk_type = (src[src_pos] >> 4) & 0x7
    if chunk_type != 0:
        raise DecoderException(
            f"エントロピー符号化されたチャンク (type={chunk_type}) には対応していません"
        )

    if src[src_pos] >= 0x80:
        # 長さが下位 12 ビットに入っている形式
        source_size = ((src[src_pos] << 8) | src[src_pos + 1]) & 0xFFF
        src_pos += 2
    else:
        if src_end - src_pos < 3:
            raise DecoderException(f"入力が不足しています ({src_end - src_pos} バイト)")
        source_size = (src[src_pos] << 16) | (src[src_pos + 1] << 8) | src[src_pos + 2]
        if source_size & ~0x3FFFF:
            raise DecoderException("予約ビットが設定されています")
        src_pos += 3

    if source_size > output_size or src_end - src_pos < source_size:
        raise DecoderException(
            f"サブストリームの長さが不正です (size={source_size}, output_size={output_size})"
        )

    return src_pos, source_size, (src_pos + source_size - src_org)


def _mermaid_decode_far_offsets(
    src: bytes, src_pos: int, src_end: int, output_size: int, offset: int
) -> tuple[array, int]:
    """32 ビットの遠距離オフセット列を読み取る。"""
    result = array("I", bytes(4 * output_size))
    start = src_pos

    if offset < (0xC00000 - 1):
        for i in range(output_size):
            if src_end - src_pos < 3:
                raise DecoderException("遠距離オフセットの読み取りで入力が不足しました")
            off = src[src_pos] | (src[src_pos + 1] << 8) | (src[src_pos + 2] << 16)
            src_pos += 3
            result[i] = off
            if off > offset:
                raise DecoderException(f"オフセットが不正です ({off} > {offset})")
        return result, src_pos - start

    for i in range(output_size):
        if src_end - src_pos < 3:
            raise DecoderException("遠距離オフセットの読み取りで入力が不足しました")
        off = src[src_pos] | (src[src_pos + 1] << 8) | (src[src_pos + 2] << 16)
        src_pos += 3
        if off >= 0xC00000:
            if src_pos == src_end:
                raise DecoderException("遠距離オフセットの読み取りで入力が不足しました")
            off += src[src_pos] << 22
            src_pos += 1
        result[i] = off
        if off > offset:
            raise DecoderException(f"オフセットが不正です ({off} > {offset})")

    return result, src_pos - start


def _mermaid_read_lz_table(
    mode: int,
    src: bytes,
    src_pos: int,
    src_end: int,
    dst: bytearray,
    dst_pos: int,
    dst_size: int,
    offset: int,
) -> _LzTable:
    """各サブストリームの位置を読み取る。"""
    if mode > 1:
        raise DecoderException(f"Mermaid モード {mode} は未対応です")
    if src_end - src_pos < 10:
        raise DecoderException("LZ テーブルの読み取りで入力が不足しました")

    scratch_left = min(2 * dst_size + 32, 0x40000) - _LZ_TABLE_SIZE
    lz = _LzTable()

    if offset == 0:
        dst[dst_pos : dst_pos + 8] = src[src_pos : src_pos + 8]
        dst_pos += 8
        src_pos += 8

    # リテラルストリーム
    start, decode_count, num_bytes = _decode_bytes(
        src, src_pos, src_end, min(scratch_left, dst_size)
    )
    src_pos += num_bytes
    lz.lit_stream = start
    lz.lit_stream_end = start + decode_count
    scratch_left -= decode_count

    # フラグ (コマンド) ストリーム
    start, decode_count, num_bytes = _decode_bytes(
        src, src_pos, src_end, min(scratch_left, dst_size)
    )
    src_pos += num_bytes
    lz.cmd_stream = start
    lz.cmd_stream_end = start + decode_count
    scratch_left -= decode_count

    lz.cmd_stream_2_offsets_end = decode_count

    if dst_size <= 0x10000:
        lz.cmd_stream_2_offsets = decode_count
    else:
        if src_end - src_pos < 2:
            raise DecoderException("LZ テーブルの読み取りで入力が不足しました")
        lz.cmd_stream_2_offsets = _u16(src, src_pos)
        src_pos += 2
        if lz.cmd_stream_2_offsets > lz.cmd_stream_2_offsets_end:
            raise DecoderException("コマンドストリームの分割位置が不正です")

    if src_end - src_pos < 2:
        raise DecoderException("LZ テーブルの読み取りで入力が不足しました")

    off16_count = _u16(src, src_pos)

    if off16_count == 0xFFFF:
        # 上位バイトと下位バイトが別ストリームになっている形式
        src_pos += 2
        high_start, high_count, num_bytes = _decode_bytes(
            src, src_pos, src_end, min(scratch_left, dst_size >> 1)
        )
        src_pos += num_bytes
        scratch_left -= high_count

        low_start, low_count, num_bytes = _decode_bytes(
            src, src_pos, src_end, min(scratch_left, dst_size >> 1)
        )
        src_pos += num_bytes
        scratch_left -= low_count

        if low_count != high_count:
            raise DecoderException("オフセットストリームの要素数が一致しません")
        if low_count * 2 > scratch_left:
            raise DecoderException("スクラッチ領域が不足しました")
        scratch_left -= low_count * 2

        off16 = array("I", bytes(4 * low_count))
        for i in range(low_count):
            off16[i] = src[low_start + i] + src[high_start + i] * 256
        lz.off16 = off16
        lz.off16_end = low_count
    else:
        off16 = array("H")
        off16.frombytes(src[src_pos + 2 : src_pos + 2 + off16_count * 2])
        if sys.byteorder == "big":  # pragma: no cover - 通常は little endian
            off16.byteswap()
        src_pos += 2 + off16_count * 2
        lz.off16 = off16
        lz.off16_end = off16_count

    lz.off16_index = 0

    if src_end - src_pos < 3:
        raise DecoderException("LZ テーブルの読み取りで入力が不足しました")

    temp = src[src_pos] | (src[src_pos + 1] << 8) | (src[src_pos + 2] << 16)
    src_pos += 3

    if temp != 0:
        off32_size_1 = temp >> 12
        off32_size_2 = temp & 0xFFF

        if off32_size_1 == 4095:
            if src_end - src_pos < 2:
                raise DecoderException("LZ テーブルの読み取りで入力が不足しました")
            off32_size_1 = _u16(src, src_pos)
            src_pos += 2

        if off32_size_2 == 4095:
            if src_end - src_pos < 2:
                raise DecoderException("LZ テーブルの読み取りで入力が不足しました")
            off32_size_2 = _u16(src, src_pos)
            src_pos += 2

        if 4 * (off32_size_1 + off32_size_2) + 64 > scratch_left:
            raise DecoderException("スクラッチ領域が不足しました")

        lz.off32_1_size = off32_size_1
        lz.off32_2_size = off32_size_2

        lz.off32_1, num_bytes = _mermaid_decode_far_offsets(
            src, src_pos, src_end, off32_size_1, offset
        )
        src_pos += num_bytes

        lz.off32_2, num_bytes = _mermaid_decode_far_offsets(
            src, src_pos, src_end, off32_size_2, offset + 0x10000
        )
        src_pos += num_bytes
    else:
        lz.off32_1_size = 0
        lz.off32_2_size = 0
        lz.off32_1 = array("I")
        lz.off32_2 = array("I")

    lz.length_stream = src_pos
    return lz


def _mermaid_process_lz_runs(
    mode: int,
    src: bytes,
    src_end: int,
    dst: bytearray,
    dst_pos: int,
    dst_size: int,
    offset: int,
    lz: _LzTable,
) -> None:
    """LZ 命令列を実行して出力を生成する。"""
    dst_start = dst_pos - offset
    saved_dist = -8
    src_current = -1
    cmd_stream_begin = lz.cmd_stream

    for iteration in (0, 1):
        dst_size_current = min(dst_size, 0x10000)

        if iteration == 0:
            lz.off32 = lz.off32_1
            lz.off32_index = 0
            lz.off32_end = lz.off32_1_size
            lz.cmd_stream_end = lz.cmd_stream + lz.cmd_stream_2_offsets
        else:
            lz.off32 = lz.off32_2
            lz.off32_index = 0
            lz.off32_end = lz.off32_2_size
            lz.cmd_stream_end = cmd_stream_begin + lz.cmd_stream_2_offsets_end
            lz.cmd_stream = cmd_stream_begin + lz.cmd_stream_2_offsets

        if mode == 0:
            raise DecoderException("Mermaid モード 0 は未対応です")

        src_current, saved_dist = _mermaid_mode1(
            dst,
            dst_pos,
            dst_size_current,
            dst_start,
            src,
            src_end,
            lz,
            saved_dist,
            8 if (offset == 0 and iteration == 0) else 0,
        )

        dst_pos += dst_size_current
        dst_size -= dst_size_current

        if dst_size == 0:
            break

    if src_current != src_end:
        raise DecoderException("入力データを読み切れませんでした")


def _mermaid_mode1(
    dst: bytearray,
    dst_pos: int,
    dst_size: int,
    dst_start: int,
    src: bytes,
    src_end: int,
    lz: _LzTable,
    saved_dist: int,
    start_off: int,
) -> tuple[int, int]:
    """Mermaid モード 1 の命令列を処理する。

    戻り値は ``(長さストリームの位置, 直近のオフセット)``。
    """
    dst_end = dst_pos + dst_size
    cmd_stream = lz.cmd_stream
    cmd_stream_end = lz.cmd_stream_end
    length_stream = lz.length_stream
    lit_stream = lz.lit_stream
    lit_stream_end = lz.lit_stream_end
    off16 = lz.off16
    off16_index = lz.off16_index
    off16_end = lz.off16_end
    off32 = lz.off32
    off32_index = lz.off32_index
    off32_end = lz.off32_end
    recent_offs = saved_dist

    dst_begin = dst_pos
    dst_pos += start_off

    while cmd_stream < cmd_stream_end:
        flag = src[cmd_stream]
        cmd_stream += 1

        if flag >= 24:
            # リテラルを少しコピーしてから直近のオフセットでマッチをコピーする
            lit_len = flag & 7
            dst[dst_pos : dst_pos + 8] = src[lit_stream : lit_stream + 8]
            dst_pos += lit_len
            lit_stream += lit_len

            if not (flag & 0x80):
                if off16_index >= off16_end:
                    raise DecoderException("16 ビットオフセットが不足しました")
                recent_offs = -off16[off16_index]
                off16_index += 1

            match = dst_pos + recent_offs
            if match < dst_start:
                raise DecoderException("マッチ位置が出力バッファの範囲外です")
            dst[dst_pos : dst_pos + 8] = dst[match : match + 8]
            dst[dst_pos + 8 : dst_pos + 16] = dst[match + 8 : match + 16]
            dst_pos += (flag >> 3) & 0xF

        elif flag > 2:
            length = flag + 5
            if off32_index >= off32_end:
                raise DecoderException("32 ビットオフセットが不足しました")
            match = dst_begin - off32[off32_index]
            off32_index += 1
            recent_offs = match - dst_pos

            if dst_end - dst_pos < length:
                raise DecoderException("出力バッファが不足しました")
            if match < dst_start:
                raise DecoderException("マッチ位置が出力バッファの範囲外です")

            dst[dst_pos : dst_pos + 8] = dst[match : match + 8]
            dst[dst_pos + 8 : dst_pos + 16] = dst[match + 8 : match + 16]
            dst[dst_pos + 16 : dst_pos + 24] = dst[match + 16 : match + 24]
            dst[dst_pos + 24 : dst_pos + 32] = dst[match + 24 : match + 32]
            dst_pos += length

        elif flag == 0:
            # 長いリテラル列
            if src_end - length_stream == 0:
                raise DecoderException("長さストリームが不足しました")
            length = src[length_stream]
            if length > 251:
                if src_end - length_stream < 3:
                    raise DecoderException("長さストリームが不足しました")
                length += _u16(src, length_stream + 1) * 4
                length_stream += 2
            length_stream += 1
            length += 64

            if dst_end - dst_pos < length or lit_stream_end - lit_stream < length:
                raise DecoderException("リテラル列の長さが不正です")

            while True:
                dst[dst_pos : dst_pos + 8] = src[lit_stream : lit_stream + 8]
                dst[dst_pos + 8 : dst_pos + 16] = src[lit_stream + 8 : lit_stream + 16]
                dst_pos += 16
                lit_stream += 16
                length -= 16
                if length <= 0:
                    break
            dst_pos += length
            lit_stream += length

        elif flag == 1:
            # 16 ビットオフセットによる長いマッチ
            if src_end - length_stream == 0:
                raise DecoderException("長さストリームが不足しました")
            length = src[length_stream]
            if length > 251:
                if src_end - length_stream < 3:
                    raise DecoderException("長さストリームが不足しました")
                length += _u16(src, length_stream + 1) * 4
                length_stream += 2
            length_stream += 1
            length += 91

            if off16_index >= off16_end:
                raise DecoderException("16 ビットオフセットが不足しました")
            match = dst_pos - off16[off16_index]
            off16_index += 1
            recent_offs = match - dst_pos
            if match < dst_start:
                raise DecoderException("マッチ位置が出力バッファの範囲外です")

            while True:
                dst[dst_pos : dst_pos + 8] = dst[match : match + 8]
                dst[dst_pos + 8 : dst_pos + 16] = dst[match + 8 : match + 16]
                dst_pos += 16
                match += 16
                length -= 16
                if length <= 0:
                    break
            dst_pos += length

        else:
            # 32 ビットオフセットによる長いマッチ
            if src_end - length_stream == 0:
                raise DecoderException("長さストリームが不足しました")
            length = src[length_stream]
            if length > 251:
                if src_end - length_stream < 3:
                    raise DecoderException("長さストリームが不足しました")
                length += _u16(src, length_stream + 1) * 4
                length_stream += 2
            length_stream += 1
            length += 29

            if off32_index >= off32_end:
                raise DecoderException("32 ビットオフセットが不足しました")
            match = dst_begin - off32[off32_index]
            off32_index += 1
            recent_offs = match - dst_pos
            if match < dst_start:
                raise DecoderException("マッチ位置が出力バッファの範囲外です")

            while True:
                dst[dst_pos : dst_pos + 8] = dst[match : match + 8]
                dst[dst_pos + 8 : dst_pos + 16] = dst[match + 8 : match + 16]
                dst_pos += 16
                match += 16
                length -= 16
                if length <= 0:
                    break
            dst_pos += length

    # 残りはリテラルで埋める
    length = dst_end - dst_pos
    while length >= 8:
        dst[dst_pos : dst_pos + 8] = src[lit_stream : lit_stream + 8]
        dst_pos += 8
        lit_stream += 8
        length -= 8
    if length > 0:
        dst[dst_pos : dst_pos + length] = src[lit_stream : lit_stream + length]
        dst_pos += length
        lit_stream += length

    lz.length_stream = length_stream
    lz.off16_index = off16_index
    lz.off32_index = off32_index
    lz.lit_stream = lit_stream

    return length_stream, recent_offs


def _mermaid_decode_quantum(
    dst: bytearray, dst_pos: int, dst_end: int, src: bytes, src_pos: int, src_end: int
) -> int:
    """量子 1 つ分を展開する。戻り値は消費した入力バイト数。"""
    src_in = src_pos

    while dst_end - dst_pos != 0:
        dst_count = min(dst_end - dst_pos, 0x20000)

        if src_end - src_pos < 4:
            raise DecoderException(f"入力が不足しています ({src_end - src_pos} バイト)")

        chunk_header = src[src_pos + 2] | (src[src_pos + 1] << 8) | (src[src_pos] << 16)

        if not (chunk_header & 0x800000):
            raise DecoderException("マッチを含まないチャンクには対応していません")

        src_pos += 3
        src_used = chunk_header & 0x7FFFF
        mode = (chunk_header >> 19) & 0xF

        if src_end - src_pos < src_used:
            raise DecoderException(
                f"入力が不足しています ({src_end - src_pos} < {src_used})"
            )

        if src_used < dst_count:
            lz = _mermaid_read_lz_table(
                mode, src, src_pos, src_pos + src_used, dst, dst_pos, dst_count, dst_pos
            )
            _mermaid_process_lz_runs(
                mode, src, src_pos + src_used, dst, dst_pos, dst_count, dst_pos, lz
            )
        elif src_used > dst_count or mode != 0:
            raise DecoderException(
                f"チャンクヘッダーが不正です (src_used={src_used}, dst_count={dst_count}, mode={mode})"
            )
        else:
            dst[dst_pos : dst_pos + dst_count] = src[src_pos : src_pos + dst_count]

        src_pos += src_used
        dst_pos += dst_count

    return src_pos - src_in
