from pathlib import Path
import time

import pyautogui
import wx


def pump_ui(iterations: int = 10) -> None:
    for _ in range(iterations):
        wx.YieldIfNeeded()


# def _is_likely_black(bitmap: wx.Bitmap) -> bool:
#     image = bitmap.ConvertToImage()
#     if not image.IsOk():
#         return True
#
#     data = image.GetDataBuffer()
#     if data is None or len(data) == 0:
#         return True
#
#     total = len(data)
#     bright = 0
#     dark = 0
#     bright_threshold = 24
#     dark_threshold = 6
#
#     for idx in range(0, total, 3):
#         r = data[idx]
#         g = data[idx + 1]
#         b = data[idx + 2]
#         if r > bright_threshold or g > bright_threshold or b > bright_threshold:
#             bright += 1
#         if r < dark_threshold and g < dark_threshold and b < dark_threshold:
#             dark += 1
#
#     pixel_count = total // 3
#     if bright == 0:
#         return True
#
#     # Treat as invalid only when the bitmap is almost entirely near-black.
#     # This avoids false negatives on dark themes while still rejecting empty
#     # ScreenDC captures under Xvfb.
#     return dark >= int(pixel_count * 0.995)
#
#
# def _bitmap_quality(bitmap: wx.Bitmap) -> int:
#     image = bitmap.ConvertToImage()
#     if not image.IsOk():
#         return -1
#
#     data = image.GetDataBuffer()
#     if data is None or len(data) == 0:
#         return -1
#
#     bright = 0
#     threshold = 24
#     total = len(data)
#     for idx in range(0, total, 3):
#         if data[idx] > threshold or data[idx + 1] > threshold or data[idx + 2] > threshold:
#             bright += 1
#
#     return bright


def capture_window_bitmap(window: wx.TopLevelWindow) -> wx.Bitmap:
    window.Show()
    window.Raise()
    window.SetFocus()
    window.Layout()
    window.Refresh()
    window.Update()
    pump_ui()

    rect = window.GetScreenRect()

    bitmap = wx.Bitmap(rect.width, rect.height)
    memory_dc = wx.MemoryDC(bitmap)
    screen_dc = wx.ScreenDC()

    try:
        memory_dc.SetBackground(wx.Brush(wx.Colour(0, 0, 0)))
        memory_dc.Clear()
        memory_dc.Blit(
            0,
            0,
            rect.width,
            rect.height,
            screen_dc,
            rect.x,
            rect.y,
        )
    finally:
        memory_dc.SelectObject(wx.NullBitmap)

    return bitmap


def _trim_black_edges(bitmap: wx.Bitmap) -> wx.Bitmap:
    image = bitmap.ConvertToImage()
    if not image.IsOk():
        return bitmap

    width = image.GetWidth()
    height = image.GetHeight()
    if width <= 1 or height <= 1:
        return bitmap

    data = image.GetDataBuffer()
    if data is None or len(data) == 0:
        return bitmap

    threshold = 20

    def _is_dark_pixel(x: int, y: int) -> bool:
        idx = (y * width + x) * 3
        return data[idx] < threshold and data[idx + 1] < threshold and data[idx + 2] < threshold

    def _is_dark_row(y: int) -> bool:
        dark = 0
        for x in range(width):
            if _is_dark_pixel(x, y):
                dark += 1
        return dark >= int(width * 0.98)

    def _is_dark_column(x: int) -> bool:
        dark = 0
        for y in range(height):
            if _is_dark_pixel(x, y):
                dark += 1
        return dark >= int(height * 0.98)

    top = 0
    while top < height - 1 and _is_dark_row(top):
        top += 1

    bottom = height - 1
    while bottom > top and _is_dark_row(bottom):
        bottom -= 1

    left = 0
    while left < width - 1 and _is_dark_column(left):
        left += 1

    right = width - 1
    while right > left and _is_dark_column(right):
        right -= 1

    cropped_width = right - left + 1
    cropped_height = bottom - top + 1
    if cropped_width <= 0 or cropped_height <= 0:
        return bitmap

    if cropped_width == width and cropped_height == height:
        return bitmap

    return bitmap.GetSubBitmap(wx.Rect(left, top, cropped_width, cropped_height))


def capture_window_screenshot(window: wx.TopLevelWindow, target_path: Path) -> None:
    # window.Show()
    # window.Raise()
    # window.Layout()
    # window.Refresh()
    # window.Update()
    # pump_ui(20)
    #
    # target_path.parent.mkdir(parents=True, exist_ok=True)
    # bitmap = capture_window_bitmap(window)
    # bitmap.SaveFile(str(target_path), wx.BITMAP_TYPE_PNG)
    window.Show()
    window.Raise()
    window.SetFocus()
    window.Layout()
    window.Refresh()
    window.Update()

    for _ in range(10):
        wx.GetApp().ProcessPendingEvents()
        wx.YieldIfNeeded()
        time.sleep(0.05)

    rect = window.GetScreenRect()

    image = pyautogui.screenshot(region=(
        rect.x,
        rect.y,
        rect.width,
        rect.height,
    ))

    image.save(target_path)
