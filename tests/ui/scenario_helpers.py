from pathlib import Path

import wx


def pump_ui(iterations: int = 10) -> None:
    for _ in range(iterations):
        wx.YieldIfNeeded()


def capture_window_screenshot(window: wx.TopLevelWindow, target_path: Path) -> None:
    size = window.GetSize()
    width, height = int(size.width), int(size.height)
    bitmap = wx.Bitmap(width, height)
    memory_dc = wx.MemoryDC(bitmap)
    try:
        memory_dc.Blit(0, 0, width, height, wx.ClientDC(window), 0, 0)
    finally:
        memory_dc.SelectObject(wx.NullBitmap)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    bitmap.SaveFile(str(target_path), wx.BITMAP_TYPE_PNG)
