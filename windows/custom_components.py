import wx


class CustomPopupTransientWindow(wx.PopupTransientWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(parent=kwargs.get("parent"))
