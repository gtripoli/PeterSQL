
from typing import Optional, Any, Callable
from gettext import gettext as _

import wx
import wx.dataview

from helpers.logger import logger
from helpers.bindings import AbstractModel
from helpers.exceptions import ConnectionException
from helpers.observables import Observable, debounce, Loader, CallbackEvent

from structures.session import Session, SessionEngine, CredentialsConfiguration, SourceConfiguration
from structures.configurations import SSHTunnelConfiguration

from windows import SessionManagerView
from windows.main import CURRENT_SESSION, SESSIONS, BaseDataViewModel
from windows.sessions.repository import SessionManagerRepository

NEW_SESSION: Observable[Session] = Observable()


class SessionManagerModel(AbstractModel):
    def __init__(self):
        self.name = Observable()
        self.engine = Observable(initial=SessionEngine.MYSQL.value.name)
        self.hostname = Observable()
        self.username = Observable()
        self.password = Observable()
        self.port = Observable(initial=3306)
        self.filename = Observable()
        self.comments = Observable()

        self.ssh_tunnel_enabled = Observable(initial=False)
        self.ssh_tunnel_executable = Observable(initial="ssh")
        self.ssh_tunnel_hostname = Observable()
        self.ssh_tunnel_port = Observable(initial=22)
        self.ssh_tunnel_username = Observable()
        self.ssh_tunnel_password = Observable()
        self.ssh_tunnel_local_port = Observable(initial=3307)

        self.engine.subscribe(self._set_default_port)

        debounce(
            self.name, self.engine, self.hostname, self.username, self.password, self.port,
            self.filename, self.comments,
            self.ssh_tunnel_enabled, self.ssh_tunnel_executable, self.ssh_tunnel_hostname,
            self.ssh_tunnel_port, self.ssh_tunnel_username, self.ssh_tunnel_password, self.ssh_tunnel_local_port,
            callback=self._build_session
        )

        CURRENT_SESSION.subscribe(self.clear, CallbackEvent.BEFORE_CHANGE)
        CURRENT_SESSION.subscribe(self.populate)

    def _set_default_port(self, session_engine_name: str):
        session_engine = SessionEngine.from_name(session_engine_name)
        if session_engine == SessionEngine.POSTGRESQL:
            if self.port.get_value() != 5432:
                self.port.set_value(5432)
        elif session_engine in [SessionEngine.MYSQL, SessionEngine.MARIADB]:
            if self.port.get_value() != 3306:
                self.port.set_value(3306)

    def clear(self, *args):
        defaults = {
            self.name: None,
            self.engine: SessionEngine.MYSQL.value.name,
            self.hostname: None, self.username: None, self.password: None, self.port: 3306,
            self.filename: None,
            self.comments: None,
            self.ssh_tunnel_enabled: False, self.ssh_tunnel_executable: "ssh", self.ssh_tunnel_hostname: None,
            self.ssh_tunnel_port: 22, self.ssh_tunnel_username: None, self.ssh_tunnel_password: None,
            self.ssh_tunnel_local_port: 3307,
        }

        for observable, value in defaults.items():
            observable.set_value(value)

    def populate(self, session: Session):
        if not session:
            return

        self.name.set_value(session.name)

        if session.engine is not None:
            self.engine.set_value(session.engine.value.name)

        self.comments.set_value(session.comments)

        if isinstance(session.configuration, CredentialsConfiguration):
            self.hostname.set_value(session.configuration.hostname)
            self.username.set_value(session.configuration.username)
            self.password.set_value(session.configuration.password)
            self.port.set_value(session.configuration.port)

        elif isinstance(session.configuration, SourceConfiguration):
            self.filename.set_value(session.configuration.filename)

        if tunnel := session.ssh_tunnel:
            self.ssh_tunnel_enabled.set_value(tunnel.enabled)
            self.ssh_tunnel_executable.set_value(tunnel.executable)
            self.ssh_tunnel_hostname.set_value(tunnel.hostname)
            self.ssh_tunnel_port.set_value(tunnel.port)
            self.ssh_tunnel_username.set_value(tunnel.username)
            self.ssh_tunnel_password.set_value(tunnel.password)
            self.ssh_tunnel_local_port.set_value(tunnel.local_port)
        else:
            self.ssh_tunnel_enabled.set_value(False)

    def do_create_session(self):
        CURRENT_SESSION.set_value(None)
        NEW_SESSION.set_value(None)

        session = Session(
            id=-1,
            name=self.name.get_value() or _("New Session"),
            engine=SessionEngine.MYSQL,
            configuration=CredentialsConfiguration(
                hostname="localhost",
                username="root",
                password="",
                port=3306
            )
        )

        CURRENT_SESSION.set_value(session)

    def _build_session(self, *args):
        if any([self.name.is_empty, self.engine.is_empty]):
            return

        session_engine = SessionEngine.from_name(self.engine.get_value())

        if (NEW_SESSION.get_value() or CURRENT_SESSION.get_value()) is None:
            self.do_create_session()

        current_session = (NEW_SESSION.get_value() or CURRENT_SESSION.get_value()).copy()

        new_session = NEW_SESSION.get_value() or CURRENT_SESSION.get_value()
        new_session.name = self.name.get_value()
        new_session.engine = session_engine
        new_session.comments = self.comments.get_value()

        if session_engine in [SessionEngine.MYSQL, SessionEngine.MARIADB, SessionEngine.POSTGRESQL]:
            new_session.configuration = CredentialsConfiguration(
                hostname=self.hostname.get_value(),
                username=self.username.get_value(),
                password=self.password.get_value(),
                port=self.port.get_value()
            )

            if ssh_tunnel_enabled := bool(self.ssh_tunnel_enabled.get_value()):
                new_session.ssh_tunnel = SSHTunnelConfiguration(
                    enabled=ssh_tunnel_enabled,
                    executable=self.ssh_tunnel_executable.get_value(),
                    hostname=self.ssh_tunnel_hostname.get_value(),
                    port=self.ssh_tunnel_port.get_value(),
                    username=self.ssh_tunnel_username.get_value(),
                    password=self.ssh_tunnel_password.get_value(),
                    local_port=self.ssh_tunnel_local_port.get_value(),
                )

        elif session_engine == SessionEngine.SQLITE:
            new_session.configuration = SourceConfiguration(
                filename=self.filename.get_value()
            )
            new_session.ssh_tunnel = None

        if not new_session.is_valid:
            return

        elif new_session == current_session:
            return

        NEW_SESSION.set_value(new_session)


