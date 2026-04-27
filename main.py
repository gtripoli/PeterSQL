import gettext
import locale
import os

from pathlib import Path

import wx

from constants import WORKDIR
from icons import IconRegistry

from helpers.loader import Loader
from helpers.logger import configure_logging, enable_fault_handler, install_global_exception_hooks, logger
from helpers.settings import Settings, SettingsRepository

from windows.components.stc.styles import apply_stc_theme, set_theme_loader
from windows.components.stc.themes import ThemeManager
from windows.components.stc.registry import SyntaxRegistry
from windows.components.stc.profiles import BASE64, CSV, HTML, JSON, MARKDOWN, REGEX, SQL, TEXT, XML, YAML
from windows.components.stc.theme_loader import ThemeLoader


class PeterSQL(wx.App):
    locale: wx.Locale = wx.Locale()

    settings_repository = SettingsRepository(WORKDIR / "settings.yml")
    settings: Settings = settings_repository.load()

    main_frame: wx.Frame = None

    icon_registry_16: IconRegistry

    syntax_registry: SyntaxRegistry
    
    theme_loader: ThemeLoader

    def OnInit(self) -> bool:
        Loader.loading.subscribe(self._on_loading_change)

        self.icon_registry_16 = IconRegistry(WORKDIR / "icons", 16)

        self._init_theme_loader()
        
        self.theme_manager = ThemeManager(apply_function=apply_stc_theme)
        self.syntax_registry = SyntaxRegistry([JSON, SQL, XML, YAML, MARKDOWN, HTML, REGEX, CSV, BASE64, TEXT])

        self._init_locale()

        self.open_session_manager()

        return True

    def OnExceptionInMainLoop(self) -> bool:
        # wx calls this hook implicitly when an exception escapes an event callback in MainLoop.
        logger.exception("Unhandled exception raised inside wx main loop")
        return True
    
    def _init_theme_loader(self) -> None:
        theme_name = self.settings.get_value("ui", "appearance", "theme", default="petersql")
        self.theme_loader = ThemeLoader(WORKDIR / "themes")
        try:
            self.theme_loader.load_theme(theme_name)
            set_theme_loader(self.theme_loader)
        except FileNotFoundError:
            logger.warning(f"Theme '{theme_name}' not found, using default colors")
        except Exception as ex:
            logger.error(f"Error loading theme: {ex}", exc_info=True)

    def _init_locale(self):
        _locale = self.settings.get_value("language", default="en_US")

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
        from windows.dialogs.connections.view import ConnectionsManager

        self.connection_manager = ConnectionsManager(None)
        self.connection_manager.SetIcon(
            wx.Icon(str(WORKDIR / "icons" / "petersql.ico"))
        )
        self.connection_manager.Show()

    def open_main_frame(self) -> None:
        try:
            from windows.main.controller import MainFrameController

            self.main_frame = MainFrameController()
            size_values = self.settings.get_value("ui", "window", "size", default=[1920, 1080])
            size = wx.Size(*list(map(int, size_values)))
            self.main_frame.SetSize(width=size.width, height=size.height)

            position_values = self.settings.get_value("ui", "window", "position", default=[0, 0])
            position = wx.Point(*list(map(int, position_values)))
            self.main_frame.SetPosition(position)
            self.main_frame.Layout()
            self.main_frame.SetIcon(
                wx.Icon(str(WORKDIR / "icons" / "petersql.ico"))
            )
            self.main_frame.Show()

            self.main_frame.Bind(wx.EVT_SIZE, self._on_size)
            self.main_frame.Bind(wx.EVT_MOVE, self._on_move)
        except Exception as ex:
            logger.error(ex, exc_info=True)

    def _on_size(self, event: wx.SizeEvent) -> None:
        size = event.GetSize()
        self.settings.set_value("ui", "window", "size", value=[size.Width, size.Height])
        self.main_frame.Layout()

    def _on_move(self, event: wx.MouseEvent) -> None:
        position = event.GetPosition()
        self.settings.set_value(
            "ui", "window", "position", value=[position.x, position.y]
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
    logs_directory = WORKDIR / "logs"
    configure_logging(logs_directory / "petersql.log")
    enable_fault_handler(logs_directory / "fault.log")
    install_global_exception_hooks()

    app = PeterSQL()
    app.MainLoop()
