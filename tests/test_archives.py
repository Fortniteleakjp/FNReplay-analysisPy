"""アーカイブリーダーのテスト (C# 版 Unreal.Core.Test からの移植)。"""

from __future__ import annotations

import pytest

from fnreplay.unreal.archives import BinaryReader, BitReader, NetBitReader
from fnreplay.unreal.enums import (
    EngineNetworkVersionHistory,
    RotatorQuantization,
    SeekOrigin,
    VectorQuantization,
)
from fnreplay.unreal.models import FVector2D


@pytest.mark.parametrize(
    "raw,expected_bits",
    [
        (b"\x23", [True, True, False, False, False, True, False, False]),
        (b"\x2F", [True, True, True, True, False, True, False, False]),
        (b"\xD7", [True, True, True, False, True, False, True, True]),
    ],
)
def test_read_bit(raw: bytes, expected_bits: list[bool]) -> None:
    reader = BitReader(raw)
    for index, expected in enumerate(expected_bits):
        assert reader.read_bit() is expected
        assert reader.position == index + 1
    assert reader.position == 8


@pytest.mark.parametrize("raw,position", [(b"", 0), (b"\x35", 8)])
def test_read_bit_sets_error(raw: bytes, position: int) -> None:
    reader = BitReader(raw)
    reader.seek(position)
    reader.read_bit()
    assert reader.is_error


def test_peek_bit_does_not_advance() -> None:
    reader = BitReader(b"\x23")
    for _ in range(8):
        assert reader.peek_bit() is True
    assert reader.position == 0


@pytest.mark.parametrize(
    "raw,expected,bits_to_read",
    [
        (b"\x23", b"\x23", 7),
        (b"\x23", b"\x03", 5),
        (b"\x0D\x0A", b"\x0D", 8),
        (b"\x0D\x0A", b"\x0D\x0A", 16),
    ],
)
def test_read_bits(raw: bytes, expected: bytes, bits_to_read: int) -> None:
    reader = BitReader(raw)
    assert reader.read_bits(bits_to_read) == expected
    assert reader.position == bits_to_read


@pytest.mark.parametrize(
    "raw,expected,position,bits_to_read",
    [
        (b"\x99", b"\x0C", 1, 4),
        (b"\x99", b"\x02", 2, 2),
        (b"\x99", b"\x03", 3, 3),
    ],
)
def test_read_bits_with_offset(
    raw: bytes, expected: bytes, position: int, bits_to_read: int
) -> None:
    reader = BitReader(raw)
    reader.seek(position)
    assert reader.read_bits(bits_to_read) == expected
    assert reader.position == position + bits_to_read


@pytest.mark.parametrize(
    "raw,expected,bits_to_read,position",
    [
        (b"\x23", b"\x11", 5, 1),
        (b"\x4A\xF1\xB2", b"\x5E\x06", 11, 11),
        (b"\xEE\x32\xC9", b"\x0C", 4, 20),
        (b"\x58\x22\x38", b"\x4B\x04", 16, 3),
        (b"\x58\x22\x38", b"\x4B\x04\x03", 18, 3),
        (b"\x94\xA6\x7C\x0D", b"\xD2\x94\x2F", 23, 3),
    ],
)
def test_read_bits_misaligned(
    raw: bytes, expected: bytes, bits_to_read: int, position: int
) -> None:
    reader = BitReader(raw)
    reader.seek(position)
    assert reader.read_bits(bits_to_read) == expected
    assert reader.position == position + bits_to_read


@pytest.mark.parametrize("bits_to_read", [9, -1])
def test_read_bits_sets_error(bits_to_read: int) -> None:
    reader = BitReader(b"\x23")
    reader.read_bits(bits_to_read)
    assert reader.is_error


@pytest.mark.parametrize(
    "seek,expected,origin",
    [
        (8, 8, SeekOrigin.Begin),
        (6, 18, SeekOrigin.End),
        (11, 11, SeekOrigin.Current),
    ],
)
def test_seek(seek: int, expected: int, origin: SeekOrigin) -> None:
    reader = BitReader(b"\x23\x2F\xD7")
    reader.seek(seek, origin)
    assert reader.position == expected