class SessionListModel(BaseDataViewModel):
    def __init__(self):
        super().__init__(column_count=2)

    def GetColumnType(self, col):
        if col == 0:
            return wx.dataview.DataViewIconText

        return "string"

    def GetChildren(self, parent, children):
        if not parent:
            for session in self.data:
                children.append(self.ObjectToItem(session))

            return len(self.data)

        return 0

    def IsContainer(self, item):
        if not item:
            return True

        return False

    def GetParent(self, item):
        # if not item:
        return wx.dataview.NullDataViewItem


    def GetValue(self, item, col):
        node = self.ItemToObject(item)

        mapper = {}
        if isinstance(node, Session):
            bitmap = node.engine.value.bitmap
            

            mapper = {0: wx.dataview.DataViewIconText(node.name, bitmap), 1: ""}
        else:
            print(node)

        return mapper[col]


class SessionTreeController():
    on_selection_chance: Callable[[Optional[Any]], Optional[Any]] = None
    on_item_activated: Callable[[Optional[Any]], Optional[Any]] = None

    def __init__(self, session_tree_ctrl: wx.dataview.DataViewCtrl, repository: SessionManagerRepository):
        self.session_tree_ctrl = session_tree_ctrl
        self.repository = repository

        self.model = SessionListModel()
        self.model.set_observable(self.repository.sessions)
        self.session_tree_ctrl.AssociateModel(self.model)

        self.session_tree_ctrl.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)
        self.session_tree_ctrl.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self._on_item_activated)

        # CURRENT_SESSION.subscribe(self._on_current_session_changed, CallbackEvent.AFTER_CHANGE)
        # NEW_SESSION.subscribe(self._on_new_session)

    def _on_selection_changed(self, event):
        item = event.GetItem()
        CURRENT_SESSION.set_value(None)

        if not item.IsOk():
            return

        session = self.model.ItemToObject(item)

        CURRENT_SESSION.set_value(session)

    def _on_item_activated(self, event):
        item = event.GetItem()
        if not item.IsOk():
            return
        session = self.model.ItemToObject(item)

        CURRENT_SESSION.set_value(session)

        if self.on_item_activated:
            self.on_item_activated(session)


