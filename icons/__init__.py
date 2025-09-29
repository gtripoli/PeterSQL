import wx
import os
import enum

ImageList = wx.ImageList(16, 16)


class BitmapList(object):
    NOT_FOUND = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "cross.png"), wx.BITMAP_TYPE_PNG)

    SYSTEM_FOLDER = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "folder.png"), wx.BITMAP_TYPE_PNG)
    SYSTEM_TABLE = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "table.png"), wx.BITMAP_TYPE_PNG)
    SYSTEM_DATABASE = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "database.png"), wx.BITMAP_TYPE_PNG)
    SYSTEM_CHECKBOX_CHECKED = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "gridcheckbox_checked.png"), wx.BITMAP_TYPE_PNG)
    SYSTEM_CHECKBOX_UNCHECKED = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "gridcheckbox_unchecked.png"), wx.BITMAP_TYPE_PNG)

    ENGINE_SQLITE = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "server-sqlite.png"), wx.BITMAP_TYPE_PNG)
    ENGINE_MYSQL = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "server-mysql.png"), wx.BITMAP_TYPE_PNG)
    ENGINE_MARIADB = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "server-mariadb.png"), wx.BITMAP_TYPE_PNG)
    ENGINE_POSTGRESQL = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "server-postgresql.png"), wx.BITMAP_TYPE_PNG)

    KEY_FULLTEXT = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_fulltext.png"), wx.BITMAP_TYPE_PNG)
    KEY_PRIMARY = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_primary.png"), wx.BITMAP_TYPE_PNG)
    KEY_SPATIAL = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_spatial.png"), wx.BITMAP_TYPE_PNG)
    KEY_UNIQUE = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_unique.png"), wx.BITMAP_TYPE_PNG)
    KEY_NORMAL = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_index.png"), wx.BITMAP_TYPE_PNG)

    ADD = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "add.png"), wx.BITMAP_TYPE_PNG)
    DELETE = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "delete.png"), wx.BITMAP_TYPE_PNG)
    LIGHTNING = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "lightning.png"), wx.BITMAP_TYPE_PNG)
    ARROW_UP = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "arrow_up.png"), wx.BITMAP_TYPE_PNG)
    ARROW_DOWN = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "arrow_down.png"), wx.BITMAP_TYPE_PNG)


class IconList(object):
    NOT_FOUND = ImageList.Add(BitmapList.NOT_FOUND)

    SYSTEM_FOLDER = ImageList.Add(BitmapList.SYSTEM_FOLDER)
    SYSTEM_TABLE = ImageList.Add(BitmapList.SYSTEM_TABLE)
    SYSTEM_DATABASE = ImageList.Add(BitmapList.SYSTEM_DATABASE)
    # SYSTEM_CHECKBOX_CHECKED = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "gridcheckbox_checked.png"), wx.BITMAP_TYPE_PNG))
    # SYSTEM_CHECKBOX_UNCHECKED = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "gridcheckbox_unchecked.png"), wx.BITMAP_TYPE_PNG))

    ENGINE_SQLITE = ImageList.Add(BitmapList.ENGINE_SQLITE)
    ENGINE_MYSQL = ImageList.Add(BitmapList.ENGINE_MYSQL)
    ENGINE_MARIADB = ImageList.Add(BitmapList.ENGINE_MARIADB)
    ENGINE_POSTGRESQL = ImageList.Add(BitmapList.ENGINE_POSTGRESQL)

    KEY_FULLTEXT = ImageList.Add(BitmapList.KEY_FULLTEXT)
    KEY_PRIMARY = ImageList.Add(BitmapList.KEY_PRIMARY)
    KEY_SPATIAL = ImageList.Add(BitmapList.KEY_SPATIAL)
    KEY_UNIQUE = ImageList.Add(BitmapList.KEY_UNIQUE)
    KEY_NORMAL = ImageList.Add(BitmapList.KEY_NORMAL)

    ADD = ImageList.Add(BitmapList.ADD)
    DELETE = ImageList.Add(BitmapList.DELETE)
    LIGHTNING = ImageList.Add(BitmapList.LIGHTNING)