@pytest.mark.parametrize(
    "position,origin",
    [
        (-1, SeekOrigin.Begin),
        (25, SeekOrigin.Begin),
        (25, SeekOrigin.End),
        (25, SeekOrigin.Current),
    ],
)
def test_seek_sets_error(position: int, origin: SeekOrigin) -> None:
    reader = BitReader(b"\x23\x2F\xD7")
    reader.seek(position, origin)
    assert reader.is_error


@pytest.mark.parametrize("raw", [b"\x23\x2F\xD7", b"\x5C\xF2\x0D\x0A\x3A"])
def test_read_byte(raw: bytes) -> None:
    reader = BitReader(raw)
    for expected in raw:
        assert reader.read_byte() == expected
    assert reader.position == len(raw) * 8


@pytest.mark.parametrize(
    "expected,bit_position", [(0x91, 1), (0x5C, 14), (0xF2, 4)]
)
def test_read_byte_misaligned(expected: int, bit_position: int) -> None:
    reader = BitReader(b"\x23\x2F\xD7")
    reader.seek(bit_position)
    assert reader.read_byte() == expected
    assert reader.position == bit_position + 8


@pytest.mark.parametrize("raw", [b"\x23\x2F\xD7", b"\xAB\x46\x65", b"\x72\x6F\x99"])
def test_read_bytes(raw: bytes) -> None:
    reader = BitReader(raw)
    assert reader.read_bytes(3) == raw
    assert reader.position == len(raw) * 8


@pytest.mark.parametrize(
    "raw,expected,bytes_to_read,bit_position",
    [
        (b"\x23\x2F\xD7", b"\x91", 1, 1),
        (b"\x4E\xE5\x8A\x3F", b"\x2B\xFE", 2, 14),
        (b"\xAB\x46\x65\x72\x72\x6F\x6E\x99", b"\x93\x93", 2, 21),
    ],
)
def test_read_bytes_misaligned(
    raw: bytes, expected: bytes, bytes_to_read: int, bit_position: int
) -> None:
    reader = BitReader(raw)
    reader.seek(bit_position)
    assert reader.read_bytes(bytes_to_read) == expected
    assert reader.position == bit_position + bytes_to_read * 8


@pytest.mark.parametrize("bit_position", [1, 14, -1])
def test_read_bytes_sets_error(bit_position: int) -> None:
    reader = BitReader(b"\x23\x2F\xD7")
    reader.seek(bit_position)
    reader.read_bytes(3)
    assert reader.is_error


@pytest.mark.parametrize("expected,raw", [(510, b"\xFE\x01"), (16, b"\x10\x00")])
def test_read_uint16(expected: int, raw: bytes) -> None:
    assert BitReader(raw).read_uint16() == expected


@pytest.mark.parametrize("expected,raw", [(109, b"\x6D\x00"), (-255, b"\x01\xFF")])
def test_read_int16(expected: int, raw: bytes) -> None:
    assert BitReader(raw).read_int16() == expected


@pytest.mark.parametrize(
    "expected,raw",
    [
        (14858, b"\x0A\x3A\x00\x00"),
        (12345, b"\x39\x30\x00\x00"),
        (420, b"\xA4\x01\x00\x00"),
        (73909, b"\xB5\x20\x01\x00"),
    ],
)
def test_read_uint32(expected: int, raw: bytes) -> None:
    assert BitReader(raw).read_uint32() == expected


@pytest.mark.parametrize(
    "expected,raw",
    [
        (109, b"\x6D\x00\x00\x00"),
        (14858, b"\x0A\x3A\x00\x00"),
        (420, b"\xA4\x01\x00\x00"),
        (-420, b"\x5C\xFE\xFF\xFF"),
    ],
)
def test_read_int32(expected: int, raw: bytes) -> None:
    assert BitReader(raw).read_int32() == expected


@pytest.mark.parametrize("raw", [b"\xE7", b"\x6D\x00\x00"])
def test_read_int32_sets_error(raw: bytes) -> None:
    reader = BitReader(raw)
    assert reader.read_int32() == 0
    assert reader.is_error


@pytest.mark.parametrize(
    "expected,raw",
    [
        (123456789123456789, b"\x15\x5F\xD0\xAC\x4B\x9B\xB6\x01"),
        (420, b"\xA4\x01\x00\x00\x00\x00\x00\x00"),
    ],
)
def test_read_uint64(expected: int, raw: bytes) -> None:
    assert BitReader(raw).read_uint64() == expected


