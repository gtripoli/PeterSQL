import wx
import os
import enum

ImageList = wx.ImageList(16, 16)


class BitmapList:
    NOT_FOUND = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "cross.png"), wx.BITMAP_TYPE_PNG)

    SYSTEM_FOLDER = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "folder.png"), wx.BITMAP_TYPE_PNG)
    SYSTEM_TABLE = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "table.png"), wx.BITMAP_TYPE_PNG)
    SYSTEM_DATABASE = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "database.png"), wx.BITMAP_TYPE_PNG)
    SYSTEM_VIEW = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "view.png"), wx.BITMAP_TYPE_PNG)
    SYSTEM_TRIGGER = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "cog.png"), wx.BITMAP_TYPE_PNG)
    SYSTEM_PROCEDURE = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "code-folding.png"), wx.BITMAP_TYPE_PNG)
    SYSTEM_FUNCTION = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "lightning.png"), wx.BITMAP_TYPE_PNG)
    SYSTEM_EVENT = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "calendar_view_day.png"), wx.BITMAP_TYPE_PNG)

    ENGINE_SQLITE = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "server-sqlite.png"), wx.BITMAP_TYPE_PNG)
    ENGINE_MYSQL = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "server-mysql.png"), wx.BITMAP_TYPE_PNG)
    ENGINE_MARIADB = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "server-mariadb.png"), wx.BITMAP_TYPE_PNG)
    ENGINE_POSTGRESQL = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "server-postgresql.png"), wx.BITMAP_TYPE_PNG)

    KEY_PRIMARY = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_primary.png"), wx.BITMAP_TYPE_PNG)
    KEY_UNIQUE = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_unique.png"), wx.BITMAP_TYPE_PNG)
    KEY_NORMAL = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_index.png"), wx.BITMAP_TYPE_PNG)
    KEY_SPATIAL = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_spatial.png"), wx.BITMAP_TYPE_PNG)
    KEY_FULLTEXT = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_fulltext.png"), wx.BITMAP_TYPE_PNG)

    KEY_FOREIGN = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "table_relationship.png"), wx.BITMAP_TYPE_PNG)

    ADD = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "add.png"), wx.BITMAP_TYPE_PNG)
    DELETE = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "delete.png"), wx.BITMAP_TYPE_PNG)
    LIGHTNING = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "lightning.png"), wx.BITMAP_TYPE_PNG)
    ARROW_UP = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "arrow_up.png"), wx.BITMAP_TYPE_PNG)
    ARROW_DOWN = wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "arrow_down.png"), wx.BITMAP_TYPE_PNG)


class IconList(object):
    NOT_FOUND = ImageList.Add(BitmapList.NOT_FOUND)

    SYSTEM_FOLDER = ImageList.Add(BitmapList.SYSTEM_FOLDER)
    SYSTEM_TABLE = ImageList.Add(BitmapList.SYSTEM_TABLE)
    SYSTEM_VIEW = ImageList.Add(BitmapList.SYSTEM_VIEW)
    SYSTEM_TRIGGER = ImageList.Add(BitmapList.SYSTEM_TRIGGER)
    SYSTEM_DATABASE = ImageList.Add(BitmapList.SYSTEM_DATABASE)

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


def combine_bitmaps(*bitmaps: wx.Bitmap) -> wx.Bitmap:
    if not bitmaps:
        return wx.NullBitmap

    width = bitmaps[0].GetWidth()
    height = bitmaps[0].GetHeight()

    # Create a new image with combined width and alpha channel
    combined_width = width * len(bitmaps)
    combined_image = wx.Image(combined_width, height)
    combined_image.InitAlpha()  # Enable alpha channel

    # Set all pixels to transparent initially
    combined_image.SetAlpha(b'\xff' * (combined_width * height))  # Fully transparent

    x_offset = 0
    for bitmap in bitmaps:
        icon_image = bitmap.ConvertToImage()
        # Paste the icon onto the combined image at x_offset
        combined_image.Paste(icon_image, x_offset, 0)
        x_offset += width

    # Convert back to bitmap
    combined_bitmap = combined_image.ConvertToBitmap()
    return combined_bitmap
