"""C# の UnrealNames.cs から Python の名前テーブルを生成する補助スクリプト。"""
import re
import sys

src = open(sys.argv[1], encoding="utf-8-sig").read()
body = src.split("public enum UnrealNames", 1)[1]
body = body.split("{", 1)[1].rsplit("}", 1)[0]

entries = []
current = -1
for line in body.splitlines():
    line = re.sub(r"//.*", "", line).strip().rstrip(",")
    if not line:
        continue
    m = re.match(r"^(\w+)\s*=\s*(-?\d+)$", line)
    if m:
        current = int(m.group(2))
        entries.append((current, m.group(1)))
        continue
    m = re.match(r"^(\w+)$", line)
    if m:
        current += 1
        entries.append((current, m.group(1)))
        continue
    raise SystemExit(f"parse error: {line!r}")

out = ['"""ハードコードされた Unreal の名前テーブル (UnrealNames.inl)。',
       "",
       "https://github.com/EpicGames/UnrealEngine/blob/release/Engine/Source/Runtime/Core/Public/UObject/UnrealNames.inl",
       '"""',
       "",
       "UNREAL_NAMES: dict[int, str] = {"]
for value, name in entries:
    out.append(f'    {value}: "{name}",')
out.append("}")
out.append("")
out.append("")
out.append("def unreal_name(index: int) -> str:")
out.append('    """名前インデックスを文字列に変換する。未知の場合はインデックスをそのまま返す。"""')
out.append("    return UNREAL_NAMES.get(index, str(index))")
out.append("")
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(out))
print(f"{len(entries)} names")
