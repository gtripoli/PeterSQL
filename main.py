import locale
import os
from pathlib import Path

import wx
import gettext

import settings

from icons import IconRegistry

from helpers.logger import logger
from helpers.loader import Loader
from helpers.observables import ObservableObject

WORKDIR = Path(os.path.abspath(os.path.dirname(__file__)))


class PeterSQL(wx.App):
    locale: wx.Locale = wx.Locale()

    settings: ObservableObject = settings.load(WORKDIR.joinpath("settings.yml"))

    main_frame: wx.Frame = None

    icon_registry_16: IconRegistry

    def OnInit(self) -> bool:
        from windows.components.stc.themes import ThemeManager
        from windows.components.stc.styles import apply_stc_theme

        Loader.loading.subscribe(self._on_loading_change)

        self.icon_registry_16 = IconRegistry(os.path.join(WORKDIR, "icons"), 16)

        self.theme_manager = ThemeManager(apply_fn=apply_stc_theme)

        self._init_locale()

        self.open_session_manager()

        return True

    def _init_locale(self):
        _locale = self.settings.get_value("locale")

        if _locale is None:
            _locale, encoding = locale.getdefaultlocale()

        translation = gettext.translation(
            'petersql',
            localedir=WORKDIR.joinpath("locale"),
            languages=[_locale],
            fallback=True
        )
        translation.install(['gettext', 'ngettext', 'npgettext', 'pgettext'])

        def gettext_wrapper(message):
            return translation.gettext(message)

        gettext.gettext = gettext_wrapper

        self.locale.Init()
        self.locale.AddCatalogLookupPathPrefix(str(WORKDIR.joinpath("locale")))
        self.locale.AddCatalog("petersql")
        locale.setlocale(locale.LC_ALL, _locale)

    def open_session_manager(self) -> None:
        from windows.connections.manager import ConnectionsManager

        self.connection_manager = ConnectionsManager(None)
        self.connection_manager.SetIcon(
            wx.Icon(os.path.join(WORKDIR, "icons", "petersql.ico"))
        )
        self.connection_manager.Show()

    def open_main_frame(self) -> None:
        try:
            from windows.main.main_frame import MainFrameController

            self.main_frame = MainFrameController()
            size = wx.Size(
                *list(map(int, self.settings.get_value("window", "size").split(",")))
            )
            self.main_frame.SetSize(width=size.width, height=size.height)

            position = wx.Point(
                *list(
                    map(int, self.settings.get_value("window", "position").split(","))
                )
            )
            self.main_frame.SetPosition(position)
            self.main_frame.Layout()
            self.main_frame.SetIcon(
                wx.Icon(os.path.join(WORKDIR, "icons", "petersql.ico"))
            )
            self.main_frame.Show()

            self.main_frame.Bind(wx.EVT_SIZE, self._on_size)
            self.main_frame.Bind(wx.EVT_MOVE, self._on_move)
        except Exception as ex:
            logger.error(ex, exc_info=True)

    def _on_size(self, event: wx.SizeEvent) -> None:
        size = event.GetSize()
        self.settings.set_value("window", "size", value=f"{size.Width},{size.Height}")
        self.main_frame.Layout()

    def _on_move(self, event: wx.MouseEvent) -> None:
        position = event.GetPosition()
        self.settings.set_value(
            "window", "position", value=f"{position.x},{position.y}"
        )
        self.main_frame.Layout()

    def _on_loading_change(self, loading: bool) -> None:
        """Handle loading state changes"""
        if loading:
            wx.BeginBusyCursor()
        else:
            wx.EndBusyCursor()

    def do_exit(self, event: wx.Event) -> None:
        self.ExitMainLoop()


if __name__ == "__main__":
    app = PeterSQL()
    app.MainLoop()