@pytest.mark.parametrize(
    "expected,raw",
    [
        (123456789123456789, b"\x15\x5F\xD0\xAC\x4B\x9B\xB6\x01"),
        (420, b"\xA4\x01\x00\x00\x00\x00\x00\x00"),
        (-420, b"\x5C\xFE\xFF\xFF\xFF\xFF\xFF\xFF"),
    ],
)
def test_read_int64(expected: int, raw: bytes) -> None:
    assert BitReader(raw).read_int64() == expected


@pytest.mark.parametrize(
    "expected,raw", [(7, b"\x0E"), (18, b"\x24\x40"), (102, b"\xCC")]
)
def test_read_int_packed(expected: int, raw: bytes) -> None:
    assert BitReader(raw).read_int_packed() == expected


@pytest.mark.parametrize(
    "expected,raw,max_value", [(0, b"\x64", 3), (1, b"\x01", 2)]
)
def test_read_serialized_int(expected: int, raw: bytes, max_value: int) -> None:
    assert BitReader(raw).read_serialized_int(max_value) == expected


def test_read_fname_hardcoded() -> None:
    reader = BitReader(b"\x99\xF1")
    reader.engine_network_version = (
        EngineNetworkVersionHistory.HISTORY_FAST_ARRAY_DELTA_STRUCT
    )
    assert reader.read_fname() == "Actor"
    assert reader.position == 9
    assert not reader.is_error


@pytest.mark.parametrize(
    "raw,x,y,z",
    [
        (b"\x70\x99\x7F\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F", 0.998435020446777, 1, 1),
        (
            b"\xD3\x89\x7F\x3F\xBB\x08\x80\x3F\x00\x00\x80\x3F",
            0.99819678068161,
            1.00026643276215,
            1,
        ),
    ],
)
def test_read_fvector(raw: bytes, x: float, y: float, z: float) -> None:
    result = BitReader(raw).read_fvector()
    assert result.x == pytest.approx(x, rel=1e-6)
    assert result.y == pytest.approx(y, rel=1e-6)
    assert result.z == pytest.approx(z, rel=1e-6)


@pytest.mark.parametrize(
    "raw,scale_factor,max_bits,x,y,z",
    [
        (b"\xB4\xC5\x5C\xEF\x81\x33\x76\x33\x3F", 10, 24, 176286.1, -167520.3, -2618.1),
        (b"\x74\xF3\x74\xC7\xB4\x2D\x62\x51\x3F", 10, 24, 181237.9, -172272.8, -2235.1),
        (
            b"\x98\xE4\x52\x62\x07\x9A\x75\x70\x4F\xF9\x03",
            100,
            30,
            179955.56,
            -181401.46,
            -2192.08,
        ),
        (
            b"\x98\x5A\xF6\x63\x8C\x4B\x7A\x46\x08\xF8\x03",
            100,
            30,
            188546.12,
            -175249.68,
            -2610.85,
        ),
        (b"\x40\x05", 1, 24, 0, 0, 0),
    ],
)
def test_read_packed_vector(
    raw: bytes, scale_factor: int, max_bits: int, x: float, y: float, z: float
) -> None:
    result = BitReader(raw).read_packed_vector(scale_factor, max_bits)
    # C# 版は整数除算で小数を落とすが、本実装は UE と同じく実数で割る
    assert result.x == pytest.approx(x)
    assert result.y == pytest.approx(y)
    assert result.z == pytest.approx(z)


@pytest.mark.parametrize(
    "raw,raw2", [(b"\x99\xF1", b"\x21\xA1"), (b"\x81\xEE\x7A\x00\x06", b"\x84\xE3")]
)
def test_append_data_from_checked(raw: bytes, raw2: bytes) -> None:
    archive = BitReader(raw)
    assert archive.get_bits_left() == len(raw) * 8
    archive.append_data_from_checked(raw2, len(raw2) * 8)
    assert archive.get_bits_left() == (len(raw) + len(raw2)) * 8


