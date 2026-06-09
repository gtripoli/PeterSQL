import os
import time

from collections import defaultdict
from gettext import gettext as _
from typing import Callable

import wx
import wx.dataview


class QueryHistoryController:
    def __init__(self, tree_ctrl: wx.dataview.DataViewTreeCtrl, on_open_query: Callable[[str], None]):
        self.tree_ctrl = tree_ctrl
        self.on_open_query = on_open_query

        self.tree_ctrl.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self._on_item_activated)
        self.tree_ctrl.Bind(wx.dataview.EVT_DATAVIEW_ITEM_START_EDITING, self._on_item_start_editing)

    def _open_history_item(self, item: wx.dataview.DataViewItem) -> None:
        if not item.IsOk():
            return

        file_path = self.tree_ctrl.GetItemData(item)
        if not isinstance(file_path, str):
            return

        if not os.path.isfile(file_path):
            return

        self.on_open_query(file_path)

    def _on_item_activated(self, event: wx.dataview.DataViewEvent) -> None:
        item = event.GetItem()
        if item.IsOk():
            self._open_history_item(item)

    @staticmethod
    def _on_item_start_editing(event: wx.dataview.DataViewEvent) -> None:
        event.Veto()

    @staticmethod
    def get_query_history_directory() -> str:
        query_dir = os.path.join(os.getcwd(), ".queries")
        os.makedirs(query_dir, exist_ok=True)
        return query_dir

    @staticmethod
    def _build_query_preview(content: str) -> str:
        for line in content.splitlines():
            query_line = line.strip()
            if query_line:
                return query_line[:120]

        return _("(empty query)")

    @staticmethod
    def _group_query_paths_by_date(query_paths: list[str]) -> dict[str, list[str]]:
        grouped_paths: dict[str, list[str]] = defaultdict(list)
        for file_path in query_paths:
            modified_date = time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(file_path)))
            grouped_paths[modified_date].append(file_path)

        return grouped_paths

    def _list_query_paths(self) -> list[str]:
        query_dir = self.get_query_history_directory()
        query_paths = []

        for filename in os.listdir(query_dir):
            if not filename.endswith(".sql"):
                continue

            file_path = os.path.join(query_dir, filename)
            if os.path.isfile(file_path):
                query_paths.append(file_path)

        return query_paths

    def refresh(self) -> None:
        self.tree_ctrl.DeleteAllItems()

        grouped_paths = self._group_query_paths_by_date(self._list_query_paths())
        root_item = wx.dataview.NullDataViewItem
        sorted_dates = sorted(grouped_paths.keys(), reverse=True)

        for date_index, modified_date in enumerate(sorted_dates):
            date_item = self.tree_ctrl.AppendContainer(root_item, modified_date)
            sorted_paths = sorted(grouped_paths[modified_date], key=os.path.getmtime, reverse=True)

            for file_path in sorted_paths:
                try:
                    with open(file_path, "r", encoding="utf-8") as file_obj:
                        preview = self._build_query_preview(file_obj.read())
                except Exception:
                    preview = os.path.basename(file_path)

                self.tree_ctrl.AppendItem(date_item, preview, data=file_path)

            if date_index == 0:
                self.tree_ctrl.Expand(date_item)
            else:
                self.tree_ctrl.Collapse(date_item)