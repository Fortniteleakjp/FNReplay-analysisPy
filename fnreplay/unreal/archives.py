"""バイト単位／ビット単位のアーカイブリーダー。

C# 版の ``FArchive`` / ``BinaryReader`` / ``BitReader`` / ``NetBitReader`` に対応する。

参考: https://github.com/EpicGames/UnrealEngine/blob/release/Engine/Source/Runtime/Core/Public/Serialization/Archive.h
"""

from __future__ import annotations

import math
import struct
from typing import Callable, TypeVar

from .enums import (
    EngineNetworkVersionHistory,
    NetworkVersionHistory,
    ReplayHeaderFlags,
    ReplayVersionHistory,
    RotatorQuantization,
    SeekOrigin,
    UniqueIdEncodingFlags,
    VectorQuantization,
)
from .models import (
    FQuat,
    FRepMovement,
    FRotator,
    FTransform,
    FVector,
    FVector2D,
    NetworkReplayVersion,
)
from .unreal_names import unreal_name

T = TypeVar("T")
U = TypeVar("U")

_UNPACK_I16 = struct.Struct("<h").unpack_from
_UNPACK_U16 = struct.Struct("<H").unpack_from
_UNPACK_I32 = struct.Struct("<i").unpack_from
_UNPACK_U32 = struct.Struct("<I").unpack_from
_UNPACK_I64 = struct.Struct("<q").unpack_from
_UNPACK_U64 = struct.Struct("<Q").unpack_from
_UNPACK_F32 = struct.Struct("<f").unpack_from
_UNPACK_F64 = struct.Struct("<d").unpack_from