# ---------------------------------------------------------------------------
# BinaryReader
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        bytes([0x00, 0x06, 0x00, 0x00, 0x00, 0x4C, 0x65, 0x76, 0x65, 0x6C, 0x00, 0x00, 0x00, 0x00, 0x00]),
        bytes([0x01, 0xAF, 0x02]),
    ],
)
def test_binary_reader_read_fname(raw: bytes) -> None:
    archive = BinaryReader(raw)
    archive.engine_network_version = (
        EngineNetworkVersionHistory.HISTORY_FAST_ARRAY_DELTA_STRUCT
    )
    archive.read_fname()
    assert archive.at_end()
    assert not archive.is_error


def test_binary_reader_read_ftransform() -> None:
    raw = bytes(
        [
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x3F,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x3F,
            0x00, 0x00, 0x80, 0x3F, 0x00, 0x00, 0x80, 0x3F,
        ]
    )
    archive = BinaryReader(raw)
    archive.read_ftransform()
    assert archive.at_end()
    assert not archive.is_error


# ---------------------------------------------------------------------------
# NetBitReader
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,bit_count,location,rotation,velocity,engine_version",
    [
        (
            bytes([0xD0, 0xD7, 0x07, 0x6F, 0xB0, 0xB3, 0x7F, 0x90, 0x01, 0xDD, 0x81, 0x0F, 0xE2, 0x0E, 0x20]),
            118,
            VectorQuantization.RoundTwoDecimals,
            RotatorQuantization.ByteComponents,
            VectorQuantization.RoundWholeNumber,
            EngineNetworkVersionHistory.HISTORY_INITIAL,
        ),
        (
            bytes([0x34, 0xC6, 0x7F, 0xF7, 0xA1, 0xB7, 0x8B, 0xB0, 0x9F, 0xA2, 0xFE, 0xDD, 0xD9, 0x25]),
            110,
            VectorQuantization.RoundOneDecimal,
            RotatorQuantization.ByteComponents,
            VectorQuantization.RoundWholeNumber,
            EngineNetworkVersionHistory.HISTORY_INITIAL,
        ),
        (
            bytes([
                0x5A, 0x45, 0x13, 0xEF, 0x35, 0xFC, 0xA4, 0x4E, 0x77, 0xBF, 0x00, 0xDE,
                0x1D, 0xD6, 0xF2, 0x18, 0xB0, 0x95, 0x4C, 0xF5, 0xD1, 0xF0, 0x14, 0x7E,
                0xA7, 0x97, 0x1B, 0x01,
            ]),
            218,
            VectorQuantization.RoundWholeNumber,
            RotatorQuantization.ShortComponents,
            VectorQuantization.RoundTwoDecimals,
            EngineNetworkVersionHistory.HISTORY_INITIAL,
        ),
        (
            bytes([
                0x5B, 0xAE, 0xF0, 0x14, 0x44, 0x01, 0x1E, 0x47, 0x02, 0xBD, 0xA7, 0xFF,
                0x4B, 0x10, 0xBA, 0xFF, 0x03, 0x15, 0xA8,
            ]),
            152,
            VectorQuantization.RoundTwoDecimals,
            RotatorQuantization.ShortComponents,
            VectorQuantization.RoundWholeNumber,
            EngineNetworkVersionHistory.HISTORY_INITIAL,
        ),
        (
            bytes([
                0x34, 0x88, 0xDF, 0x03, 0xE0, 0xE9, 0xCB, 0x3F, 0x92, 0x3B, 0x53, 0x3C,
                0x47, 0x61, 0xD6, 0x01,
            ]),
            122,
            VectorQuantization.RoundWholeNumber,
            RotatorQuantization.ByteComponents,
            VectorQuantization.RoundWholeNumber,
            EngineNetworkVersionHistory.HISTORY_INITIAL,
        ),
        (
            bytes([
                0x74, 0x20, 0x88, 0x53, 0x86, 0xDA, 0x16, 0xD8, 0x02, 0x40, 0x00, 0x38,
                0x2B, 0x00,
            ]),
            105,
            VectorQuantization.RoundWholeNumber,
            RotatorQuantization.ByteComponents,
            VectorQuantization.RoundWholeNumber,
            EngineNetworkVersionHistory.HISTORY_INITIAL,
        ),
        (
            bytes([
                0xDA, 0x34, 0x06, 0xCA, 0x0A, 0xFE, 0x68, 0x40, 0x29, 0xBE, 0xB9, 0xFF,
                0x83, 0x55, 0x1A, 0xF9, 0x47, 0xF2, 0xBD, 0xBE, 0x54, 0x3B, 0xFB, 0x88,
                0xAB, 0xBF, 0x70, 0xB3, 0xCB, 0x02,
            ]),
            236,
            VectorQuantization.RoundWholeNumber,
            RotatorQuantization.ShortComponents,
            VectorQuantization.RoundTwoDecimals,
            EngineNetworkVersionHistory.HISTORY_INITIAL,
        ),
        (
            bytes([
                0xA0, 0x65, 0x06, 0xE5, 0x68, 0x79, 0x0F, 0x60, 0xD8, 0x85, 0xFD, 0x05,
                0x15, 0x04,
            ]),
            111,
            VectorQuantization.RoundTwoDecimals,
            RotatorQuantization.ByteComponents,
            VectorQuantization.RoundWholeNumber,
            EngineNetworkVersionHistory.CustomExports,
        ),
    ],
)
def test_serialize_rep_movement(
    raw: bytes,
    bit_count: int,
    location: VectorQuantization,
    rotation: RotatorQuantization,
    velocity: VectorQuantization,
    engine_version: EngineNetworkVersionHistory,
) -> None:
    reader = NetBitReader(raw, bit_count)
    reader.engine_network_version = engine_version
    reader.serialize_rep_movement(location, rotation, velocity)
    assert not reader.is_error
    assert reader.at_end()


