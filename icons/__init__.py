import enum
from typing import Hashable

import wx
import os
import dataclasses
from pathlib import Path

BASE_PATH = os.path.join(os.getcwd(), "icons")


@dataclasses.dataclass(frozen=True)
class Icon:
    id: str
    filename: str

    def load(self, size: int) -> wx.Bitmap:
        path = os.path.join(BASE_PATH, f"{size}x{size}", self.filename)
        bmp = wx.Bitmap(str(path), wx.BITMAP_TYPE_PNG)
        return bmp if bmp.IsOk() else wx.NullBitmap


class IconList:
    # Generic
    NOT_FOUND = Icon("not_found", "cross.png")
    FOLDER = Icon("folder", "folder.png")
    DATABASE = Icon("database", "database.png")

    # DB objects
    TABLE = Icon("table", "table.png")
    VIEW = Icon("view", "view.png")
    TRIGGER = Icon("trigger", "cog.png")
    PROCEDURE = Icon("procedure", "code-folding.png")
    FUNCTION = Icon("function", "lightning.png")
    EVENT = Icon("event", "calendar_view_day.png")

    # Engines
    SQLITE = Icon("engine_sqlite", "server-sqlite.png")
    MYSQL = Icon("engine_mysql", "server-mysql.png")
    MARIADB = Icon("engine_mariadb", "server-mariadb.png")
    POSTGRESQL = Icon("engine_postgresql", "server-postgresql.png")

    # Keys
    KEY_PRIMARY = Icon("key_primary", "key_primary.png")
    KEY_UNIQUE = Icon("key_unique", "key_unique.png")
    KEY_NORMAL = Icon("key_normal", "key_index.png")
    KEY_SPATIAL = Icon("key_spatial", "key_spatial.png")
    KEY_FULLTEXT = Icon("key_fulltext", "key_fulltext.png")
    KEY_FOREIGN = Icon("key_foreign", "table_relationship.png")

    # Actions
    ADD = Icon("add", "add.png")
    DELETE = Icon("delete", "delete.png")
    RUN = Icon("run", "lightning.png")
    CLOCK = Icon("clock", "time.png")


class IconRegistry:
    def __init__(self, size: int = 16):
        self.size = size
        self._imagelist = wx.ImageList(size, size)

        self._idx_cache: dict[Hashable, int] = {}
        self._bmp_cache: dict[Hashable, wx.Bitmap] = {}

    @property
    def imagelist(self) -> wx.ImageList:
        return self._imagelist

    @staticmethod
    def _combine_bitmaps(*bitmaps: wx.Bitmap) -> wx.Bitmap:
        bitmaps = [b for b in bitmaps if b and b.IsOk()]
        if not bitmaps:
            return wx.NullBitmap

        w, h = bitmaps[0].GetWidth(), bitmaps[0].GetHeight()
        for b in bitmaps[1:]:
            if b.GetWidth() != w or b.GetHeight() != h:
                raise ValueError("All bitmaps must have the same size")

        img = wx.Image(w * len(bitmaps), h)
        img.InitAlpha()
        img.SetAlpha(bytes([0x00]) * (w * len(bitmaps) * h))  # transparent bg

        x = 0
        for b in bitmaps:
            img.Paste(b.ConvertToImage(), x, 0)
            x += w

        return img.ConvertToBitmap()

    @staticmethod
    def _key(*icons: "Icon") -> tuple[Hashable, ...]:
        # single -> (id,), combo -> (id1, id2, ...)
        return tuple(icon.id for icon in icons)

    def get_bitmap(self, *icons: "Icon") -> wx.Bitmap:
        if not icons:
            return wx.NullBitmap

        key = self._key(*icons)

        bmp = self._bmp_cache.get(key)
        if bmp and bmp.IsOk():
            return bmp

        if len(icons) == 1:
            # load single
            bmp = icons[0].load(self.size)
            if not bmp or not bmp.IsOk():
                return wx.NullBitmap

            self._bmp_cache[key] = bmp
            return bmp

        # combo: ensure single bitmaps exist (and are cached with (id,))
        parts: list[wx.Bitmap] = []
        for icon in icons:
            part = self.get_bitmap(icon)  # caches (id,)
            if part and part.IsOk():
                parts.append(part)

        if not parts:
            return wx.NullBitmap

        combo = self._combine_bitmaps(*parts) if len(parts) > 1 else parts[0]
        self._bmp_cache[key] = combo
        return combo

    def get_index(self, *icons: "Icon") -> int:
        if not icons:
            return -1

        key = self._key(*icons)

        idx = self._idx_cache.get(key)
        if idx is not None:
            return idx

        bmp = self.get_bitmap(*icons)
        if not bmp or not bmp.IsOk():
            return -1

        idx = self._imagelist.Add(bmp)
        self._idx_cache[key] = idx
        return idx


iconRegistry = IconRegistry(16)