class FArchive:
    """アーカイブの共通インターフェース。

    バージョン情報を保持し、``is_error`` で読み取り失敗を伝播する。
    """

    __slots__ = (
        "engine_network_version",
        "replay_header_flags",
        "network_version",
        "replay_version",
        "network_replay_version",
        "is_error",
    )

    def __init__(self) -> None:
        self.engine_network_version = EngineNetworkVersionHistory.HISTORY_INITIAL
        self.replay_header_flags = ReplayHeaderFlags.NONE
        self.network_version = NetworkVersionHistory.HISTORY_REPLAY_INITIAL
        self.replay_version = ReplayVersionHistory.HISTORY_INITIAL
        self.network_replay_version: NetworkReplayVersion | None = None
        self.is_error = False

    # -- 状態 ---------------------------------------------------------------

    def set_error(self) -> None:
        """エラー状態にする。"""
        self.is_error = True

    def reset(self) -> None:
        """位置とエラー状態を初期化する。"""
        self.is_error = False
        self.seek(0)

    def copy_version_from(self, other: "FArchive") -> "FArchive":
        """他のアーカイブからバージョン情報を引き継ぐ。"""
        self.engine_network_version = other.engine_network_version
        self.replay_header_flags = other.replay_header_flags
        self.network_version = other.network_version
        self.replay_version = other.replay_version
        self.network_replay_version = other.network_replay_version
        return self

    def has_level_streaming_fixes(self) -> bool:
        """レベルストリーミング修正を含むリプレイかどうか。"""
        return bool(self.replay_header_flags & ReplayHeaderFlags.HasStreamingFixes)

    def has_game_specific_frame_data(self) -> bool:
        """ゲーム固有のフレームデータを含むかどうか。"""
        return bool(self.replay_header_flags & ReplayHeaderFlags.GameSpecificFrameData)

    def has_delta_checkpoints(self) -> bool:
        """差分チェックポイントを使うかどうか。"""
        return bool(self.replay_header_flags & ReplayHeaderFlags.DeltaCheckpoints)

    # -- 抽象メソッド -------------------------------------------------------

    @property
    def position(self) -> int:
        raise NotImplementedError

    def at_end(self) -> bool:
        raise NotImplementedError

    def can_read(self, count: int) -> bool:
        raise NotImplementedError

    def seek(self, offset: int, origin: SeekOrigin = SeekOrigin.Begin) -> None:
        raise NotImplementedError

    def read_byte(self) -> int:
        raise NotImplementedError

    def read_bytes(self, count: int) -> bytes:
        raise NotImplementedError

    def read_boolean(self) -> bool:
        raise NotImplementedError

    def read_int16(self) -> int:
        raise NotImplementedError

    def read_uint16(self) -> int:
        raise NotImplementedError

    def read_int32(self) -> int:
        raise NotImplementedError

    def read_uint32(self) -> int:
        raise NotImplementedError

    def read_int64(self) -> int:
        raise NotImplementedError

    def read_uint64(self) -> int:
        raise NotImplementedError

    def read_single(self) -> float:
        raise NotImplementedError

    def read_double(self) -> float:
        raise NotImplementedError

    def read_int_packed(self) -> int:
        raise NotImplementedError

    def read_fstring(self) -> str:
        raise NotImplementedError

    def read_fname(self) -> str:
        raise NotImplementedError

    # -- 共通実装 -----------------------------------------------------------

    def skip_bytes(self, count: int) -> None:
        """指定バイト数を読み飛ばす。"""
        self.seek(count, SeekOrigin.Current)

    def read_bytes_to_string(self, count: int) -> str:
        """指定バイト数を大文字 16 進文字列として読み取る。"""
        return self.read_bytes(count).hex().upper()

    def read_guid(self, size: int = 16) -> str:
        """GUID を 16 進文字列として読み取る。"""
        return self.read_bytes_to_string(size)

    def read_int32_as_boolean(self) -> bool:
        """4 バイト整数を真偽値として読み取る。"""
        return self.read_int32() >= 1

    def read_uint32_as_boolean(self) -> bool:
        """4 バイト符号なし整数を真偽値として読み取る。"""
        return self.read_uint32() >= 1

    def read_uint32_as_enum(self, enum_type: type) -> object:
        """4 バイト符号なし整数を列挙型に変換して読み取る。"""
        return _to_enum(enum_type, self.read_uint32())

    def read_byte_as_enum(self, enum_type: type) -> object:
        """1 バイトを列挙型に変換して読み取る。"""
        return _to_enum(enum_type, self.read_byte())

    def read_array(self, func: Callable[[], T]) -> list[T]:
        """要素数プレフィックス付きの配列を読み取る。"""
        count = self.read_uint32()
        return [func() for _ in range(count)]

    def read_tuple_array(
        self, func1: Callable[[], T], func2: Callable[[], U]
    ) -> list[tuple[T, U]]:
        """要素数プレフィックス付きのタプル配列を読み取る。"""
        count = self.read_uint32()
        result: list[tuple[T, U]] = []
        for _ in range(count):
            first = func1()
            second = func2()
            result.append((first, second))
        return result


def _to_enum(enum_type: type, value: int):
    """値を列挙型に変換する。未定義値はそのまま整数で返す。"""
    try:
        return enum_type(value)
    except ValueError:
        return value


def _decode_fstring(raw: bytes, is_unicode: bool) -> str:
    """FString のバイト列をデコードして前後の空白と NUL を取り除く。"""
    text = raw.decode("utf-16-le" if is_unicode else "utf-8", errors="replace")
    return text.strip(" \0")