@pytest.mark.parametrize(
    "raw,bit_count,expected",
    [
        (
            bytes([
                0x08, 0x31, 0x00, 0x00, 0x00, 0x44, 0x45, 0x53, 0x4B, 0x54, 0x4F, 0x50,
                0x2D, 0x32, 0x32, 0x38, 0x4E, 0x47, 0x43, 0x35, 0x2D, 0x42, 0x39, 0x31,
                0x33, 0x37, 0x31, 0x30, 0x38, 0x34, 0x46, 0x46, 0x32, 0x46, 0x37, 0x45,
                0x35, 0x44, 0x36, 0x38, 0x38, 0x30, 0x31, 0x39, 0x35, 0x30, 0x35, 0x30,
                0x39, 0x41, 0x43, 0x31, 0x34, 0x00,
            ]),
            432,
            "DESKTOP-228NGC5-B91371084FF2F7E5D68801950509AC14",
        ),
        (
            bytes([
                0x11, 0x10, 0x37, 0xDF, 0x4A, 0x07, 0x98, 0xC2, 0x40, 0x2E, 0xAA, 0x62,
                0x69, 0x47, 0xEC, 0x29, 0x90, 0x3F,
            ]),
            144,
            "37DF4A0798C2402EAA626947EC29903F",
        ),
        (
            bytes([0x29, 0x08, 0x25, 0x35, 0x43, 0x94, 0x31, 0x47, 0x40, 0x39]),
            80,
            "2535439431474039",
        ),
    ],
)
def test_serialize_property_net_id(raw: bytes, bit_count: int, expected: str) -> None:
    reader = NetBitReader(raw, bit_count)
    assert reader.serialize_property_net_id() == expected
    assert not reader.is_error
    assert reader.at_end()


@pytest.mark.parametrize(
    "raw,x,y",
    [
        (bytes([0x00, 0x00, 0x00, 0x44, 0x00, 0x00, 0x00, 0x44]), 512, 512),
        (bytes([0x80, 0x00, 0xA0, 0x48, 0x30, 0x1F, 0x9E, 0x48]), 327684, 323833.5),
    ],
)
def test_serialize_property_vector2d(raw: bytes, x: float, y: float) -> None:
    reader = NetBitReader(raw)
    assert reader.serialize_property_vector2d() == FVector2D(x, y)
    assert not reader.is_error
    assert reader.at_end()


@pytest.mark.parametrize(
    "raw,expected",
    [
        (b"\x52\xEB", 0.8384655),
        (b"\x99\xA8", 0.31717888),
        (b"\xB8\xB8", 0.44312876),
    ],
)
def test_read_fixed_compressed_float(raw: bytes, expected: float) -> None:
    reader = NetBitReader(raw)
    assert reader.read_fixed_compressed_float(1, 16) == pytest.approx(expected, rel=1e-6)
    assert not reader.is_error
    assert reader.at_end()
