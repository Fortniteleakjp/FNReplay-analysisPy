"""C# の NetFieldExport 定義を Python へ変換するジェネレーター。

使い方::

    python tools/gen_exports.py <FortniteReplayReader のパス> <出力先 .py>

C# 側の属性 (``[NetFieldExportGroup]`` など) とプロパティ宣言を読み取り、
:mod:`fnreplay.unreal.export_registry` のデコレーター形式に変換する。
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# 手書きで移植したクラス (生成対象から除外する)
HANDWRITTEN = {
    "PlaylistInfo",
    "FQuantizedBuildingAttribute",
    "PlayerNameData",
    "FAthenaPawnReplayData",
}

# Unreal.Core 側の IProperty 実装
CORE_PROPERTY_TYPES = {
    "ActorGuid",
    "DebuggingObject",
    "FDateTime",
    "FGameplayAbilityRepAnimMontage",
    "FGameplayCueParameters",
    "FGameplayEffectContextHandle",
    "FGameplayTag",
    "FGameplayTagContainer",
    "FHitResult",
    "FName",
    "FPredictionKey",
    "FQuat",
    "FStaticName",
    "FText",
    "ItemDefinition",
    "NetworkGUID",
}

# C# の配列要素型 -> RepLayoutCmdType (NetFieldParser._primitiveTypeLayout 相当)
PRIMITIVE_ELEMENTS = {
    "bool": "PropertyBool",
    "byte": "PropertyByte",
    "ushort": "PropertyUInt16",
    "int": "PropertyInt",
    "uint": "PropertyUInt32",
    "ulong": "PropertyUInt64",
    "float": "PropertyFloat",
    "string": "PropertyString",
    "object": "Ignore",
}

ATTR_RE = re.compile(r"\[([A-Za-z]+)\((.*?)\)\]", re.DOTALL)
CLASS_RE = re.compile(
    r"public\s+(?:abstract\s+|sealed\s+|partial\s+)*class\s+(\w+)\s*(?::\s*([^{]+))?\{"
)
PROPERTY_RE = re.compile(r"public\s+([A-Za-z0-9_<>?]+(?:\[\])?)\s+(\w+)\s*\{\s*get")


@dataclass
class FieldInfo:
    """1 プロパティ分の情報。"""

    name: str | None
    handle: int | None
    attr: str
    cmd_type: str
    prop_type: str | None
    element: str | None
    parse_mode: str | None
    movement: tuple[str, str, str] | None


@dataclass
class RpcInfo:
    """ClassNetCache のエントリ情報。"""

    name: str
    path_name: str
    attr: str
    prop_type: str | None
    is_function: bool
    enable_property_checksum: bool
    is_custom_struct: bool


@dataclass
class ClassInfo:
    """1 クラス分の情報。"""

    name: str
    bases: list[str]
    kind: str  # group / subgroup / classnetcache / plain
    path: str | None = None
    parse_mode: str | None = None
    player_controller: str | None = None
    fields: list[FieldInfo] = field(default_factory=list)
    rpcs: list[RpcInfo] = field(default_factory=list)
    source: str = ""


def strip_comments(text: str) -> str:
    """行コメントを取り除く (文字列内の // は現れないため単純に処理する)。"""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        lines.append(line)
    return "\n".join(lines)


def to_snake(name: str) -> str:
    """C# のプロパティ名を Python の属性名に変換する。"""
    if name.startswith("b") and len(name) > 1 and name[1].isupper():
        name = "b_" + name[1:]
    result = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    result = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", result)
    result = result.replace("__", "_").lower()
    # "scale3_d" のような分割を "scale3d" に戻す
    result = re.sub(r"(\d)_([a-z])(?![a-z])", lambda m: m.group(1) + m.group(2), result)
    if result in {"class", "def", "import", "from", "global", "type", "id", "lambda", "None"}:
        result += "_"
    return result


def split_args(text: str) -> list[str]:
    """属性の引数をカンマで分割する (括弧・文字列を考慮)。"""
    args: list[str] = []
    depth = 0
    in_string = False
    current = ""
    for char in text:
        if in_string:
            current += char
            if char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            current += char
        elif char in "(<[":
            depth += 1
            current += char
        elif char in ")>]":
            depth -= 1
            current += char
        elif char == "," and depth == 0:
            args.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        args.append(current.strip())
    return args


def parse_attributes(text: str) -> list[tuple[str, list[str]]]:
    """属性の並びを ``(名前, 引数)`` のリストに変換する。"""
    return [(m.group(1), split_args(m.group(2))) for m in ATTR_RE.finditer(text)]


def find_class_body(text: str, start: int) -> tuple[str, int]:
    """``{`` の位置からクラス本体を取り出す。"""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
    raise ValueError("クラス本体の終端が見つかりません")


def unquote(value: str) -> str:
    return value.strip().strip('"')


def parse_class_attributes(info: ClassInfo, attributes: list[tuple[str, list[str]]]) -> None:
    for name, args in attributes:
        if name == "NetFieldExportGroup":
            info.kind = "group"
            info.path = unquote(args[0])
            info.parse_mode = _parse_mode(args[1:])
        elif name == "NetFieldExportSubGroup":
            info.kind = "subgroup"
            info.path = unquote(args[0])
            info.parse_mode = _parse_mode(args[1:])
        elif name == "NetFieldExportClassNetCache":
            info.kind = "classnetcache"
            info.path = unquote(args[0])
            info.parse_mode = _parse_mode(args[1:])
        elif name == "PlayerController":
            info.player_controller = unquote(args[0])


def _parse_mode(args: list[str]) -> str | None:
    for arg in args:
        if "ParseMode." in arg:
            return arg.split("ParseMode.")[1].strip().rstrip(")")
    return None


def parse_property_attributes(
    attributes: list[tuple[str, list[str]]], cs_type: str, cs_name: str
) -> FieldInfo | RpcInfo | None:
    movement: tuple[str, str, str] | None = None
    for name, args in attributes:
        if name == "RepMovement":
            location = "RoundTwoDecimals"
            rotation = "ByteComponents"
            velocity = "RoundWholeNumber"
            for arg in args:
                if "locationQuantizationLevel" in arg:
                    location = arg.split("VectorQuantization.")[1]
                elif "rotationQuantizationLevel" in arg:
                    rotation = arg.split("RotatorQuantization.")[1]
                elif "velocityQuantizationLevel" in arg:
                    velocity = arg.split("VectorQuantization.")[1]
            movement = (location, rotation, velocity)

    for name, args in attributes:
        if name == "NetFieldExport":
            cmd_type = args[1].split("RepLayoutCmdType.")[1].strip()
            parse_mode = _parse_mode(args[2:])
            prop_type, element = resolve_types(cs_type, cmd_type)
            return FieldInfo(
                name=unquote(args[0]),
                handle=None,
                attr=to_snake(cs_name),
                cmd_type=cmd_type,
                prop_type=prop_type,
                element=element,
                parse_mode=parse_mode,
                movement=movement,
            )
        if name == "NetFieldExportHandle":
            cmd_type = args[1].split("RepLayoutCmdType.")[1].strip()
            parse_mode = _parse_mode(args[2:])
            prop_type, element = resolve_types(cs_type, cmd_type)
            return FieldInfo(
                name=None,
                handle=int(args[0]),
                attr=to_snake(cs_name),
                cmd_type=cmd_type,
                prop_type=prop_type,
                element=element,
                parse_mode=parse_mode,
                movement=movement,
            )
        if name == "NetFieldExportRPC":
            is_function = any("isFunction: true" in a for a in args)
            checksum = not any("enablePropertyChecksum: false" in a for a in args)
            custom_struct = any("customStruct: true" in a for a in args)
            prop_type = cs_type.rstrip("?").replace("[]", "")
            return RpcInfo(
                name=unquote(args[0]),
                path_name=unquote(args[1]),
                attr=to_snake(cs_name),
                prop_type=prop_type,
                is_function=is_function,
                enable_property_checksum=checksum,
                is_custom_struct=custom_struct,
            )
    return None


def resolve_types(cs_type: str, cmd_type: str) -> tuple[str | None, str | None]:
    """C# の型から Python 側の prop_type / element を決める。"""
    base_type = cs_type.rstrip("?")
    if base_type.endswith("[]"):
        element_type = base_type[:-2].rstrip("?")
        if element_type in PRIMITIVE_ELEMENTS:
            return None, f"RepLayoutCmdType.{PRIMITIVE_ELEMENTS[element_type]}"
        return None, element_type
    if cmd_type == "Property":
        return base_type, None
    return None, None


def parse_file(path: Path) -> list[ClassInfo]:
    """1 ファイルからクラス情報を取り出す。"""
    text = strip_comments(path.read_text(encoding="utf-8-sig"))
    classes: list[ClassInfo] = []
    parse_scope(text, path.name, classes)
    return classes


def parse_scope(text: str, source: str, classes: list[ClassInfo]) -> None:
    """1 つのスコープ内のクラス (入れ子を含む) を解析する。"""
    pos = 0
    while True:
        match = CLASS_RE.search(text, pos)
        if match is None:
            break

        # クラス宣言直前の属性をまとめて取得する
        preceding = text[:match.start()]
        attribute_block = ""
        for line in reversed(preceding.rstrip().splitlines()):
            stripped = line.strip()
            if not stripped:
                if attribute_block:
                    break
                continue
            if stripped.endswith("]") or stripped.endswith(",") or stripped.startswith("["):
                attribute_block = line + "\n" + attribute_block
            else:
                break

        bases = [b.strip() for b in (match.group(2) or "").split(",") if b.strip()]
        info = ClassInfo(
            name=match.group(1),
            bases=[b for b in bases if not b.startswith("I")],
            kind="plain",
            source=source,
        )
        parse_class_attributes(info, parse_attributes(attribute_block))

        body, end = find_class_body(text, match.end() - 1)
        pos = end

        # 入れ子になったクラスを先に処理し、その範囲はプロパティ探索から除外する
        nested_ranges: list[tuple[int, int]] = []
        nested_pos = 0
        while True:
            nested = CLASS_RE.search(body, nested_pos)
            if nested is None:
                break
            _, nested_end = find_class_body(body, nested.end() - 1)
            nested_ranges.append((nested.start(), nested_end))
            nested_pos = nested_end
        if nested_ranges:
            parse_scope(body, source, classes)

        # プロパティを順に取り出す
        prop_pos = 0
        while True:
            prop = PROPERTY_RE.search(body, prop_pos)
            if prop is None:
                break
            if any(start <= prop.start() < stop for start, stop in nested_ranges):
                prop_pos = prop.end()
                continue
            preceding_body = body[:prop.start()]
            attribute_block = ""
            for line in reversed(preceding_body.rstrip().splitlines()):
                stripped = line.strip()
                if not stripped:
                    if attribute_block:
                        break
                    continue
                if stripped.endswith("]") or stripped.endswith(",") or stripped.startswith("["):
                    attribute_block = line + "\n" + attribute_block
                else:
                    break
            parsed = parse_property_attributes(
                parse_attributes(attribute_block), prop.group(1), prop.group(2)
            )
            if isinstance(parsed, FieldInfo):
                info.fields.append(parsed)
            elif isinstance(parsed, RpcInfo):
                info.rpcs.append(parsed)
            prop_pos = prop.end()

        resolve_attribute_collisions(info)
        classes.append(info)


def resolve_attribute_collisions(info: ClassInfo) -> None:
    """同じクラス内で属性名が衝突した場合に名前を調整する。

    ``PlayerId`` と ``PlayerID`` のように大文字小文字だけが異なる古い名前は
    ``*_legacy`` を付けて区別する。
    """
    seen: dict[str, FieldInfo] = {}
    for f in info.fields:
        if f.attr not in seen:
            seen[f.attr] = f
            continue
        previous = seen[f.attr]
        original = f.name or ""
        previous_original = previous.name or ""
        # 全部大文字で終わる方 (PlayerID など) を legacy 扱いにする
        if original[-2:].isupper() and not previous_original[-2:].isupper():
            f.attr = f"{f.attr}_legacy"
        elif previous_original[-2:].isupper() and not original[-2:].isupper():
            previous.attr = f"{previous.attr}_legacy"
            seen[f.attr] = f
        else:
            f.attr = f"{f.attr}_2"
        seen[f.attr] = f


def topological_sort(classes: list[ClassInfo]) -> list[ClassInfo]:
    """基底クラスと参照型が先に来るように並べ替える。"""
    by_name = {c.name: c for c in classes}
    ordered: list[ClassInfo] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(info: ClassInfo) -> None:
        if info.name in visited:
            return
        if info.name in visiting:
            return
        visiting.add(info.name)

        dependencies: list[str] = list(info.bases)
        for f in info.fields:
            for candidate in (f.prop_type, f.element):
                if candidate and not candidate.startswith("RepLayoutCmdType."):
                    dependencies.append(candidate)
        for r in info.rpcs:
            if r.prop_type:
                dependencies.append(r.prop_type)

        for dependency in dependencies:
            target = by_name.get(dependency)
            if target is not None and target is not info:
                visit(target)

        visiting.discard(info.name)
        visited.add(info.name)
        ordered.append(info)

    # ClassNetCache は最後に回す
    for info in classes:
        if info.kind != "classnetcache":
            visit(info)
    for info in classes:
        visit(info)

    return ordered


def python_type_ref(name: str, known: set[str]) -> str:
    """Python 側の型参照を返す。"""
    if name.startswith("RepLayoutCmdType."):
        return name
    if name in known or name in CORE_PROPERTY_TYPES:
        return name
    return "None"


def render(classes: list[ClassInfo]) -> str:
    """Python モジュールのソースを生成する。"""
    known = {c.name for c in classes} | CORE_PROPERTY_TYPES | HANDWRITTEN

    # RPC を (継承も含めて) 持つクラスを洗い出す
    by_name = {c.name: c for c in classes}
    rpc_classes: set[str] = set()
    for info in classes:
        current: ClassInfo | None = info
        while current is not None:
            if current.rpcs:
                rpc_classes.add(info.name)
                break
            current = by_name.get(current.bases[0]) if current.bases else None
    lines: list[str] = [
        '"""Fortnite のネットフィールドエクスポート定義。',
        "",
        "このファイルは ``tools/gen_exports.py`` により",
        "Shiqan/FortniteReplayDecompressor の C# 定義から生成されている。",
        "手で編集せず、ジェネレーターを更新すること。",
        '"""',
        "",
        "# ruff: noqa: E501",
        "from __future__ import annotations",
        "",
        "from ...unreal.enums import ParseMode, RepLayoutCmdType",
        "from ...unreal.export_registry import (",
        "    ExportGroup,",
        "    RepMovementSpec,",
        "    class_net_cache,",
        "    export_group,",
        "    export_subgroup,",
        "    field,",
        "    handle_field,",
        "    player_controller,",
        "    rpc,",
        ")",
        "from ...unreal.enums import RotatorQuantization, VectorQuantization",
        "from ...unreal.models import (",
        "    ActorGuid,",
        "    FDateTime,",
        "    FGameplayAbilityRepAnimMontage,",
        "    FGameplayCueParameters,",
        "    FGameplayEffectContextHandle,",
        "    FGameplayTag,",
        "    FGameplayTagContainer,",
        "    FHitResult,",
        "    FName,",
        "    FPredictionKey,",
        "    FQuat,",
        "    FStaticName,",
        "    FText,",
        "    ItemDefinition,",
        "    NetworkGUID,",
        ")",
        "from .handwritten import (",
        "    DebuggingObject,",
        "    FAthenaPawnReplayData,",
        "    FQuantizedBuildingAttribute,",
        "    PlaylistInfo,",
        ")",
        "",
        "",
    ]

    for info in classes:
        if info.name in HANDWRITTEN:
            continue

        decorators: list[str] = []
        if info.kind == "group":
            mode = f", ParseMode.{info.parse_mode}" if info.parse_mode else ""
            decorators.append(f'@export_group("{info.path}"{mode})')
        elif info.kind == "subgroup":
            mode = f", ParseMode.{info.parse_mode}" if info.parse_mode else ""
            decorators.append(f'@export_subgroup("{info.path}"{mode})')
        elif info.kind == "classnetcache":
            mode = f", ParseMode.{info.parse_mode}" if info.parse_mode else ""
            decorators.append(f'@class_net_cache("{info.path}"{mode})')
        if info.player_controller:
            decorators.append(f'@player_controller("{info.player_controller}")')

        base = info.bases[0] if info.bases else None
        if base is None:
            base_name = "object" if info.kind == "classnetcache" else "ExportGroup"
        else:
            base_name = base

        lines.extend(decorators)
        lines.append(f"class {info.name}({base_name}):")
        lines.append(f'    """{info.path or info.name} ({info.source})。"""')
        lines.append("")

        if info.rpcs:
            prefix = f"{base}.RPCS + " if base and base in rpc_classes else ""
            lines.append(f"    RPCS = {prefix}[")
            for r in info.rpcs:
                prop_type = python_type_ref(r.prop_type or "", known)
                args = [f'"{r.name}"', f'"{r.path_name}"', f'attr="{r.attr}"']
                if prop_type != "None":
                    args.append(f"prop_type={prop_type}")
                if r.is_function:
                    args.append("is_function=True")
                if not r.enable_property_checksum:
                    args.append("enable_property_checksum=False")
                if r.is_custom_struct:
                    args.append("is_custom_struct=True")
                lines.append(f"        rpc({', '.join(args)}),")
            lines.append("    ]")
        elif info.fields:
            prefix = f"{base}.FIELDS + " if base else ""
            lines.append(f"    FIELDS = {prefix}[")
            for f in info.fields:
                args: list[str] = []
                if f.handle is not None:
                    call = "handle_field"
                    args.append(str(f.handle))
                else:
                    call = "field"
                    args.append(f'"{f.name}"')
                args.append(f'"{f.attr}"')
                args.append(f"RepLayoutCmdType.{f.cmd_type}")
                if f.prop_type:
                    args.append(f"prop_type={python_type_ref(f.prop_type, known)}")
                if f.element:
                    args.append(f"element={python_type_ref(f.element, known)}")
                if f.parse_mode:
                    args.append(f"parse_mode=ParseMode.{f.parse_mode}")
                if f.movement:
                    args.append(
                        "movement=RepMovementSpec("
                        f"VectorQuantization.{f.movement[0]}, "
                        f"RotatorQuantization.{f.movement[1]}, "
                        f"VectorQuantization.{f.movement[2]})"
                    )
                lines.append(f"        {call}({', '.join(args)}),")
            lines.append("    ]")
        elif base and base in rpc_classes:
            lines.append(f"    RPCS = {base}.RPCS")
        elif base:
            lines.append(f"    FIELDS = {base}.FIELDS")
        else:
            lines.append("    FIELDS = []")

        lines.append("")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    root = Path(sys.argv[1])
    output = Path(sys.argv[2])

    classes: list[ClassInfo] = []
    for path in sorted(root.rglob("*.cs")):
        if path.name in {f"{n}.cs" for n in HANDWRITTEN}:
            continue
        classes.extend(parse_file(path))

    # 属性を持たず参照もされないクラスは出力しない
    referenced: set[str] = set()
    for info in classes:
        referenced.update(info.bases)
        for f in info.fields:
            for candidate in (f.prop_type, f.element):
                if candidate and not candidate.startswith("RepLayoutCmdType."):
                    referenced.add(candidate)
        for r in info.rpcs:
            if r.prop_type:
                referenced.add(r.prop_type)

    classes = [
        c
        for c in classes
        if c.kind != "plain" or c.name in referenced or c.player_controller
    ]

    ordered = topological_sort(classes)
    output.write_text(render(ordered), encoding="utf-8")
    print(f"{len(ordered)} classes -> {output}")


if __name__ == "__main__":
    main()