class BinaryReader(FArchive):
    """バイト境界のアーカイブリーダー。"""

    __slots__ = ("_buffer", "_length", "_position")

    def __init__(self, data: bytes | bytearray | memoryview) -> None:
        super().__init__()
        if hasattr(data, "read"):  # ファイルライクオブジェクト
            data = data.read()
        self._buffer = bytes(data)
        self._length = len(self._buffer)
        self._position = 0

    @property
    def buffer(self) -> bytes:
        """基になるバイト列。"""
        return self._buffer

    @property
    def position(self) -> int:
        return self._position

    def __len__(self) -> int:
        return self._length

    def at_end(self) -> bool:
        return self._position >= self._length

    def can_read(self, count: int) -> bool:
        return self._position + count < self._length

    def seek(self, offset: int, origin: SeekOrigin = SeekOrigin.Begin) -> None:
        if offset < 0 or offset > self._length or (
            origin == SeekOrigin.Current and offset + self._position > self._length
        ):
            self.is_error = True
            return
        if origin == SeekOrigin.Begin:
            self._position = offset
        elif origin == SeekOrigin.End:
            self._position = self._length - offset
        else:
            self._position += offset

    def skip_bytes(self, count: int) -> None:
        # C# 版は境界チェックせず加算するだけ
        self._position += count

    def read_boolean(self) -> bool:
        value = self._buffer[self._position]
        self._position += 1
        return value != 0

    def read_byte(self) -> int:
        value = self._buffer[self._position]
        self._position += 1
        return value

    def read_sbyte(self) -> int:
        value = self._buffer[self._position]
        self._position += 1
        return value - 256 if value > 127 else value

    def read_bytes(self, count: int) -> bytes:
        result = self._buffer[self._position : self._position + count]
        self._position += count
        return result

    def read_int16(self) -> int:
        value = _UNPACK_I16(self._buffer, self._position)[0]
        self._position += 2
        return value

    def read_uint16(self) -> int:
        value = _UNPACK_U16(self._buffer, self._position)[0]
        self._position += 2
        return value

    def read_int32(self) -> int:
        value = _UNPACK_I32(self._buffer, self._position)[0]
        self._position += 4
        return value

    def read_uint32(self) -> int:
        value = _UNPACK_U32(self._buffer, self._position)[0]
        self._position += 4
        return value

    def read_int64(self) -> int:
        value = _UNPACK_I64(self._buffer, self._position)[0]
        self._position += 8
        return value

    def read_uint64(self) -> int:
        value = _UNPACK_U64(self._buffer, self._position)[0]
        self._position += 8
        return value

    def read_single(self) -> float:
        value = _UNPACK_F32(self._buffer, self._position)[0]
        self._position += 4
        return value

    def read_double(self) -> float:
        value = _UNPACK_F64(self._buffer, self._position)[0]
        self._position += 8
        return value

    def read_int_packed(self) -> int:
        value = 0
        count = 0
        remaining = True
        while remaining:
            next_byte = self.read_byte()
            remaining = (next_byte & 1) == 1
            next_byte >>= 1
            value += next_byte << (7 * count)
            count += 1
        return value & 0xFFFFFFFF

    def read_fstring(self) -> str:
        length = self.read_int32()
        if length == 0:
            return ""
        is_unicode = length < 0
        if is_unicode:
            length = -2 * length
        return _decode_fstring(self.read_bytes(length), is_unicode)

    def read_fname(self) -> str:
        is_hardcoded = self.read_boolean()
        if is_hardcoded:
            if self.engine_network_version < EngineNetworkVersionHistory.HISTORY_CHANNEL_NAMES:
                name_index = self.read_uint32()
            else:
                name_index = self.read_int_packed()
            return unreal_name(name_index)
        value = self.read_fstring()
        self.read_int32()  # in_number
        return value

    def read_fvector(self) -> FVector:
        return FVector(self.read_single(), self.read_single(), self.read_single())

    def read_fquat(self) -> FQuat:
        return FQuat(
            self.read_single(), self.read_single(), self.read_single(), self.read_single()
        )

    def read_ftransform(self) -> FTransform:
        return FTransform(
            rotation=self.read_fquat(),
            translation=self.read_fvector(),
            scale_3d=self.read_fvector(),
        )

    def read_fvector_double(self) -> FVector:
        """倍精度 (UE5 の Large World Coordinates) のベクトルを読み取る。"""
        return FVector(self.read_double(), self.read_double(), self.read_double())

    def read_fquat_double(self) -> FQuat:
        """倍精度のクォータニオンを読み取る。"""
        return FQuat(
            self.read_double(), self.read_double(), self.read_double(), self.read_double()
        )


