"""受信したプロパティを Python オブジェクトへ変換するパーサー。

C# 版の ``Unreal.Core.NetFieldParser`` に対応する。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field as _dc_field
from typing import Any

from .archives import NetBitReader
from .enums import ArchiveEndIndex, ParseMode, RepLayoutCmdType, RotatorQuantization
from .export_registry import (
    REGISTRY,
    ExportGroup,
    ExportRegistry,
    FieldDef,
    RepMovementSpec,
    RpcDef,
)
from .models import (
    NetFieldExport,
    NetFieldExportGroup,
    NetworkReplayVersion,
    Property,
    Resolvable,
)
from .net_guid_cache import NetGuidCache

logger = logging.getLogger(__name__)

#: ``++Fortnite+Release-41.30`` のようなブランチ名からメジャーバージョンを取り出す
_BRANCH_RELEASE_RE = re.compile(r"\+Release-(\d+)\.")

#: 回転が 16 ビットに拡大された最初の Fortnite ビルド 41.00 の変更リスト番号
#: (Shiqan/FortniteReplayDecompressor#77 で確認されたもの)
WIDE_ROTATION_CHANGELIST = 54618515

#: 回転が 16 ビットに拡大された最初の Fortnite のメジャーバージョン
WIDE_ROTATION_MAJOR_VERSION = 41


def uses_wide_rep_movement_rotation(version: NetworkReplayVersion | None) -> bool:
    """属性指定の無い ``RepMovement`` の回転が 16 ビットかどうかを判定する。

    Fortnite ビルド 41.00 で、``[RepMovement]`` 相当の指定を持たないアクター
    (PlayerPawn など) の回転量子化が 8 ビットから 16 ビットに拡大された。
    ``EngineNetworkVersion`` は 40.x / 41.x のどちらも 44 のままで区別できないため、
    リプレイのブランチ名と変更リスト番号から判定する。
    """
    if version is None:
        return False
    match = _BRANCH_RELEASE_RE.search(version.branch or "")
    if match:
        return int(match.group(1)) >= WIDE_ROTATION_MAJOR_VERSION
    return version.changelist >= WIDE_ROTATION_CHANGELIST


@dataclass
class GroupInfo:
    """解析時に使うエクスポートグループの情報。"""

    path: str
    cls: type[ExportGroup]
    uses_handles: bool = False
    fields_by_name: dict[str, FieldDef] = _dc_field(default_factory=dict)
    fields_by_handle: dict[int, FieldDef] = _dc_field(default_factory=dict)
    element_classes: set[type] = _dc_field(default_factory=set)


class NetFieldParser:
    """エクスポートグループ定義に従ってプロパティを読み取る。"""

    def __init__(
        self,
        cache: NetGuidCache,
        mode: ParseMode = ParseMode.Minimal,
        registry: ExportRegistry = REGISTRY,
    ) -> None:
        self.guid_cache = cache
        self.mode = mode
        self.registry = registry

        self._group_infos: list[GroupInfo] = []
        self._path_to_index: dict[str, int] = {}
        self._class_net_caches: dict[str, dict[str, RpcDef]] = {}

        for path, declaration in registry.groups.items():
            if declaration.parse_mode > mode:
                continue
            info = GroupInfo(path=path, cls=declaration.cls)
            info.element_classes = {declaration.cls, *declaration.extra_classes}
            base = declaration.cls.__base__
            if base is not None:
                info.element_classes.add(base)
            for definition in declaration.fields:
                if definition.parse_mode is not None and definition.parse_mode > mode:
                    continue
                if definition.handle is not None:
                    info.uses_handles = True
                    info.fields_by_handle[definition.handle] = definition
                else:
                    info.fields_by_name[definition.name] = definition
            self._path_to_index[path] = len(self._group_infos)
            self._group_infos.append(info)

        for path, declaration in registry.class_net_caches.items():
            if declaration.parse_mode > mode:
                continue
            self._class_net_caches[path] = {r.name: r for r in declaration.rpcs}

    # -- 問い合わせ ---------------------------------------------------------

    @property
    def player_controller_groups(self) -> set[str]:
        """プレイヤーコントローラーとして扱うパスの集合。"""
        return self.registry.player_controllers

    def will_read_type(self, group: str) -> bool:
        """このグループを解析する設定になっているか。"""
        return group in self._path_to_index

    def will_read_class_net_cache(self, group: str) -> bool:
        """この ClassNetCache を解析する設定になっているか。"""
        return group in self._class_net_caches

    def try_get_class_net_cache_property(self, prop: str, group: str) -> RpcDef | None:
        """ClassNetCache 内のプロパティ定義を取得する。"""
        properties = self._class_net_caches.get(group)
        if properties is None:
            return None
        return properties.get(prop)

    def create_type(self, group: str) -> ExportGroup | None:
        """エクスポートグループのインスタンスを生成する。"""
        index = self._path_to_index.get(group)
        if index is None:
            return None
        return self._group_infos[index].cls()

    def create_property_type(self, group: str, property_name: str) -> Property | None:
        """ClassNetCache のカスタムプロパティのインスタンスを生成する。"""
        definition = self.try_get_class_net_cache_property(property_name, group)
        if definition is None or definition.prop_type is None:
            return None
        return definition.prop_type()

    # -- 読み取り -----------------------------------------------------------

    def read_field(
        self,
        obj: ExportGroup,
        export: NetFieldExport,
        handle: int,
        export_group: NetFieldExportGroup,
        reader: NetBitReader,
    ) -> bool:
        """1 つのプロパティを読み取り ``obj`` に設定する。"""
        if export.property_id == -2 or export_group.group_id == -2:
            return False

        if export_group.group_id == -1:
            index = self._path_to_index.get(export_group.path_name)
            if index is None:
                export_group.group_id = -2
                return False
            export_group.group_id = index

        info = self._group_infos[export_group.group_id]

        if info.uses_handles:
            definition = info.fields_by_handle.get(handle)
            if definition is None:
                return False
        else:
            definition = info.fields_by_name.get(export.name)
            if definition is None:
                export.property_id = -2
                return False

        self._set_type(obj, definition, info, export_group, reader)
        return True

    def _set_type(
        self,
        obj: Any,
        definition: FieldDef,
        info: GroupInfo,
        export_group: NetFieldExportGroup,
        reader: NetBitReader,
    ) -> None:
        if definition.type == RepLayoutCmdType.DynamicArray:
            data = self._read_array_field(export_group, definition, info, reader)
        elif definition.type == RepLayoutCmdType.RepMovement:
            data = self._read_rep_movement(definition, reader)
        else:
            data = self._read_data_type(definition.type, reader, definition.prop_type)

        if data is not None and not reader.is_error:
            setattr(obj, definition.attr, data)

    def _read_rep_movement(self, definition: FieldDef, reader: NetBitReader) -> Any:
        """``RepMovement`` を読み取る。

        回転の量子化 (8 ビット / 16 ビット) はアクター側の設定で決まるため、
        属性指定が無いアクターではビルドによって切り替える必要がある
        (:func:`uses_wide_rep_movement_rotation` を参照)。
        判定を誤ってビット数が合わなかった場合は、もう一方の設定で読み直す。
        """
        movement = definition.movement
        if movement is not None:
            location = movement.location
            rotation = movement.rotation
            velocity = movement.velocity
        else:
            defaults = RepMovementSpec()
            location = defaults.location
            velocity = defaults.velocity
            rotation = (
                RotatorQuantization.ShortComponents
                if uses_wide_rep_movement_rotation(reader.network_replay_version)
                else RotatorQuantization.ByteComponents
            )

        data = reader.serialize_rep_movement(
            location_quantization_level=location,
            rotation_quantization_level=rotation,
            velocity_quantization_level=velocity,
        )
        if not reader.is_error and reader.at_end():
            return data

        alternate = (
            RotatorQuantization.ShortComponents
            if rotation == RotatorQuantization.ByteComponents
            else RotatorQuantization.ByteComponents
        )
        reader.reset()
        retry = reader.serialize_rep_movement(
            location_quantization_level=location,
            rotation_quantization_level=alternate,
            velocity_quantization_level=velocity,
        )
        if not reader.is_error and reader.at_end():
            logger.debug("RepMovement を %s で読み直しました", alternate.name)
            return retry

        return data

    def _read_data_type(
        self, layout: RepLayoutCmdType, reader: NetBitReader, prop_type: type | None
    ) -> Any:
        """``RepLayoutCmdType`` に応じてプロパティ 1 つ分を読み取る。"""
        if layout == RepLayoutCmdType.Property:
            if prop_type is None:
                reader.seek_to_end()
                return None
            data = prop_type()
            if isinstance(data, Property):
                data.serialize(reader)
            if isinstance(data, Resolvable):
                data.resolve(self.guid_cache)
            return data
        if layout == RepLayoutCmdType.PropertyBool:
            return reader.serialize_property_bool()
        if layout == RepLayoutCmdType.PropertyNativeBool:
            return reader.serialize_property_native_bool()
        if layout == RepLayoutCmdType.PropertyName:
            return reader.serialize_property_name()
        if layout == RepLayoutCmdType.PropertyFloat:
            return reader.serialize_property_float()
        if layout == RepLayoutCmdType.PropertyDouble:
            return reader.serialize_property_double()
        if layout == RepLayoutCmdType.PropertyNetId:
            return reader.serialize_property_net_id()
        if layout == RepLayoutCmdType.PropertyObject:
            return reader.serialize_property_object()
        if layout == RepLayoutCmdType.PropertyRotator:
            return reader.serialize_property_rotator()
        if layout == RepLayoutCmdType.PropertyString:
            return reader.serialize_property_string()
        if layout == RepLayoutCmdType.PropertyVector10:
            return reader.serialize_property_vector10()
        if layout == RepLayoutCmdType.PropertyVector100:
            return reader.serialize_property_vector100()
        if layout == RepLayoutCmdType.PropertyVectorNormal:
            return reader.serialize_property_vector_normal()
        if layout == RepLayoutCmdType.PropertyVectorQ:
            return reader.serialize_property_quantized_vector()
        if layout == RepLayoutCmdType.RepMovement:
            return reader.serialize_rep_movement()
        if layout == RepLayoutCmdType.Enum:
            return reader.serialize_property_enum()
        if layout == RepLayoutCmdType.PropertyByte:
            return reader.read_byte()
        if layout == RepLayoutCmdType.PropertyInt:
            return reader.read_int32()
        if layout == RepLayoutCmdType.PropertyInt16:
            return reader.read_int16()
        if layout == RepLayoutCmdType.PropertyUInt64:
            return reader.read_uint64()
        if layout == RepLayoutCmdType.PropertyUInt16:
            return reader.read_uint16()
        if layout == RepLayoutCmdType.PropertyUInt32:
            return reader.read_uint32()
        if layout == RepLayoutCmdType.PropertyVector:
            return reader.serialize_property_vector()
        if layout == RepLayoutCmdType.PropertyVector2D:
            return reader.serialize_property_vector2d()
        if layout == RepLayoutCmdType.PropertyPlane:
            raise NotImplementedError("PropertyPlane は未対応です")
        # Ignore などは読み飛ばす
        reader.seek_to_end()
        return None

    def _resolve_element(
        self, definition: FieldDef, info: GroupInfo
    ) -> tuple[bool, RepLayoutCmdType, type | None, type | None]:
        """配列要素の型を解決する。

        戻り値は ``(グループ型か, レイアウト, プロパティ型, 要素クラス)``。
        """
        element = definition.element
        if isinstance(element, type):
            if element in info.element_classes or issubclass(element, info.cls):
                return True, RepLayoutCmdType.Property, None, element
            if issubclass(element, Property):
                return False, RepLayoutCmdType.Property, element, element
            return False, RepLayoutCmdType.Ignore, None, None
        if isinstance(element, RepLayoutCmdType):
            return False, element, None, None
        return False, RepLayoutCmdType.Ignore, None, None

    def _read_array_field(
        self,
        export_group: NetFieldExportGroup,
        definition: FieldDef,
        info: GroupInfo,
        reader: NetBitReader,
    ) -> list[Any] | None:
        """動的配列プロパティを読み取る。"""
        array_indexes = reader.read_int_packed()
        is_group_type, layout, prop_type, element_cls = self._resolve_element(definition, info)

        if not is_group_type and layout == RepLayoutCmdType.Ignore:
            return None

        result: list[Any] = [None] * array_indexes

        while True:
            index = reader.read_int_packed()
            if index == 0:
                # 0 は配列の終端、または削除された末尾要素の終端を表す
                if reader.get_bits_left() == 8:
                    terminator = reader.read_int_packed()
                    if terminator != 0x00:
                        logger.debug("配列の終端が不正です: %s", terminator)
                return result

            index -= 1
            if index >= array_indexes:
                logger.debug("配列インデックスが範囲外です: %s >= %s", index, array_indexes)
                return result

            data: Any = element_cls() if is_group_type and element_cls is not None else None

            while True:
                handle = reader.read_int_packed()
                if handle == 0:
                    break
                handle -= 1
                if export_group.net_field_exports_length < handle:
                    return result
                export = export_group.net_field_exports[handle]
                num_bits = reader.read_int_packed()
                if num_bits == 0:
                    continue
                if export is None:
                    reader.skip_bits(num_bits)
                    continue
                reader.set_temp_end(num_bits, ArchiveEndIndex.READ_ARRAY_FIELD)
                try:
                    if is_group_type:
                        self.read_field(data, export, handle, export_group, reader)
                    else:
                        data = self._read_data_type(layout, reader, prop_type)
                finally:
                    reader.restore_temp_end(ArchiveEndIndex.READ_ARRAY_FIELD)

            result[index] = data
