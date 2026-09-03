"""NetGUID とエクスポートグループの対応表。

C# 版の ``Unreal.Core.Models.NetGuidCache`` に対応する。
"""

from __future__ import annotations

from typing import Any

from .models import NetFieldExportGroup
from .paths import clean_path_suffix, remove_all_path_prefixes


class NetGuidCache:
    """NetGUID・パス名・エクスポートグループの相互参照を保持する。"""

    def __init__(self) -> None:
        self.net_field_export_group_map: dict[str, NetFieldExportGroup] = {}
        self.net_field_export_group_index_to_group: dict[int, str] = {}
        self.net_guid_to_path_name: dict[int, str] = {}
        self.net_field_export_group_map_path_fixed: dict[int, NetFieldExportGroup] = {}
        self.external_data: dict[int, Any] = {}

        self._network_gameplay_tag_node_index: NetFieldExportGroup | None = None
        self._arch_type_to_export_group: dict[int, NetFieldExportGroup] = {}
        self._cleaned_paths: dict[int, str] = {}
        self._cleaned_class_net_cache: dict[str, str] = {}
        self._failed_paths: set[str] = set()

    # -- GameplayTag --------------------------------------------------------

    @property
    def network_gameplay_tag_node_index(self) -> NetFieldExportGroup | None:
        """GameplayTag のインデックス表。"""
        if self._network_gameplay_tag_node_index is None:
            group = self.net_field_export_group_map.get("NetworkGameplayTagNodeIndex")
            if group is None:
                group = self.net_field_export_group_map.get("NetworkGameplayTagDynamicIndex")
            self._network_gameplay_tag_node_index = group
        return self._network_gameplay_tag_node_index

    def try_get_tag_name(self, tag_index: int) -> str | None:
        """GameplayTag のインデックスから名前を得る。"""
        node_index = self.network_gameplay_tag_node_index
        if node_index is not None and node_index.is_valid_index(tag_index):
            export = node_index.net_field_exports[tag_index]
            if export is not None:
                return export.name
        return None

    # -- エクスポートグループ ------------------------------------------------

    def add_to_export_group_map(self, group: str, export_group: NetFieldExportGroup) -> None:
        """エクスポートグループを登録する。"""
        if group.endswith("ClassNetCache"):
            export_group.path_name = remove_all_path_prefixes(export_group.path_name)
        self.net_field_export_group_map[group] = export_group
        self.net_field_export_group_index_to_group[export_group.path_name_index] = group

    def get_net_field_export_group_from_index(self, index: int | None) -> NetFieldExportGroup | None:
        """パス名インデックスからエクスポートグループを得る。"""
        if index is None:
            return None
        group = self.net_field_export_group_index_to_group.get(index)
        if group is None:
            return None
        return self.net_field_export_group_map.get(group)

    def get_net_field_export_group_by_path(self, path: str | None) -> NetFieldExportGroup | None:
        """パス名からエクスポートグループを得る。"""
        if not path:
            return None
        return self.net_field_export_group_map.get(path)

    def get_net_field_export_group(self, netguid: int | None) -> NetFieldExportGroup | None:
        """NetGUID (アーキタイプ) からエクスポートグループを推定する。"""
        if netguid is None:
            return None

        group = self._arch_type_to_export_group.get(netguid)
        if group is not None:
            return group

        path = self.net_guid_to_path_name.get(netguid)
        if path is None:
            return None

        # 一度失敗したパスは再探索しない
        if path in self._failed_paths:
            return None

        group = self.net_field_export_group_map_path_fixed.get(netguid)
        if group is not None:
            self._arch_type_to_export_group[netguid] = group
            return group

        for group_path, export_group in self.net_field_export_group_map.items():
            group_path_fixed = self._cleaned_paths.get(export_group.path_name_index)
            if group_path_fixed is None:
                group_path_fixed = remove_all_path_prefixes(group_path)
                self._cleaned_paths[export_group.path_name_index] = group_path_fixed
            if group_path_fixed in path:
                self.net_field_export_group_map_path_fixed[netguid] = export_group
                self._arch_type_to_export_group[netguid] = export_group
                return export_group

        cleaned_path = clean_path_suffix(path)
        for group_path, export_group in self.net_field_export_group_map.items():
            group_path_fixed = self._cleaned_paths.get(export_group.path_name_index)
            if group_path_fixed is not None and cleaned_path in group_path_fixed:
                self.net_field_export_group_map_path_fixed[netguid] = export_group
                self._arch_type_to_export_group[netguid] = export_group
                return export_group

        self._failed_paths.add(path)
        return None

    def try_get_class_net_cache(
        self, group: str | None, use_full_name: bool
    ) -> NetFieldExportGroup | None:
        """クラスの ClassNetCache グループを取得する。"""
        if not group:
            return None
        class_net_cache_path = self._cleaned_class_net_cache.get(group)
        if class_net_cache_path is None:
            class_net_cache_path = (
                f"{group}_ClassNetCache"
                if use_full_name
                else f"{remove_all_path_prefixes(group)}_ClassNetCache"
            )
            self._cleaned_class_net_cache[group] = class_net_cache_path
        return self.net_field_export_group_map.get(class_net_cache_path)

    # -- その他 -------------------------------------------------------------

    def try_get_path_name(self, netguid: int) -> str | None:
        """NetGUID からパス名を得る。"""
        return self.net_guid_to_path_name.get(netguid)

    def try_get_external_data(self, netguid: int | None) -> Any | None:
        """外部データを取り出す (取り出したデータは削除される)。"""
        if netguid is None:
            return None
        return self.external_data.pop(netguid, None)

    def cleanup(self) -> None:
        """すべてのキャッシュを破棄する。"""
        self.net_field_export_group_index_to_group.clear()
        self.net_field_export_group_map.clear()
        self.net_guid_to_path_name.clear()
        self.net_field_export_group_map_path_fixed.clear()
        self.external_data.clear()
        self._network_gameplay_tag_node_index = None
        self._arch_type_to_export_group.clear()
        self._cleaned_paths.clear()
        self._cleaned_class_net_cache.clear()
        self._failed_paths.clear()
