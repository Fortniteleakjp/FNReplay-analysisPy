"""ネットフィールドエクスポートを宣言するための仕組み。

C# 版では属性 (``[NetFieldExportGroup]`` など) で宣言していた情報を、
Python ではクラス変数とデコレーターで表現する。

例::

    @export_group("/Game/Athena/SafeZone/SafeZoneIndicator.SafeZoneIndicator_C")
    class SafeZoneIndicator(ExportGroup):
        FIELDS = [
            field("Radius", "radius", RepLayoutCmdType.PropertyFloat),
        ]
"""

from __future__ import annotations

from dataclasses import dataclass, field as _dc_field
from typing import Any, Callable, Iterable

from .enums import ParseMode, RepLayoutCmdType, RotatorQuantization, VectorQuantization


@dataclass(frozen=True)
class RepMovementSpec:
    """``RepMovement`` プロパティの量子化設定。"""

    location: VectorQuantization = VectorQuantization.RoundTwoDecimals
    rotation: RotatorQuantization = RotatorQuantization.ByteComponents
    velocity: VectorQuantization = VectorQuantization.RoundWholeNumber


@dataclass(frozen=True)
class FieldDef:
    """1 つのネットフィールドの定義。"""

    name: str | None
    attr: str
    type: RepLayoutCmdType
    prop_type: type | None = None
    element: Any = None
    parse_mode: ParseMode | None = None
    handle: int | None = None
    movement: RepMovementSpec | None = None


def field(
    name: str,
    attr: str,
    cmd_type: RepLayoutCmdType,
    prop_type: type | None = None,
    element: Any = None,
    parse_mode: ParseMode | None = None,
    movement: RepMovementSpec | None = None,
) -> FieldDef:
    """プロパティ名で対応づけるネットフィールドを定義する。"""
    return FieldDef(
        name=name,
        attr=attr,
        type=cmd_type,
        prop_type=prop_type,
        element=element,
        parse_mode=parse_mode,
        movement=movement,
    )


def handle_field(
    handle: int,
    attr: str,
    cmd_type: RepLayoutCmdType,
    prop_type: type | None = None,
    element: Any = None,
    parse_mode: ParseMode | None = None,
    movement: RepMovementSpec | None = None,
) -> FieldDef:
    """ハンドル番号で対応づけるネットフィールドを定義する。"""
    return FieldDef(
        name=None,
        attr=attr,
        type=cmd_type,
        prop_type=prop_type,
        element=element,
        parse_mode=parse_mode,
        handle=handle,
        movement=movement,
    )


@dataclass(frozen=True)
class RpcDef:
    """ClassNetCache 内の RPC / カスタムプロパティ定義。"""

    name: str
    path_name: str
    attr: str = ""
    prop_type: type | None = None
    is_function: bool = False
    enable_property_checksum: bool = True
    is_custom_struct: bool = False


def rpc(
    name: str,
    path_name: str,
    attr: str = "",
    prop_type: type | None = None,
    is_function: bool = False,
    enable_property_checksum: bool = True,
    is_custom_struct: bool = False,
) -> RpcDef:
    """ClassNetCache のエントリを定義する。"""
    return RpcDef(
        name=name,
        path_name=path_name,
        attr=attr,
        prop_type=prop_type,
        is_function=is_function,
        enable_property_checksum=enable_property_checksum,
        is_custom_struct=is_custom_struct,
    )


class ExportGroup:
    """ネットフィールドエクスポートの基底クラス。

    宣言されたフィールドはクラス属性として ``None`` に初期化されるため、
    未受信のプロパティを参照しても ``AttributeError`` にならない。
    """

    #: このクラスが表すエクスポートグループのパス
    PATH: str = ""
    #: このクラスに含まれるフィールド定義
    FIELDS: list[FieldDef] = []

    def to_dict(self) -> dict[str, Any]:
        """受信済みのプロパティのみを辞書化する。"""
        return dict(vars(self))

    def __repr__(self) -> str:
        values = ", ".join(f"{k}={v!r}" for k, v in vars(self).items())
        return f"{type(self).__name__}({values})"


@dataclass
class GroupDeclaration:
    """1 つのエクスポートグループの宣言内容。"""

    path: str
    cls: type[ExportGroup]
    parse_mode: ParseMode
    fields: list[FieldDef] = _dc_field(default_factory=list)
    #: サブグループとして後から追加されたフィールドの持ち主クラス
    extra_classes: list[type] = _dc_field(default_factory=list)


