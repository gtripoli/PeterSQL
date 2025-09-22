import wx
import os
import enum

ImageList = wx.ImageList(16, 16)


class IconList(object):
    NOT_FOUND = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "cross.png"), wx.BITMAP_TYPE_ANY))

    SYSTEM_FOLDER = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "folder.png"), wx.BITMAP_TYPE_ANY))
    SYSTEM_TABLE = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "table.png"), wx.BITMAP_TYPE_ANY))
    SYSTEM_DATABASE = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "database.png"), wx.BITMAP_TYPE_ANY))
    SYSTEM_CHECKBOX_CHECKED = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "gridcheckbox_checked.png"), wx.BITMAP_TYPE_ANY))
    SYSTEM_CHECKBOX_UNCHECKED = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "gridcheckbox_unchecked.png"), wx.BITMAP_TYPE_ANY))

    ENGINE_SQLITE = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "server-sqlite.png"), wx.BITMAP_TYPE_ANY))
    ENGINE_MYSQL = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "server-mysql.png"), wx.BITMAP_TYPE_ANY))
    ENGINE_MARIADB = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "server-mariadb.png"), wx.BITMAP_TYPE_ANY))
    ENGINE_POSTGRESQL = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "server-postgresql.png"), wx.BITMAP_TYPE_ANY))

    KEY_FULLTEXT = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_fulltext.png"), wx.BITMAP_TYPE_ANY))
    KEY_PRIMARY = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_primary.png"), wx.BITMAP_TYPE_ANY))
    KEY_SPATIAL = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_spatial.png"), wx.BITMAP_TYPE_ANY))
    KEY_UNIQUE = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_unique.png"), wx.BITMAP_TYPE_ANY))
    KEY_NORMAL = ImageList.Add(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_index.png"), wx.BITMAP_TYPE_ANY))