class BitReader(FArchive):
    """ビット境界のアーカイブリーダー。

    Unreal のビットストリームは各バイトの最下位ビットから順に読み進む。
    """

    __slots__ = ("_buffer", "_position", "last_bit", "mark_position", "_temp_last_bit")

    def __init__(self, data: bytes | bytearray | memoryview = b"", bit_count: int | None = None):
        super().__init__()
        self._buffer = bytes(data)
        self.last_bit = len(self._buffer) * 8 if bit_count is None else bit_count
        self._position = 0
        self.mark_position = 0
        self._temp_last_bit: dict[int, int] = {}

    # -- バッファ操作 -------------------------------------------------------

    def fill_buffer(self, data: bytes, bit_count: int | None = None) -> None:
        """バッファを差し替えて位置を先頭に戻す。"""
        self._buffer = bytes(data)
        self.last_bit = len(self._buffer) * 8 if bit_count is None else bit_count
        self._position = 0
        self.is_error = False

    @property
    def buffer(self) -> bytes:
        return self._buffer

    @property
    def position(self) -> int:
        return self._position

    @position.setter
    def position(self, value: int) -> None:
        self._position = value

    def at_end(self) -> bool:
        return self._position >= self.last_bit

    def can_read(self, count: int) -> bool:
        return self._position + count <= self.last_bit

    def get_bits_left(self) -> int:
        """残りビット数。"""
        return self.last_bit - self._position

    def mark(self) -> None:
        """現在位置を記憶する。"""
        self.mark_position = self._position

    def pop(self) -> None:
        """記憶した位置へ戻る。"""
        self._position = self.mark_position

    def seek(self, offset: int, origin: SeekOrigin = SeekOrigin.Begin) -> None:
        buffer_bits = len(self._buffer) * 8
        if (
            offset < 0
            or (offset >> 3) > len(self._buffer)
            or ((offset >> 3) == len(self._buffer) and (offset & 7) > 0)
            or (origin == SeekOrigin.Current and offset + self._position > buffer_bits)
        ):
            self.is_error = True
            return
        if origin == SeekOrigin.Begin:
            self._position = offset
        elif origin == SeekOrigin.End:
            self._position = buffer_bits - offset
        else:
            self._position += offset

    def skip_bits(self, bit_count: int) -> None:
        """指定ビット数を読み飛ばす。"""
        self.seek(bit_count, SeekOrigin.Current)

    def seek_to_end(self) -> None:
        """残りのビットをすべて読み飛ばす。"""
        self.seek(self.get_bits_left(), SeekOrigin.Current)

    def skip_bytes(self, count: int) -> None:
        self.seek(count * 8, SeekOrigin.Current)

    def reset(self) -> None:
        self.is_error = False
        self._position = 0

    def append_data_from_checked(self, data: bytes, bit_count: int) -> None:
        """部分バンチを連結する (連結地点はバイト境界であることが前提)。"""
        self.last_bit += bit_count
        self._buffer = self._buffer + bytes(data)

    def set_temp_end(self, size: int, index: int) -> None:
        """一時的に終端を手前へ移動する。``restore_temp_end`` と対で使う。"""
        set_position = self._position + size
        if set_position > self.last_bit:
            self.is_error = True
            return
        self._temp_last_bit[index] = self.last_bit
        self.last_bit = set_position

    def restore_temp_end(self, index: int) -> None:
        """``set_temp_end`` で縮めた終端を元に戻す。"""
        self._position = self.last_bit
        self.last_bit = self._temp_last_bit[index]
        self.is_error = False

    # -- ビット読み取り -----------------------------------------------------

    def peek_bit(self) -> bool:
        return (self._buffer[self._position >> 3] & (1 << (self._position & 7))) > 0

    def read_bit(self) -> bool:
        if self._position >= self.last_bit or self.is_error:
            self.is_error = True
            return False
        result = (self._buffer[self._position >> 3] & (1 << (self._position & 7))) > 0
        self._position += 1
        return result

    def read_boolean(self) -> bool:
        return self.read_bit()

    def _read_bits_value(self, bit_count: int) -> int:
        """``bit_count`` ビットを整数として取り出す (境界チェック済み前提)。"""
        position = self._position
        start = position >> 3
        end = (position + bit_count + 7) >> 3
        value = int.from_bytes(self._buffer[start:end], "little") >> (position & 7)
        self._position = position + bit_count
        return value & ((1 << bit_count) - 1)

    def read_bits(self, bit_count: int) -> bytes:
        """``bit_count`` ビットを読み取りバイト列として返す。"""
        if bit_count < 0 or not self.can_read(bit_count):
            self.is_error = True
            return b""
        if bit_count == 0:
            return b""
        position = self._position
        if (position & 7) == 0 and (bit_count & 7) == 0:
            # バイト境界にそろっている場合はスライスするだけでよい
            start = position >> 3
            self._position = position + bit_count
            return self._buffer[start : start + (bit_count >> 3)]
        value = self._read_bits_value(bit_count)
        return value.to_bytes((bit_count + 7) // 8, "little")

    def read_bits_to_int(self, bit_count: int) -> int:
        """``bit_count`` ビットを整数として読み取る。

        注意: C# 版はここで byte に丸めるため 8 ビットを超える指定では
        上位ビットが失われる。本実装は全ビットを保持する。
        """
        if bit_count <= 0:
            return 0
        if not self.can_read(bit_count):
            self.is_error = True
            return 0
        return self._read_bits_value(bit_count)

    def read_bits_to_long(self, bit_count: int) -> int:
        """``bit_count`` ビットを符号なし整数として読み取る。"""
        if bit_count <= 0:
            return 0
        if not self.can_read(bit_count):
            self.is_error = True
            return 0
        return self._read_bits_value(bit_count)

    def read_serialized_int(self, max_value: int) -> int:
        """0 以上 ``max_value`` 未満の整数を可変ビット長で読み取る。"""
        value = 0
        mask = 1
        while (value + mask) < max_value:
            if self.read_bit():
                value |= mask
            mask *= 2
        return value

    # -- バイト・数値読み取り ------------------------------------------------

    def peek_byte(self) -> int:
        result = self.read_byte()
        self._position -= 8
        return result

    def read_byte(self) -> int:
        # C# 版と同様、終端 (last_bit) ではなくバッファ長のみを見る
        if ((self._position + 8 + 7) >> 3) > len(self._buffer) + 1:
            self.is_error = True
            return 0
        try:
            return self._read_bits_value(8)
        except IndexError:  # pragma: no cover - 念のため
            self.is_error = True
            return 0

    def read_bytes(self, count: int) -> bytes:
        if count < 0 or not self.can_read(count * 8):
            self.is_error = True
            return b""
        if count == 0:
            return b""
        position = self._position
        if (position & 7) == 0:
            start = position >> 3
            self._position = position + count * 8
            return self._buffer[start : start + count]
        value = self._read_bits_value(count * 8)
        return value.to_bytes(count, "little")

    def read_int16(self) -> int:
        data = self.read_bytes(2)
        return 0 if self.is_error else _UNPACK_I16(data, 0)[0]

    def read_uint16(self) -> int:
        data = self.read_bytes(2)
        return 0 if self.is_error else _UNPACK_U16(data, 0)[0]

    def read_int32(self) -> int:
        data = self.read_bytes(4)
        return 0 if self.is_error else _UNPACK_I32(data, 0)[0]

    def read_uint32(self) -> int:
        data = self.read_bytes(4)
        return 0 if self.is_error else _UNPACK_U32(data, 0)[0]

    def read_int32_as_boolean(self) -> bool:
        return self.read_int32() == 1

    def read_int64(self) -> int:
        data = self.read_bytes(8)
        return 0 if self.is_error else _UNPACK_I64(data, 0)[0]

    def read_uint64(self) -> int:
        data = self.read_bytes(8)
        return 0 if self.is_error else _UNPACK_U64(data, 0)[0]

    def read_single(self) -> float:
        data = self.read_bytes(4)
        return 0.0 if self.is_error else _UNPACK_F32(data, 0)[0]

    def read_double(self) -> float:
        data = self.read_bytes(8)
        return 0.0 if self.is_error else _UNPACK_F64(data, 0)[0]

    def read_int_packed(self) -> int:
        """可変長エンコードされた符号なし整数を読み取る。"""
        bit_count_used_in_byte = self._position & 7
        bit_count_left_in_byte = 8 - bit_count_used_in_byte
        src_mask_byte0 = (1 << bit_count_left_in_byte) - 1
        src_mask_byte1 = (1 << bit_count_used_in_byte) - 1
        src_index = self._position >> 3
        next_src_index = src_index + 1 if bit_count_used_in_byte != 0 else src_index

        value = 0
        shift_count = 0
        buffer = self._buffer
        buffer_length = len(buffer)
        for _ in range(5):
            if not self.can_read(8):
                self.is_error = True
                break
            if next_src_index >= buffer_length:
                next_src_index = src_index
            self._position += 8
            read_byte = ((buffer[src_index] >> bit_count_used_in_byte) & src_mask_byte0) | (
                (buffer[next_src_index] & src_mask_byte1) << (bit_count_left_in_byte & 7)
            )
            read_byte &= 0xFF
            value |= (read_byte >> 1) << shift_count
            shift_count += 7
            src_index += 1
            next_src_index += 1
            if (read_byte & 1) == 0:
                break
        return value & 0xFFFFFFFF

    # -- 文字列 -------------------------------------------------------------

    def read_fstring(self) -> str:
        length = self.read_int32()
        if length == 0:
            return ""
        is_unicode = length < 0
        if is_unicode:
            length = -2 * length
        return _decode_fstring(self.read_bytes(length), is_unicode)

    def read_fname(self) -> str:
        is_hardcoded = self.read_bit()
        if is_hardcoded:
            if self.engine_network_version < EngineNetworkVersionHistory.HISTORY_CHANNEL_NAMES:
                name_index = self.read_uint32()
            else:
                name_index = self.read_int_packed()
            return unreal_name(name_index)
        value = self.read_fstring()
        self.read_int32()  # in_number
        return value

    # -- ベクトル・回転 -----------------------------------------------------

    def read_fvector(self) -> FVector:
        if (
            self.engine_network_version
            >= EngineNetworkVersionHistory.HISTORY_PACKED_VECTOR_LWC_SUPPORT
        ):
            return FVector(self.read_double(), self.read_double(), self.read_double())
        return FVector(self.read_single(), self.read_single(), self.read_single())

    def read_packed_vector(self, scale_factor: int, max_bits: int) -> FVector:
        """量子化されたベクトルを読み取る。"""
        if (
            self.engine_network_version
            >= EngineNetworkVersionHistory.HISTORY_PACKED_VECTOR_LWC_SUPPORT
            and self.engine_network_version
            != EngineNetworkVersionHistory.HISTORY_21_AND_VIEWPITCH_ONLY_DO_NOT_USE
        ):
            return self._read_quantized_vector(scale_factor)
        return self._read_packed_vector_legacy(scale_factor, max_bits)

    def _read_quantized_vector(self, scale_factor: int) -> FVector:
        component_bit_count_and_extra_info = self.read_serialized_int(1 << 7)
        component_bit_count = component_bit_count_and_extra_info & 63
        extra_info = component_bit_count_and_extra_info >> 6

        if component_bit_count > 0:
            x = self.read_bits_to_long(component_bit_count)
            y = self.read_bits_to_long(component_bit_count)
            z = self.read_bits_to_long(component_bit_count)
            sign_bit = 1 << (component_bit_count - 1)
            fx = float((x ^ sign_bit) - sign_bit)
            fy = float((y ^ sign_bit) - sign_bit)
            fz = float((z ^ sign_bit) - sign_bit)
            if extra_info > 0:
                fx /= scale_factor
                fy /= scale_factor
                fz /= scale_factor
            return FVector(fx, fy, fz, scale_factor=scale_factor, bits=component_bit_count)
        if extra_info == 0:
            return FVector(
                self.read_single(),
                self.read_single(),
                self.read_single(),
                scale_factor=scale_factor,
                bits=32,
            )
        return FVector(
            self.read_double(),
            self.read_double(),
            self.read_double(),
            scale_factor=scale_factor,
            bits=64,
        )

    def _read_packed_vector_legacy(self, scale_factor: int, max_bits: int) -> FVector:
        bits = self.read_serialized_int(max_bits)
        if self.is_error:
            return FVector(0, 0, 0)
        bias = 1 << (bits + 1)
        max_value = 1 << (bits + 2)
        dx = self.read_serialized_int(max_value)
        dy = self.read_serialized_int(max_value)
        dz = self.read_serialized_int(max_value)
        if self.is_error:
            return FVector(0, 0, 0)
        return FVector(
            (dx - bias) / scale_factor,
            (dy - bias) / scale_factor,
            (dz - bias) / scale_factor,
        )

    def read_rotation(self) -> FRotator:
        """1 成分 8 ビットの回転を読み取る。"""
        pitch = yaw = roll = 0.0
        if self.read_bit():
            pitch = self.read_byte() * 360 / 256
        if self.read_bit():
            yaw = self.read_byte() * 360 / 256
        if self.read_bit():
            roll = self.read_byte() * 360 / 256
        if self.is_error:
            return FRotator(0, 0, 0)
        return FRotator(pitch, yaw, roll)

    def read_rotation_short(self) -> FRotator:
        """1 成分 16 ビットの回転を読み取る。"""
        pitch = yaw = roll = 0.0
        if self.read_bit():
            pitch = self.read_uint16() * 360 / 65536
        if self.read_bit():
            yaw = self.read_uint16() * 360 / 65536
        if self.read_bit():
            roll = self.read_uint16() * 360 / 65536
        if self.is_error:
            return FRotator(0, 0, 0)
        return FRotator(pitch, yaw, roll)


class NetBitReader(BitReader):
    """プロパティの型ごとの読み取りを提供するビットリーダー。"""

    __slots__ = ()

    # -- 単純な型 -----------------------------------------------------------

    def serialize_property_int(self) -> int:
        return self.read_int32()

    def serialize_property_uint32(self) -> int:
        return self.read_uint32()

    def serialize_property_uint16(self) -> int:
        return self.read_uint16()

    def serialize_property_uint64(self) -> int:
        return self.read_uint64()

    def serialize_property_float(self) -> float:
        return self.read_single()

    def serialize_property_double(self) -> float:
        return self.read_double()

    def serialize_property_name(self) -> str:
        return self.read_fname()

    def serialize_property_string(self) -> str:
        return self.read_fstring()

    def serialize_property_bool(self) -> bool:
        return self.read_bit()

    def serialize_property_native_bool(self) -> bool:
        return self.read_bit()

    def serialize_property_byte(self, enum_max_value: int = 0) -> int:
        """列挙型の最大値が判っていればそのビット数で、無ければ 8 ビットで読む。"""
        if enum_max_value > 0:
            return self.read_bits_to_int(math.ceil(math.log2(enum_max_value)))
        return self.read_byte()

    def serialize_property_enum(self) -> int:
        return self.read_bits_to_int(self.get_bits_left())

    def serialize_property_object(self) -> int:
        return self.read_int_packed()

    # -- ベクトル -----------------------------------------------------------

    def serialize_property_vector(self) -> FVector:
        return self.read_fvector()

    def serialize_property_vector2d(self) -> FVector2D:
        return FVector2D(self.read_single(), self.read_single())

    def serialize_property_vector_normal(self) -> FVector:
        return FVector(
            self.read_fixed_compressed_float(1, 16),
            self.read_fixed_compressed_float(1, 16),
            self.read_fixed_compressed_float(1, 16),
        )

    def serialize_property_vector10(self) -> FVector:
        return self.read_packed_vector(10, 24)

    def serialize_property_vector100(self) -> FVector:
        return self.read_packed_vector(100, 30)

    def serialize_property_quantized_vector(
        self, quantization_level: VectorQuantization = VectorQuantization.RoundWholeNumber
    ) -> FVector:
        if quantization_level == VectorQuantization.RoundTwoDecimals:
            return self.read_packed_vector(100, 30)
        if quantization_level == VectorQuantization.RoundOneDecimal:
            return self.read_packed_vector(10, 27)
        return self.read_packed_vector(1, 24)

    def serialize_property_rotator(self) -> FRotator:
        return self.read_rotation_short()

    def read_fixed_compressed_float(self, max_value: int, num_bits: int) -> float:
        """固定小数点圧縮された float を読み取る。"""
        max_bit_value = (1 << (num_bits - 1)) - 1
        bias = 1 << (num_bits - 1)
        ser_int_max = 1 << num_bits
        delta = self.read_serialized_int(ser_int_max)
        unscaled_value = delta - bias
        if max_value > max_bit_value:
            return unscaled_value * (max_value / max_bit_value)
        scale = max_bit_value / max_value
        return unscaled_value * (1.0 / scale)

    # -- 複合型 -------------------------------------------------------------

    def serialize_rep_movement(
        self,
        location_quantization_level: VectorQuantization = VectorQuantization.RoundTwoDecimals,
        rotation_quantization_level: RotatorQuantization = RotatorQuantization.ByteComponents,
        velocity_quantization_level: VectorQuantization = VectorQuantization.RoundWholeNumber,
    ) -> FRepMovement:
        """アクターの移動情報を読み取る。"""
        simulated_physic_sleep = self.read_bit()
        rep_physics = self.read_bit()
        rep_server_frame = False
        rep_server_handle = False

        if (
            self.engine_network_version
            >= EngineNetworkVersionHistory.HISTORY_REPMOVE_SERVERFRAME_AND_HANDLE
            and self.engine_network_version
            != EngineNetworkVersionHistory.HISTORY_21_AND_VIEWPITCH_ONLY_DO_NOT_USE
        ):
            rep_server_frame = self.read_bit()
            rep_server_handle = self.read_bit()

        rep_movement = FRepMovement(
            simulated_physic_sleep=simulated_physic_sleep,
            rep_physics=rep_physics,
            location=self.serialize_property_quantized_vector(location_quantization_level),
            rotation=(
                self.read_rotation()
                if rotation_quantization_level == RotatorQuantization.ByteComponents
                else self.read_rotation_short()
            ),
            linear_velocity=self.serialize_property_quantized_vector(velocity_quantization_level),
            location_quantization_level=location_quantization_level,
            velocity_quantization_level=velocity_quantization_level,
            rotation_quantization_level=rotation_quantization_level,
        )

        if rep_movement.rep_physics:
            rep_movement.angular_velocity = self.serialize_property_quantized_vector(
                velocity_quantization_level
            )
            if (
                self.engine_network_version
                >= EngineNetworkVersionHistory.CongestionExperiencedBit
            ):
                # Unreal Engine 6.0 で追加されたテレポート連番 (3 ビット)。
                # エンジン側にバージョン判定は無く UE6 では常に送られるため、
                # UE6 で最初に採番されたネットワークバージョン 45 を境界として扱う。
                # see https://github.com/EpicGames/UnrealEngine/blob/ue6-main/Engine/Source/Runtime/Engine/Private/Engine/ReplicatedState.cpp
                rep_movement.teleport_seq = self.read_bits_to_int(3)
        if rep_server_frame:
            rep_movement.server_frame = self.read_int_packed()
        if rep_server_handle:
            rep_movement.server_physics_handle = self.read_int_packed()

        if self.engine_network_version >= EngineNetworkVersionHistory.RepMoveOptionalAcceleration:
            rep_movement.rep_acceleration = self.read_bit()
            if rep_movement.rep_acceleration:
                rep_movement.acceleration = self.serialize_property_quantized_vector(
                    velocity_quantization_level
                )

        return rep_movement

    def serialize_property_net_id(self) -> str:
        """オンラインサービスの一意 ID を読み取る。"""
        type_hash_other = 31

        encoding_flags = self.read_byte()
        encoded = False
        if encoding_flags & UniqueIdEncodingFlags.IsEncoded:
            encoded = True
            if encoding_flags & UniqueIdEncodingFlags.IsEmpty:
                return ""

        type_hash = (encoding_flags & int(UniqueIdEncodingFlags.TypeMask)) >> 3
        if type_hash == 0:
            return "NULL"

        valid_type_hash = True
        if type_hash == type_hash_other:
            type_string = self.read_fstring()
            if type_string == "None":
                valid_type_hash = False

        if valid_type_hash:
            if encoded:
                encoded_size = self.read_byte()
                return self.read_bytes_to_string(encoded_size)
            return self.read_fstring()
        return ""