class SessionManagerController(SessionManagerView):
    _app = wx.GetApp()
    _repository = SessionManagerRepository()

    def __init__(self, parent):
        super().__init__(parent)
        self.engine.SetItems([e.name for e in SessionEngine.get_all()])

        self.session_tree_controller = SessionTreeController(self.session_tree_ctrl, self._repository)
        self.session_tree_controller.on_item_activated = lambda session: self.on_open(None)

        self.session_manager_model = SessionManagerModel()
        self.session_manager_model.bind_controls(
            name=self.name,
            engine=self.engine,
            hostname=self.hostname, port=self.port,
            username=self.username, password=self.password,
            filename=self.filename,
            comments=self.comments,
            ssh_tunnel_enabled=self.ssh_tunnel_enabled, ssh_tunnel_executable=self.ssh_tunnel_executable,
            ssh_tunnel_hostname=self.ssh_tunnel_hostname, ssh_tunnel_port=self.ssh_tunnel_port,
            ssh_tunnel_username=self.ssh_tunnel_username, ssh_tunnel_password=self.ssh_tunnel_password,
            ssh_tunnel_local_port=self.ssh_tunnel_local_port,
        )

        self._setup_event_handlers()

    def _setup_event_handlers(self):
        self.Bind(wx.EVT_CLOSE, self.on_exit)

        self.session_manager_model.engine.subscribe(self._on_change_engine)

        CURRENT_SESSION.subscribe(self._on_current_session)

        NEW_SESSION.subscribe(self._on_new_session)

    def _on_new_session(self, session: Session):
        item = self.session_tree_controller.model.ObjectToItem(session)
        if item.IsOk():
            self.session_tree_controller.model.ItemChanged(item)

        self.btn_save.Enable(bool(session and session.is_valid))
        self.btn_open.Enable(bool(session and session.is_valid))

    def _on_delete_session(self, event):
        """Handle session deletion"""
        session = self.session_tree_ctrl.get_selected_session()
        if session:
            if wx.MessageBox(_(f"Are you sure you want to delete session '{session.name}'?"),
                             "Confirm Delete", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) == wx.YES:
                self.session_manager.remove_session(session)
                self.session_tree_ctrl.remove_session(session)
        else:
            wx.MessageBox("Please select a session to delete", "Warning", wx.OK | wx.ICON_WARNING)

    def do_open_session(self, event):
        session = CURRENT_SESSION.get_value()
        if not session:
            wx.MessageBox("Please select a session to open", "Warning", wx.OK | wx.ICON_WARNING)
            return

        if not self.GetParent():
            self._app.open_main_frame()

        SESSIONS.append(session)

        self.Hide()

    def _on_current_session(self, session: Optional[Session]):
        self.btn_open.Enable(bool(session and session.is_valid))
        self.btn_delete.Enable(bool(session))

    def _on_session_activated(self, session: Session):
        CURRENT_SESSION.set_value(session)
        # self._app.main_frame.show()
        self.on_open(None)

    def _on_change_engine(self, value: str):
        session_engine = SessionEngine.from_name(value)
        self.panel_credentials.Show(session_engine in [SessionEngine.MYSQL, SessionEngine.MARIADB, SessionEngine.POSTGRESQL])
        self.panel_source.Show(session_engine == SessionEngine.SQLITE)
        self.panel_source.GetParent().Layout()

    def on_save(self, *args):
        session = NEW_SESSION.get_value()
        if not session:
            return False

        dialog = wx.MessageDialog(None,
                                  message=_(f'Do you want save the session {session.name}?'),
                                  caption=_("Confirm save"),
                                  style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION
                                  )

        if dialog.ShowModal() != wx.ID_YES:
            return False

        self._repository.save_session(session)

        NEW_SESSION.set_value(None)
        if session.is_new:
            session = self.session_tree_controller.model.data[-1]

        CURRENT_SESSION.set_value(None).set_value(session)
        self.session_tree_ctrl.Select(self.session_tree_controller.model.ObjectToItem(session))

        return True

    def on_create_session(self, event):
        self.session_manager_model.do_create_session()

    def on_open(self, event):
        if NEW_SESSION.get_value() and not self.on_save(event):
            return

        session = CURRENT_SESSION.get_value()
        if session:
            try:
                self.verify_connection(session)
            except ConnectionException as ex:
                logger.info(ex)
            except Exception as ex:
                logger.error(ex, exc_info=True)
            else:
                self.do_open_session(session)

    def on_delete(self, *args):
        session = CURRENT_SESSION.get_value()
        if not session:
            return
        dialog = wx.MessageDialog(None,
                                  message=_(f'Do you want delete the session {session.name}?'),
                                  caption=_(f"Confirm delete"),
                                  style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION
                                  )
        if dialog.ShowModal() == wx.ID_YES:
            NEW_SESSION.set_value(None)
            CURRENT_SESSION.set_value(None)
            self._repository.delete_session(session)

    def verify_connection(self, session: Session):
        with Loader.cursor_wait():
            try:
                session.context.connect(connect_timeout=10)
            except Exception as ex:
                wx.MessageDialog(None,
                                 message=_(f'Connection error:\n{str(ex)}'),
                                 caption=_("Connection error"),
                                 style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR).ShowModal()
                raise ConnectionException

    def on_exit(self, event):
        if not self._app.main_frame:
            self._app.do_exit(event)
        else:
            self.Hide()

        event.Skip()
