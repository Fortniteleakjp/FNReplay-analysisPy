"""パス名を正規化するためのヘルパー。

C# 版の ``StringExtensions`` に対応する。
"""

from __future__ import annotations


def remove_all_path_prefixes(path: str) -> str:
    """``/Game/Foo/Bar.Bar_C`` のようなパスから最後の ``.`` 以降を取り出す。

    ``/`` が先に見つかった場合はパスをそのまま返し、どちらも無い場合は
    ``Default__`` プレフィックスだけを取り除く。
    """
    for i in range(len(path) - 1, -1, -1):
        char = path[i]
        if char == ".":
            return path[i + 1 :]
        if char == "/":
            return path
    return remove_path_prefix(path, "Default__")


def remove_path_prefix(path: str, to_remove: str) -> str:
    """``to_remove`` で始まる場合のみプレフィックスを取り除く。"""
    if len(to_remove) > len(path):
        return path
    if not path.startswith(to_remove):
        return path
    return path[len(to_remove) :]


def clean_path_suffix(path: str) -> str:
    """末尾に付いた数字とアンダースコア (``_2`` など) を取り除く。"""
    for i in range(len(path) - 1, -1, -1):
        char = path[i]
        if not char.isdigit() and char != "_":
            return path[: i + 1]
    return path
