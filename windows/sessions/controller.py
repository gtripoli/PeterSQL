import wx
import wx.dataview

from typing import Optional, List, Dict, Any, Callable, Union
from gettext import gettext as _

from icons import IconList, ImageList

from helpers.logger import logger
from helpers.bindings import AbstractModel
from helpers.exceptions import ConnectionException
from helpers.observables import Observable, debounce, Loader, CallbackEvent

from structures.session import Session, SessionEngine, CredentialsConfiguration, SourceConfiguration

from windows import SessionManagerView
from windows.main import CURRENT_SESSION, SESSIONS
from windows.sessions.repository import SessionManagerRepository

NEW_SESSION: Observable[Session] = Observable()


class SessionManagerModel(AbstractModel):
    def __init__(self):
        self.name = Observable()
        self.engine = Observable(initial=SessionEngine.MYSQL.value)
        self.hostname = Observable()
        self.username = Observable()
        self.password = Observable()
        self.port = Observable(initial=3306)
        self.filename = Observable()
        self.comments = Observable()

        self.ssh_tunnel_use = Observable(initial=False)
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
            self.ssh_tunnel_use, self.ssh_tunnel_executable, self.ssh_tunnel_hostname,
            self.ssh_tunnel_port, self.ssh_tunnel_username, self.ssh_tunnel_password, self.ssh_tunnel_local_port,
            callback=self.build_session
        )

        CURRENT_SESSION.subscribe(self.clear, CallbackEvent.BEFORE_CHANGE)
        CURRENT_SESSION.subscribe(self.populate)

    def _set_default_port(self, engine_value):
        if engine_value == SessionEngine.POSTGRESQL.value:
            if self.port.get_value() != 5432:
                self.port.set_value(5432)
        elif engine_value in [SessionEngine.MYSQL.value, SessionEngine.MARIADB.value]:
            if self.port.get_value() != 3306:
                self.port.set_value(3306)

    def clear(self, *args):
        defaults = {
            self.name: None,
            self.engine: SessionEngine.MYSQL.value,
            self.hostname: None, self.username: None, self.password: None, self.port: 3306,
            self.filename: None,
            self.comments: None,
            self.ssh_tunnel_use: False, self.ssh_tunnel_executable: "ssh", self.ssh_tunnel_hostname: None,
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
            self.engine.set_value(session.engine.value)

        self.comments.set_value(session.comments)

        if isinstance(session.configuration, CredentialsConfiguration):
            self.hostname.set_value(session.configuration.hostname)
            self.username.set_value(session.configuration.username)
            self.password.set_value(session.configuration.password)
            self.port.set_value(session.configuration.port)

        elif isinstance(session.configuration, SourceConfiguration):
            self.filename.set_value(session.configuration.filename)

        if tunnel := session.ssh_tunnel:
            self.ssh_tunnel_use.set_value(tunnel.enabled)
            self.ssh_tunnel_executable.set_value(tunnel.executable)
            self.ssh_tunnel_hostname.set_value(tunnel.hostname)
            self.ssh_tunnel_port.set_value(tunnel.port)
            self.ssh_tunnel_username.set_value(tunnel.username)
            self.ssh_tunnel_password.set_value(tunnel.password)
            self.ssh_tunnel_local_port.set_value(tunnel.local_port)
        else:
            self.ssh_tunnel_use.set_value(False)

    def build_session(self, *args):
        if any([self.name.is_empty, self.engine.is_empty]):
            return

        new_session = None
        session_engine = SessionEngine(self.engine.get_value())
        ssh_tunnel = self._build_ssh_configuration()

        if (current_session := CURRENT_SESSION.get_value()) is None:

            if session_engine in [SessionEngine.MYSQL, SessionEngine.MARIADB, SessionEngine.POSTGRESQL] and not any([
                self.name.is_empty, self.hostname.is_empty, self.username.is_empty, self.password.is_empty
            ]):
                new_session = Session(
                    id=-1,
                    name=self.name.get_value(),
                    engine=session_engine,
                    comments=self.comments.get_value(),
                    configuration=CredentialsConfiguration(
                        hostname=self.hostname.get_value(),
                        username=self.username.get_value(),
                        password=self.password.get_value(),
                        port=self.port.get_value()
                    ),
                    ssh_tunnel=ssh_tunnel,
                )
            elif self.engine.get_value() == SessionEngine.SQLITE.value and not self.filename.is_empty:
                new_session = Session(
                    id=-1,
                    name=self.name.get_value(),
                    engine=session_engine,
                    comments=self.comments.get_value(),
                    configuration=SourceConfiguration(
                        filename=self.filename.get_value()
                    ),
                    ssh_tunnel=None,
                )
        else:
            modified = current_session.copy()
            modified.name = self.name.get_value()
            modified.engine = session_engine
            modified.comments = self.comments.get_value()

            if session_engine in [SessionEngine.MYSQL, SessionEngine.MARIADB, SessionEngine.POSTGRESQL]:
                modified.configuration = CredentialsConfiguration(
                    hostname=self.hostname.get_value(),
                    username=self.username.get_value(),
                    password=self.password.get_value(),
                    port=self.port.get_value()
                )
            elif modified.engine == SessionEngine.SQLITE:
                modified.configuration = SourceConfiguration(
                    filename=self.filename.get_value()
                )

            modified.ssh_tunnel = ssh_tunnel

            if modified.is_valid() and modified == current_session:
                return

            if modified.is_valid() and modified != current_session:
                new_session = modified

        NEW_SESSION.set_value(new_session)


class SessionTreeController():
    on_select: Optional[Callable[[Session], None]] = None
    on_active: Optional[Callable[[Session], None]] = None

    def __init__(self, session_tree_ctrl: wx.dataview.TreeListCtrl):
        self.session_tree_ctrl = session_tree_ctrl
        self.session_tree_ctrl.SetImageList(ImageList)

        self.session_tree_root = self.session_tree_ctrl.GetRootItem()

        self.session_tree_ctrl.Bind(wx.dataview.EVT_TREELIST_SELECTION_CHANGED, self._on_select_session)
        self.session_tree_ctrl.Bind(wx.dataview.EVT_TREELIST_ITEM_ACTIVATED, self._on_active_session)

        CURRENT_SESSION.subscribe(self._on_current_session_changed, CallbackEvent.AFTER_CHANGE)

    def _create_session_folder(self, name: str, sessions: List[Session], parent=None):
        if parent is None:
            parent = self.session_tree_root

        item = self.session_tree_ctrl.AppendItem(parent, icon=wx.dataview.DataViewIconText(name))
        for session in sessions:
            self._create_session_item(session, parent=item)

    def _create_session_item(self, session: Session, parent=None):
        parent = parent or self.session_tree_root

        icon_index = None
        if session.engine == SessionEngine.MYSQL:
            icon_index = IconList.ENGINE_MYSQL
        elif session.engine == SessionEngine.MARIADB:
            icon_index = IconList.ENGINE_MARIADB
        elif session.engine == SessionEngine.SQLITE:
            icon_index = IconList.ENGINE_SQLITE
        elif session.engine == SessionEngine.POSTGRESQL:
            icon_index = IconList.ENGINE_POSTGRESQL

        item = self.session_tree_ctrl.AppendItem(parent, session.name, icon_index)
        self.session_tree_ctrl.SetItemData(item, session)

    def _create_new_session(self, label: str, parent=None):
        parent = parent or self.session_tree_root

        item = self.session_tree_ctrl.AppendItem(parent, label)
        self.session_tree_ctrl.UnselectAll()
        self.session_tree_ctrl.Select(item)
        return item

    def _on_select_session(self, event):
        item = event.GetItem()
        session = self.session_tree_ctrl.GetItemData(item)
        if self.on_select is not None:
            self.on_select(session)

    def _on_active_session(self, event):
        item = event.GetItem()
        session = self.session_tree_ctrl.GetItemData(item)
        if self.on_active is not None:
            self.on_active(session)

    def _on_current_session_changed(self, session: Session):
        if session is None:
            self.session_tree_ctrl.UnselectAll()
            return

    def find_by_data(self, **filters) -> wx.TreeItemId:
        def _matches(data):
            return all(getattr(data, key, None) == value for key, value in filters.items())

        def _search(item):
            if not item.IsOk():
                return None

            data = self.session_tree_ctrl.GetItemData(item)
            if data is not None and _matches(data):
                return item

            child = self.session_tree_ctrl.GetFirstChild(item)
            while child.IsOk():
                found = _search(child)
                if found:
                    return found
                child = self.session_tree_ctrl.GetNextItem(item)

            return None

        return _search(self.session_tree_root)

    def load_sessions(self, sessions: List[Union[Dict[str, List[Session]], Session, str]]):
        self.session_tree_ctrl.DeleteAllItems()

        for session in sessions:
            if isinstance(session, dict):
                if name := str(session.get("name")):
                    self._create_session_folder(name, session.get("sessions", []))
            elif isinstance(session, Session):
                self._create_session_item(session)
            elif isinstance(session, str):
                self._create_new_session(session)


class SessionManagerController(SessionManagerView):
    _app = wx.GetApp()
    _repository = SessionManagerRepository()

    def __init__(self, parent):
        super().__init__(parent)

        self.session_tree_controller = SessionTreeController(self.session_tree_ctrl)
        self.session_tree_controller.load_sessions(self._sessions)

        self.session_manager_model = SessionManagerModel()
        self.session_manager_model.bind_controls(
            name=self.name,
            engine=(self.engine, dict(initial=[engine.value for engine in SessionEngine])),
            hostname=self.hostname,
            port=self.port,
            username=self.username,
            password=self.password,
            filename=self.filename,
            comments=self.comments,
            ssh_tunnel_use=self.ssh_tunnel_use,
            ssh_tunnel_executable=self.ssh_tunnel_executable,
            ssh_tunnel_hostname=self.ssh_tunnel_hostname,
            ssh_tunnel_port=self.ssh_tunnel_port,
            ssh_tunnel_username=self.ssh_tunnel_username,
            ssh_tunnel_password=self.ssh_tunnel_password,
            ssh_tunnel_local_port=self.ssh_tunnel_local_port,
        )
        self.session_manager_model.engine.subscribe(self._on_change_engine)

        self._setup_event_handlers()

    @property
    def _sessions(self):
        raw_sessions = self._repository.load_sessions()
        return self._build_session_tree(raw_sessions)

    def _build_session_tree(self, sessions_data: List[Dict[str, Any]], prefix: Optional[int] = None) -> List[Union[str, Dict[str, Any], Session]]:
        """Build hierarchical session tree from flat data"""
        result: List[Union[str, Dict[str, Any], Session]] = []
        for index, item in enumerate(sessions_data):
            if isinstance(item, str):
                # It's a group name
                result.append(item)
            elif isinstance(item, dict):
                if 'sessions' in item:
                    # It's a group with sessions
                    group = {
                        'name': item['name'],
                        'sessions': self._build_session_tree(item['sessions'], prefix=index)
                    }
                    result.append(group)
                else:
                    # It's a session
                    index_str = f"{prefix}_{index}" if prefix is not None else str(index)
                    session = self._repository.session_from_dict(index_str, item)
                    result.append(session)
        return result

    def _setup_event_handlers(self):
        self.Bind(wx.EVT_CLOSE, self.on_exit)

        self.session_tree_controller.on_select = self._on_session_selected
        self.session_tree_controller.on_active = self._on_session_activated

        NEW_SESSION.subscribe(self._on_new_session)

    def _on_new_session(self, session: Session):
        self.btn_save.Enable(bool(session and session.is_valid()))
        self.btn_open.Enable(bool(session and session.is_valid()))

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

    def _on_session_selected(self, session: Optional[Session]):
        CURRENT_SESSION.set_value(session)

        self.btn_open.Enable(bool(session and session.is_valid()))
        self.btn_delete.Enable(bool(session))

    def _on_session_activated(self, session: Session):
        CURRENT_SESSION.set_value(session)
        # self._app.main_frame.show()
        self.on_open(None)

    def _on_change_engine(self, value):
        self.panel_credentials.Show(value in [SessionEngine.MYSQL.value, SessionEngine.MARIADB.value, SessionEngine.POSTGRESQL.value])
        self.panel_source.Show(value == SessionEngine.SQLITE.value)
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

        if session.id <= -1:
            self._repository.save_session(session)
        # else:
        #     index = self.session_tree_controller.sessions.find(lambda s: isinstance(s, Session) and s._id == session.id)
        #     self.session_tree_controller.sessions.replace(index, session)

        self.session_tree_controller.load_sessions(self._sessions)

        NEW_SESSION.set_value(None)
        CURRENT_SESSION.set_value(session)

        return True

    def on_create(self, event):
        self.session_manager_model.clear()

        CURRENT_SESSION.set_value(None)

        session = Session(
            id=-1,
            name="New Session",
            engine=SessionEngine.MYSQL,
            configuration=CredentialsConfiguration(
                hostname="localhost",
                username="root",
                password="",
                port=3306
            )
        )
        NEW_SESSION.set_value(session)

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
            self.session_tree_controller.load_sessions(self._sessions)

    def verify_connection(self, session: Session):
        with Loader.cursor_wait():
            try:
                if session.has_enabled_tunnel():
                    SSHTunnelRunner(session).ensure()
                session.context.connect(connect_timeout=5)
            except Exception as ex:
                wx.MessageDialog(None,
                                 message=_(u'Connection error:\n{connection_error}?'.format(connection_error=str(ex))),
                                 caption=_("Connection error"),
                                 style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR).ShowModal()
                raise ConnectionException

    def on_exit(self, event):
        if not self._app.main_frame:
            self._app.do_exit(event)
        else:
            self.Hide()

        event.Skip()
