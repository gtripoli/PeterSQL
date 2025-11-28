import os
import copy
import locale

import wx
import yaml

from typing import Dict, Optional, List

from gettext import gettext as _, translation

from helpers.logger import logger
from helpers.observables import ObservableObject, Loader

WORKDIR = os.path.abspath(os.path.dirname(__file__))

SETTINGS_CONFIG_FILE = os.path.join(WORKDIR, "settings.yml")


class PeterSQL(wx.App):
    _locale: wx.Locale = wx.Locale()
    settings: ObservableObject

    main_frame: wx.Frame = None

    def OnInit(self) -> bool:

        Loader.loading.subscribe(self._on_loading_change)

        self.settings = ObservableObject(yaml.full_load(open(SETTINGS_CONFIG_FILE)))

        self.settings.subscribe(self.save_settings)

        self._init_locale()

        self.open_session_manager()

        return True

    def _init_locale(self):
        self._locale.Init()
        self._locale.AddCatalogLookupPathPrefix(os.path.join(WORKDIR, "locales"))
        self._locale.AddCatalog("PeterSQL")

    def open_session_manager(self):
        from windows.sessions.controller import SessionManagerController

        self.session_manager = SessionManagerController(None)
        self.session_manager.SetIcon(wx.Icon(os.path.join(WORKDIR, "icons", "petersql.ico")))
        self.session_manager.Show()

    def open_main_frame(self):
        try:
            from windows.main.main_frame import MainFrameController

            self.main_frame = MainFrameController()
            size = wx.Size(*list(map(int, self.settings.get_value("window", "size").split(","))))
            self.main_frame.SetSize(width=size.width, height=size.height)

            position = wx.Point(*list(map(int, self.settings.get_value("window", "position").split(","))))
            self.main_frame.SetPosition(position)
            self.main_frame.Layout()
            self.main_frame.SetIcon(wx.Icon(os.path.join(WORKDIR, "icons", "petersql.ico")))
            self.main_frame.Show()

            self.main_frame.Bind(wx.EVT_SIZE, self._on_size)
            self.main_frame.Bind(wx.EVT_MOVE, self._on_move)
        except Exception as ex:
            logger.error(ex, exc_info=True)

    def _on_size(self, event):
        size = event.GetSize()
        self.settings.set_value("window", "size", value=f"{size.Width},{size.Height}")
        self.main_frame.Layout()

    def _on_move(self, event):
        position = event.GetPosition()
        self.settings.set_value("window", "position", value=f"{position.x},{position.y}")
        self.main_frame.Layout()

    def save_settings(self, settings: Dict):
        settings = copy.copy(settings)

        with open(SETTINGS_CONFIG_FILE, 'w') as outfile:
            yaml.dump(settings, outfile, sort_keys=False)

    def _on_loading_change(self, loading):
        """Handle loading state changes"""
        if loading:
            wx.BeginBusyCursor()
        else:
            wx.EndBusyCursor()

    def do_exit(self, event):
        self.ExitMainLoop()


if __name__ == "__main__":
    app = PeterSQL()
    app.MainLoop()