@dataclass
class ClassNetCacheDeclaration:
    """1 つの ClassNetCache の宣言内容。"""

    path: str
    cls: type
    parse_mode: ParseMode
    rpcs: list[RpcDef] = _dc_field(default_factory=list)


class ExportRegistry:
    """エクスポートグループの登録簿。"""

    def __init__(self) -> None:
        self.groups: dict[str, GroupDeclaration] = {}
        self.class_net_caches: dict[str, ClassNetCacheDeclaration] = {}
        self.player_controllers: set[str] = set()
        #: 親より先に宣言されたサブグループを保持する
        self._pending_subgroups: dict[str, list[tuple[type, list[FieldDef]]]] = {}

    # -- 登録 ---------------------------------------------------------------

    def add_group(
        self, path: str, cls: type[ExportGroup], parse_mode: ParseMode, fields: Iterable[FieldDef]
    ) -> None:
        declaration = GroupDeclaration(path=path, cls=cls, parse_mode=parse_mode)
        declaration.fields.extend(fields)
        self.groups[path] = declaration

        for subgroup_cls, subgroup_fields in self._pending_subgroups.pop(path, []):
            declaration.extra_classes.append(subgroup_cls)
            declaration.fields.extend(subgroup_fields)
            _init_class_attributes(cls, subgroup_fields)

    def add_subgroup(
        self, path: str, cls: type, parse_mode: ParseMode, fields: Iterable[FieldDef]
    ) -> None:
        fields = list(fields)
        declaration = self.groups.get(path)
        if declaration is None:
            # 親グループがまだ登録されていない場合は保留する
            self._pending_subgroups.setdefault(path, []).append((cls, fields))
            return
        declaration.extra_classes.append(cls)
        declaration.fields.extend(fields)

    def add_class_net_cache(
        self, path: str, cls: type, parse_mode: ParseMode, rpcs: Iterable[RpcDef]
    ) -> None:
        declaration = ClassNetCacheDeclaration(path=path, cls=cls, parse_mode=parse_mode)
        declaration.rpcs.extend(rpcs)
        self.class_net_caches[path] = declaration

    def add_player_controller(self, path: str) -> None:
        self.player_controllers.add(path)


#: 既定の登録簿 (デコレーターはここに登録する)
REGISTRY = ExportRegistry()


def _init_class_attributes(cls: type, fields: Iterable[FieldDef]) -> None:
    """フィールドの既定値 (None) をクラス属性として用意する。"""
    for definition in fields:
        if not hasattr(cls, definition.attr):
            setattr(cls, definition.attr, None)


def export_group(
    path: str,
    minimal_parse_mode: ParseMode = ParseMode.Normal,
    registry: ExportRegistry = REGISTRY,
) -> Callable[[type], type]:
    """クラスをエクスポートグループとして登録するデコレーター。"""

    def decorator(cls: type) -> type:
        fields = list(getattr(cls, "FIELDS", []))
        cls.PATH = path
        _init_class_attributes(cls, fields)
        registry.add_group(path, cls, minimal_parse_mode, fields)
        return cls

    return decorator


def export_subgroup(
    path: str,
    minimal_parse_mode: ParseMode = ParseMode.Normal,
    registry: ExportRegistry = REGISTRY,
) -> Callable[[type], type]:
    """既存のエクスポートグループにフィールドを追加するデコレーター。"""

    def decorator(cls: type) -> type:
        fields = list(getattr(cls, "FIELDS", []))
        cls.PATH = path
        parent = registry.groups.get(path)
        if parent is not None:
            _init_class_attributes(parent.cls, fields)
        registry.add_subgroup(path, cls, minimal_parse_mode, fields)
        return cls

    return decorator


def class_net_cache(
    path: str,
    minimal_parse_mode: ParseMode = ParseMode.Normal,
    registry: ExportRegistry = REGISTRY,
) -> Callable[[type], type]:
    """クラスを ClassNetCache として登録するデコレーター。"""

    def decorator(cls: type) -> type:
        rpcs = list(getattr(cls, "RPCS", []))
        cls.PATH = path
        registry.add_class_net_cache(path, cls, minimal_parse_mode, rpcs)
        return cls

    return decorator


def player_controller(
    path: str, registry: ExportRegistry = REGISTRY
) -> Callable[[type], type]:
    """プレイヤーコントローラーのパスを登録するデコレーター。"""

    def decorator(cls: type) -> type:
        registry.add_player_controller(path)
        return cls

    return decorator
