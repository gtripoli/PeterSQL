import locale
import os
import copy
import threading
import traceback

import wx
import yaml

from typing import Dict, Optional, List

from gettext import gettext as _, translation

from helpers.logger import logger
from helpers.observables import ObservableObject

from models.session import Session

from windows.main import CursorWait

WORKDIR = os.path.abspath(os.path.dirname(__file__))

SETTINGS_CONFIG_FILE = os.path.join(WORKDIR, "settings.yml")


class PeterSQL(wx.App):
    _locale: wx.Locale = wx.Locale()
    settings: ObservableObject

    main_frame: wx.Frame = None

    def OnInit(self) -> bool:

        self.cursor_wait = CursorWait()

        self.settings = ObservableObject(yaml.full_load(open(SETTINGS_CONFIG_FILE)))

        self.settings.subscribe(self.save_settings)

        self._init_locale()

        self.open_session_manager()

        return True

    def _init_locale(self):
        self._locale.Init()
        self._locale.AddCatalogLookupPathPrefix(os.path.join(WORKDIR, "locales"))
        self._locale.AddCatalog("PeterSQL")

    def verify_connection(self, session: Session):
        with self.cursor_wait():
            try:
                session.statement.connect()
            except Exception as ex:
                logger.warning(ex)
                wx.MessageDialog(None, message=_(u'Connection error:\n{connection_error}?'.format(connection_error=str(ex))), style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR).ShowModal()
                raise

    def open_session_manager(self):
        from windows.session_manager import SessionManagerController

        sm = SessionManagerController(None, sessions=self.settings.get_value("sessions"))
        sm.Show()

    def open_main_frame(self):
        try:
            from windows.main.main_frame import MainFrameController

            self.main_frame = MainFrameController()
            self.main_frame.Show()
        except Exception as ex:
            logger.error(ex, exc_info=True)

    def _dump_sessions(self, sessions: Optional[List] = None):
        sessions_dump = []
        for session in sessions:
            if type(session) is dict:
                sessions_dump.append(dict(
                    name=session["name"],
                    sessions=self._dump_sessions(sessions=session.get("sessions"))
                ))

            elif type(session) is Session:
                sessions_dump.append(session.to_dict())

        return sessions_dump

    def save_settings(self, settings: Dict):
        settings = copy.copy(settings)
        settings["sessions"] = self._dump_sessions(settings.get("sessions"))

        with open(SETTINGS_CONFIG_FILE, 'w') as outfile:
            yaml.dump(settings, outfile, sort_keys=False)

    def do_exit(self, event):
        self.ExitMainLoop()


if __name__ == "__main__":
    app = PeterSQL()
    app.MainLoop()
